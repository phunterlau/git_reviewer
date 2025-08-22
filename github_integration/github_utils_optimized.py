import os
import re
from github import Github
from datetime import datetime


def get_commits_optimized(github_email, repo_url):
    """
    Fetch commits by a specific user using GitHub Search API (much faster for large repos).
    
    Args:
        github_email (str): The email address of the GitHub user
        repo_url (str): The GitHub repository URL
    
    Returns:
        str: Path to the generated markdown file, or None if failed
    """
    try:
        # Initialize GitHub client
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
        
        g = Github(github_token)
        
        # Extract owner/repo from URL
        repo_name = extract_repo_name(repo_url)
        if not repo_name:
            raise ValueError(f"Invalid repository URL: {repo_url}")
        
        print(f"Searching for commits by {github_email} in {repo_name} using GitHub Search API...")
        
        # Use GitHub Search API to find commits by author email in specific repo
        # This is much more efficient than scanning all commits
        search_query = f"author-email:{github_email} repo:{repo_name}"
        
        print(f"Search query: {search_query}")
        search_result = g.search_commits(search_query)
        
        # Convert search results to list and get basic info
        user_commits = []
        total_count = search_result.totalCount
        
        print(f"Found {total_count} commits by {github_email}")
        
        if total_count == 0:
            print(f"No commits found for email {github_email} in repository {repo_name}")
            return None
        
        # Limit the number of commits we process for performance
        max_commits = min(total_count, 50)  # Process max 50 commits
        print(f"Processing {max_commits} commits...")
        
        count = 0
        for commit in search_result:
            if count >= max_commits:
                break
                
            user_commits.append(commit)
            count += 1
            
            if count % 10 == 0:
                print(f"Processed {count}/{max_commits} commits...")
        
        # Generate markdown content
        markdown_content = generate_markdown_optimized(user_commits, github_email, repo_name, total_count)
        
        # Save to file
        filename = f"commits_{github_email.replace('@', '_at_').replace('.', '_')}.md"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Commits saved to {filepath}")
        return filepath
        
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            print(f"GitHub API rate limit exceeded: {error_msg}")
            print("Please wait a while before trying again, or use a different GitHub token.")
        elif "not found" in error_msg.lower() or "404" in error_msg:
            print(f"Repository not found or not accessible: {error_msg}")
            print("Please check the repository URL and make sure it's public or you have access.")
        elif "timeout" in error_msg.lower():
            print(f"Request timed out: {error_msg}")
            print("The repository might be too large. Try again or use a smaller repository.")
        elif "validation failed" in error_msg.lower():
            print(f"Search query validation failed: {error_msg}")
            print("This might happen if the email format is invalid or the repository doesn't exist.")
        else:
            print(f"Error fetching commits: {error_msg}")
        return None


def get_commits(github_email, repo_url):
    """
    Main function that tries optimized search first, falls back to original method.
    """
    # Try optimized search first
    result = get_commits_optimized(github_email, repo_url)
    if result:
        return result
    
    # Fallback to original method if search fails
    print("Falling back to original commit scanning method...")
    return get_commits_original(github_email, repo_url)


def get_commits_original(github_email, repo_url):
    """
    Original implementation - scans all commits (fallback method).
    """
    try:
        # Initialize GitHub client
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
        
        g = Github(github_token)
        
        # Extract owner/repo from URL
        repo_name = extract_repo_name(repo_url)
        if not repo_name:
            raise ValueError(f"Invalid repository URL: {repo_url}")
        
        print(f"Fetching commits from {repo_name} for user {github_email}...")
        
        # Get repository
        repo = g.get_repo(repo_name)
        
        # Get commits with pagination and limits for large repositories
        print("Scanning repository commits (this may take a moment for large repos)...")
        commits = repo.get_commits()
        user_commits = []
        processed_count = 0
        max_commits_to_scan = 2000  # Limit to prevent timeout on huge repos
        
        try:
            for commit in commits:
                processed_count += 1
                
                # Progress indicator for large repos
                if processed_count % 100 == 0:
                    print(f"Scanned {processed_count} commits, found {len(user_commits)} by {github_email}")
                
                # Check if commit author email matches
                if (commit.commit.author and 
                    commit.commit.author.email and 
                    commit.commit.author.email.lower() == github_email.lower()):
                    user_commits.append(commit)
                    
                    # Limit number of user commits to process (for very active contributors)
                    if len(user_commits) >= 50:
                        print(f"Found 50+ commits by {github_email}, limiting to first 50 for analysis")
                        break
                
                # Stop scanning if we've looked at too many commits
                if processed_count >= max_commits_to_scan:
                    print(f"Reached scan limit ({max_commits_to_scan} commits). Consider using a more recent repository or smaller timeframe.")
                    break
                    
        except Exception as e:
            print(f"Warning: Error during commit scanning: {str(e)}")
            if len(user_commits) == 0:
                raise
            print(f"Continuing with {len(user_commits)} commits found so far...")
        
        if not user_commits:
            print(f"No commits found for email {github_email} in repository {repo_name}")
            print(f"Scanned {processed_count} commits total.")
            return None
        
        print(f"Found {len(user_commits)} commits by {github_email} (scanned {processed_count} total commits)")
        
        # Generate markdown content
        markdown_content = generate_markdown(user_commits, github_email, repo_name)
        
        # Save to file
        filename = f"commits_{github_email.replace('@', '_at_').replace('.', '_')}.md"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Commits saved to {filepath}")
        return filepath
        
    except ValueError as e:
        print(f"Configuration error: {str(e)}")
        return None
    except Exception as e:
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            print(f"GitHub API rate limit exceeded: {error_msg}")
            print("Please wait a while before trying again, or use a different GitHub token.")
        elif "not found" in error_msg.lower() or "404" in error_msg:
            print(f"Repository not found or not accessible: {error_msg}")
            print("Please check the repository URL and make sure it's public or you have access.")
        elif "timeout" in error_msg.lower():
            print(f"Request timed out: {error_msg}")
            print("The repository might be too large. Try again or use a smaller repository.")
        else:
            print(f"Error fetching commits: {error_msg}")
        return None


def extract_repo_name(repo_url):
    """
    Extract owner/repo from various GitHub URL formats.
    
    Args:
        repo_url (str): GitHub repository URL
    
    Returns:
        str: Repository name in format "owner/repo" or None if invalid
    """
    # Remove trailing slash if present
    repo_url = repo_url.rstrip('/')
    
    # Remove .git suffix if present
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    
    # Pattern to match GitHub repository URLs
    patterns = [
        r'https://github\.com/([^/]+/[^/]+)',
        r'git@github\.com:([^/]+/[^/]+)',
        r'^([^/]+/[^/]+)$'  # Direct owner/repo format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, repo_url)
        if match:
            return match.group(1)
    
    return None


def generate_markdown_optimized(commits, github_email, repo_name, total_count):
    """
    Generate markdown content from commits (optimized version).
    
    Args:
        commits: List of GitHub commit objects from search
        github_email (str): Email of the user
        repo_name (str): Repository name
        total_count (int): Total number of commits found
    
    Returns:
        str: Markdown content
    """
    content = f"# Commits by {github_email} in {repo_name}\n\n"
    content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Total commits found: {total_count}\n"
    content += f"Commits processed: {len(commits)}\n"
    content += f"Search method: GitHub Search API (optimized)\n\n"
    content += "---\n\n"
    
    for i, commit in enumerate(commits, 1):
        content += f"## Commit {i}: {commit.sha[:8]}\n\n"
        content += f"**SHA:** {commit.sha}\n"
        content += f"**Date:** {commit.commit.author.date}\n"
        content += f"**Author:** {commit.commit.author.name} <{commit.commit.author.email}>\n"
        content += f"**Message:**\n```\n{commit.commit.message}\n```\n\n"
        
        # Get commit files/changes (limit to avoid performance issues)
        try:
            files = commit.files
            if files:
                content += "**Files Changed:**\n"
                # Limit number of files shown to avoid huge output
                files_to_show = files[:5]  # Show max 5 files per commit for performance
                for file in files_to_show:
                    content += f"- `{file.filename}` ({file.status})\n"
                    if hasattr(file, 'additions') and file.additions > 0:
                        content += f"  - Additions: {file.additions}\n"
                    if hasattr(file, 'deletions') and file.deletions > 0:
                        content += f"  - Deletions: {file.deletions}\n"
                
                if len(files) > 5:
                    content += f"  - ... and {len(files) - 5} more files\n"
                content += "\n"
                
                # Add patch/diff for small changes only (very limited for performance)
                content += "**Sample Changes:**\n"
                patches_added = 0
                for file in files_to_show:
                    if patches_added >= 2:  # Limit to 2 patches max
                        break
                    if hasattr(file, 'patch') and file.patch and len(file.patch) < 1000:  # Smaller limit
                        content += f"\n### {file.filename}\n"
                        content += f"```diff\n{file.patch[:500]}{'...' if len(file.patch) > 500 else ''}\n```\n"
                        patches_added += 1
                
                if len(files) > patches_added:
                    remaining = len(files) - patches_added
                    content += f"\n*... and {remaining} more files (showing sample only)*\n"
        
        except Exception as e:
            content += f"**Error getting file details:** {str(e)}\n"
        
        content += "\n---\n\n"
    
    if total_count > len(commits):
        content += f"\n**Note:** Showing {len(commits)} of {total_count} total commits. "
        content += "Large commit histories are limited for performance.\n"
    
    return content


def generate_markdown(commits, github_email, repo_name):
    """
    Generate markdown content from commits (original version).
    """
    content = f"# Commits by {github_email} in {repo_name}\n\n"
    content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"Total commits: {len(commits)}\n"
    content += f"Search method: Repository scan (fallback)\n\n"
    content += "---\n\n"
    
    for i, commit in enumerate(commits, 1):
        content += f"## Commit {i}: {commit.sha[:8]}\n\n"
        content += f"**SHA:** {commit.sha}\n"
        content += f"**Date:** {commit.commit.author.date}\n"
        content += f"**Author:** {commit.commit.author.name} <{commit.commit.author.email}>\n"
        content += f"**Message:**\n```\n{commit.commit.message}\n```\n\n"
        
        # Get commit files/changes
        try:
            files = commit.files
            if files:
                content += "**Files Changed:**\n"
                # Limit number of files shown to avoid huge output
                files_to_show = files[:10]  # Show max 10 files per commit
                for file in files_to_show:
                    content += f"- `{file.filename}` ({file.status})\n"
                    if file.additions > 0:
                        content += f"  - Additions: {file.additions}\n"
                    if file.deletions > 0:
                        content += f"  - Deletions: {file.deletions}\n"
                
                if len(files) > 10:
                    content += f"  - ... and {len(files) - 10} more files\n"
                content += "\n"
                
                # Add patch/diff for small changes only
                content += "**Changes:**\n"
                patches_added = 0
                for file in files_to_show:
                    if patches_added >= 3:  # Limit patches to avoid huge output
                        break
                    if file.patch and len(file.patch) < 1500:  # Smaller patch size limit
                        content += f"\n### {file.filename}\n"
                        content += f"```diff\n{file.patch}\n```\n"
                        patches_added += 1
                
                if len(files) > 3 or patches_added < len(files_to_show):
                    remaining = len(files) - patches_added
                    if remaining > 0:
                        content += f"\n*... and {remaining} more files (patches too large or limit reached)*\n"
        
        except Exception as e:
            content += f"**Error getting file details:** {str(e)}\n"
        
        content += "\n---\n\n"
    
    return content
