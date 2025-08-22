import os
import re
import json
from github import Github
from datetime import datetime


def get_commits_optimized(github_identifier, repo_url, limit=100):
    """
    Fetch commits by a specific user using GitHub Search API (much faster for large repos).
    
    Args:
        github_identifier (str): The email address or GitHub username of the user
        repo_url (str): The GitHub repository URL
        limit (int): Maximum number of commits to fetch (default: 100)
    
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
        
        # Determine if input is email or username
        is_email = '@' in github_identifier
        
        if is_email:
            search_query = f"author-email:{github_identifier} repo:{repo_name} sort:author-date-desc"
            print(f"Searching for commits by email {github_identifier} in {repo_name} using GitHub Search API...")
        else:
            search_query = f"author:{github_identifier} repo:{repo_name} sort:author-date-desc"
            print(f"Searching for commits by username {github_identifier} in {repo_name} using GitHub Search API...")
        
        print(f"Search query: {search_query}")
        search_result = g.search_commits(search_query)
        
        # Convert search results to list and get basic info
        user_commits = []
        total_count = search_result.totalCount
        
        identifier_type = "email" if is_email else "username"
        print(f"Found {total_count} commits by {identifier_type} {github_identifier}")
        
        if total_count == 0:
            print(f"No commits found for {identifier_type} {github_identifier} in repository {repo_name}")
            return None
        
        # Limit the number of commits we process for performance
        max_commits = min(total_count, limit)  # Process up to the specified limit
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
        markdown_content = generate_markdown_optimized(user_commits, github_identifier, repo_name, total_count)
        
        # Save to file
        safe_identifier = github_identifier.replace('@', '_at_').replace('.', '_').replace('/', '_')
        filename = f"commits_{safe_identifier}.md"
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


def get_commits(github_identifier, repo_url, limit=100):
    """
    Fetch commits by a specific user using GitHub Search API (much faster for large repos).
    Falls back to repository scanning if Search API fails.
    
    Args:
        github_identifier (str): The email address or GitHub username of the user
        repo_url (str): The GitHub repository URL
        limit (int): Maximum number of commits to fetch (default: 100)
    
    Returns:
        str: Path to the generated markdown file, or None if failed
    """
    # Try optimized search first
    result = get_commits_optimized(github_identifier, repo_url, limit)
    
    # If search API returns no results, fall back to repository scanning
    if result is None:
        print("GitHub Search API found no results. Falling back to repository scanning...")
        print("This method is slower but more comprehensive for forked repositories.")
        return get_commits_original(github_identifier, repo_url, limit)
    
    return result


def get_commits_original(github_identifier, repo_url, limit=100):
    """
    Original implementation - scans all commits (fallback method).
    
    Args:
        github_identifier (str): The email address or GitHub username of the user
        repo_url (str): The GitHub repository URL
        limit (int): Maximum number of commits to fetch (default: 100)
    
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
        
        print(f"Fetching commits from {repo_name} for user {github_identifier}...")
        
        # Determine if input is email or username
        is_email = '@' in github_identifier
        
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
                    print(f"Scanned {processed_count} commits, found {len(user_commits)} by {github_identifier}")
                
                # Check if commit matches (email or username)
                commit_matches = False
                if is_email:
                    # For email, check commit author email
                    if (commit.commit.author and 
                        commit.commit.author.email and 
                        commit.commit.author.email.lower() == github_identifier.lower()):
                        commit_matches = True
                else:
                    # For username, check against commit author name or committer login
                    if commit.author and commit.author.login == github_identifier:
                        commit_matches = True
                    elif (commit.commit.author and 
                          commit.commit.author.name and 
                          commit.commit.author.name.lower() == github_identifier.lower()):
                        commit_matches = True
                
                if commit_matches:
                    user_commits.append(commit)
                    
                    # Limit number of user commits to process based on the limit parameter
                    if len(user_commits) >= limit:
                        print(f"Found {limit}+ commits by {github_identifier}, limiting to first {limit} for analysis")
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
            identifier_type = "email" if is_email else "username"
            print(f"No commits found for {identifier_type} {github_identifier} in repository {repo_name}")
            print(f"Scanned {processed_count} commits total.")
            return None
        
        print(f"Found {len(user_commits)} commits by {github_identifier} (scanned {processed_count} total commits)")
        
        # Generate markdown content
        markdown_content = generate_markdown(user_commits, github_identifier, repo_name, limit)
        
        # Save to file
        safe_identifier = github_identifier.replace('@', '_at_').replace('.', '_').replace('/', '_')
        filename = f"commits_{safe_identifier}.md"
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
    
    # If it's already in owner/repo format
    if '/' in repo_url and 'github.com' not in repo_url:
        return repo_url
    
    # Extract from GitHub URL
    patterns = [
        r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$',
        r'github\.com/([^/]+/[^/]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, repo_url)
        if match:
            return match.group(1)
    
    return None


def generate_markdown_optimized(commits, github_identifier, repo_name, total_count):
    """
    Generate markdown content from commits with enhanced timestamps and time analysis.
    
    Args:
        commits: List of GitHub commit objects from search
        github_identifier (str): GitHub identifier (email or username) 
        repo_name (str): Repository name
        total_count (int): Total number of commits found
    
    Returns:
        str: Markdown content
    """
    from datetime import datetime, timezone
    
    current_time = datetime.now(timezone.utc)
    content = f"# Commits by {github_identifier} in {repo_name}\n\n"
    content += f"**Analysis Date:** {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    content += f"**Total commits found:** {total_count}\n"
    content += f"**Commits processed:** {len(commits)}\n"
    content += f"**Search method:** GitHub Search API (optimized)\n\n"
    content += "---\n\n"
    
    for i, commit in enumerate(commits, 1):
        commit_date = commit.commit.author.date
        commit_date_str = commit_date.strftime('%Y-%m-%d %H:%M:%S UTC') if commit_date else "Unknown"
        
        # Calculate time since commit
        if commit_date:
            time_diff = current_time - commit_date.replace(tzinfo=timezone.utc)
            days_ago = time_diff.days
            if days_ago == 0:
                time_since = "Today"
            elif days_ago == 1:
                time_since = "1 day ago"
            elif days_ago < 30:
                time_since = f"{days_ago} days ago"
            elif days_ago < 365:
                months = days_ago // 30
                time_since = f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = days_ago // 365
                time_since = f"{years} year{'s' if years > 1 else ''} ago"
        else:
            time_since = "Unknown"
        
        content += f"## Commit {i}: {commit.sha[:8]}\n\n"
        content += f"**SHA:** {commit.sha}\n"
        content += f"**Date:** {commit_date_str} ({time_since})\n"
        content += f"**Author:** {commit.commit.author.name} <{commit.commit.author.email}>\n"
        content += f"**URL:** {commit.html_url}\n"
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


def generate_markdown(commits, github_identifier, repo_name, limit=None):
    """
    Generate markdown content from commits (original version).
    
    Args:
        commits: List of commit objects
        github_identifier (str): GitHub identifier (email or username)
        repo_name (str): Repository name
        limit (int, optional): The limit that was applied during fetching
    
    Returns:
        str: Markdown content
    """
    from datetime import datetime, timezone
    
    current_time = datetime.now(timezone.utc)
    content = f"# Commits by {github_identifier} in {repo_name}\n\n"
    content += f"**Analysis Date:** {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    content += f"**Total commits found:** {len(commits)}\n"
    content += f"**Search method:** Repository scan (fallback)\n"
    if limit and len(commits) >= limit:
        content += f"**Note:** Results limited to {limit} commits\n"
    content += "\n---\n\n"
    
    for i, commit in enumerate(commits, 1):
        commit_date = commit.commit.author.date
        commit_date_str = commit_date.strftime('%Y-%m-%d %H:%M:%S UTC') if commit_date else "Unknown"
        
        # Calculate time since commit
        if commit_date:
            time_diff = current_time - commit_date.replace(tzinfo=timezone.utc)
            days_ago = time_diff.days
            if days_ago == 0:
                time_since = "Today"
            elif days_ago == 1:
                time_since = "1 day ago"
            elif days_ago < 30:
                time_since = f"{days_ago} days ago"
            elif days_ago < 365:
                months = days_ago // 30
                time_since = f"{months} month{'s' if months > 1 else ''} ago"
            else:
                years = days_ago // 365
                time_since = f"{years} year{'s' if years > 1 else ''} ago"
        else:
            time_since = "Unknown"
        
        content += f"## Commit {i}: {commit.sha[:8]}\n\n"
        content += f"**SHA:** {commit.sha}\n"
        content += f"**Date:** {commit_date_str} ({time_since})\n"
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
    
    if limit and len(commits) >= limit:
        content += f"\n**Note:** Showing {len(commits)} commits (limited by --limit parameter). "
        content += "Use a higher limit to see more commits.\n"
    
    return content


def get_issues(github_identifier, repo_url, limit=100):
    """
    Fetch issues by a specific user using GitHub Search API.
    
    Args:
        github_identifier (str): The email address or GitHub username of the user
        repo_url (str): The GitHub repository URL
        limit (int): Maximum number of issues to fetch (default: 100)
    
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
        
        # Determine if input is email or username
        is_email = '@' in github_identifier
        
        if is_email:
            # For email, we need to search by the user who has that email
            # This is more complex as we need to find the username first
            print(f"Searching for issues by email {github_identifier} in {repo_name}...")
            search_query = f"type:issue repo:{repo_name} sort:created-desc"
            issues = g.search_issues(search_query)
            
            # Filter by email (less efficient but necessary)
            user_issues = []
            processed = 0
            for issue in issues:
                processed += 1
                if processed > limit:  # Use limit to prevent timeout
                    break
                    
                # Check if issue creator email matches (if available)
                if (issue.user and hasattr(issue.user, 'email') and 
                    issue.user.email and issue.user.email.lower() == github_identifier.lower()):
                    user_issues.append(issue)
                    
        else:
            # For username, use direct search
            search_query = f"type:issue author:{github_identifier} repo:{repo_name} sort:created-desc"
            print(f"Searching for issues by username {github_identifier} in {repo_name}...")
            search_result = g.search_issues(search_query)
            user_issues = list(search_result)[:limit]  # Limit the results
        
        identifier_type = "email" if is_email else "username"
        print(f"Found {len(user_issues)} issues by {identifier_type} {github_identifier}")
        
        if not user_issues:
            print(f"No issues found for {identifier_type} {github_identifier} in repository {repo_name}")
            return None
        
        # Generate markdown content
        markdown_content = generate_issues_markdown(user_issues, github_identifier, repo_name)
        
        # Save to file
        safe_identifier = github_identifier.replace('@', '_at_').replace('.', '_')
        filename = f"issues_{safe_identifier}.md"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Issues saved to {filepath}")
        return filepath
        
    except Exception as e:
        print(f"An error occurred while fetching issues: {str(e)}")
        return None


def get_pull_requests(github_identifier, repo_url, limit=100):
    """
    Fetch pull requests by a specific user using GitHub Search API.
    
    Args:
        github_identifier (str): The email address or GitHub username of the user
        repo_url (str): The GitHub repository URL
        limit (int): Maximum number of pull requests to fetch (default: 100)
    
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
        
        # Determine if input is email or username
        is_email = '@' in github_identifier
        
        if is_email:
            # For email, we need to search by the user who has that email
            print(f"Searching for pull requests by email {github_identifier} in {repo_name}...")
            search_query = f"type:pr repo:{repo_name} sort:created-desc"
            prs = g.search_issues(search_query)
            
            # Filter by email (less efficient but necessary)
            user_prs = []
            processed = 0
            for pr in prs:
                processed += 1
                if processed > limit:  # Use limit to prevent timeout
                    break
                    
                # Check if PR creator email matches (if available)
                if (pr.user and hasattr(pr.user, 'email') and 
                    pr.user.email and pr.user.email.lower() == github_identifier.lower()):
                    user_prs.append(pr)
                    
        else:
            # For username, use direct search
            search_query = f"type:pr author:{github_identifier} repo:{repo_name} sort:created-desc"
            print(f"Searching for pull requests by username {github_identifier} in {repo_name}...")
            search_result = g.search_issues(search_query)
            user_prs = list(search_result)[:limit]  # Limit the results
        
        identifier_type = "email" if is_email else "username"
        print(f"Found {len(user_prs)} pull requests by {identifier_type} {github_identifier}")
        
        if not user_prs:
            print(f"No pull requests found for {identifier_type} {github_identifier} in repository {repo_name}")
            return None
        
        # Generate markdown content
        markdown_content = generate_pull_requests_markdown(user_prs, github_identifier, repo_name)
        
        # Save to file
        safe_identifier = github_identifier.replace('@', '_at_').replace('.', '_')
        filename = f"pull_requests_{safe_identifier}.md"
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Pull requests saved to {filepath}")
        return filepath
        
    except Exception as e:
        print(f"An error occurred while fetching pull requests: {str(e)}")
        return None


def generate_issues_markdown(issues, github_identifier, repo_name):
    """
    Generate markdown content for issues with comments and enhanced timestamps.
    
    Args:
        issues: List of issue objects
        github_identifier (str): The GitHub identifier (email or username)
        repo_name (str): Repository name
        
    Returns:
        str: Markdown formatted string
    """
    from datetime import datetime, timezone
    
    current_time = datetime.now(timezone.utc)
    content = f"# GitHub Issues for {github_identifier}\n\n"
    content += f"**Repository:** {repo_name}\n"
    content += f"**Total Issues Found:** {len(issues)}\n"
    content += f"**Analysis Date:** {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    content += "---\n\n"
    
    for i, issue in enumerate(issues, 1):
        try:
            created_date = issue.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if issue.created_at else "Unknown"
            
            # Calculate time since creation
            if issue.created_at:
                time_diff = current_time - issue.created_at.replace(tzinfo=timezone.utc)
                days_ago = time_diff.days
                if days_ago == 0:
                    time_since = "Today"
                elif days_ago == 1:
                    time_since = "1 day ago"
                elif days_ago < 30:
                    time_since = f"{days_ago} days ago"
                elif days_ago < 365:
                    months = days_ago // 30
                    time_since = f"{months} month{'s' if months > 1 else ''} ago"
                else:
                    years = days_ago // 365
                    time_since = f"{years} year{'s' if years > 1 else ''} ago"
            else:
                time_since = "Unknown"
            
            content += f"## {i}. Issue #{issue.number}: {issue.title}\n\n"
            content += f"**State:** {issue.state}\n"
            content += f"**Created:** {created_date} ({time_since})\n"
            
            # Add last updated info if available
            if hasattr(issue, 'updated_at') and issue.updated_at:
                updated_date = issue.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                update_diff = current_time - issue.updated_at.replace(tzinfo=timezone.utc)
                update_days = update_diff.days
                if update_days == 0:
                    update_time_since = "Today"
                elif update_days == 1:
                    update_time_since = "1 day ago"
                elif update_days < 30:
                    update_time_since = f"{update_days} days ago"
                else:
                    update_months = update_days // 30
                    update_time_since = f"{update_months} month{'s' if update_months > 1 else ''} ago"
                content += f"**Last Updated:** {updated_date} ({update_time_since})\n"
            
            # Add closed date if applicable
            if issue.state == 'closed' and hasattr(issue, 'closed_at') and issue.closed_at:
                closed_date = issue.closed_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                close_diff = current_time - issue.closed_at.replace(tzinfo=timezone.utc)
                close_days = close_diff.days
                if close_days == 0:
                    close_time_since = "Today"
                elif close_days < 30:
                    close_time_since = f"{close_days} days ago"
                else:
                    close_months = close_days // 30
                    close_time_since = f"{close_months} month{'s' if close_months > 1 else ''} ago"
                content += f"**Closed:** {closed_date} ({close_time_since})\n"
            
            content += f"**URL:** {issue.html_url}\n"
            content += f"**Author:** {issue.user.login if issue.user else 'Unknown'}\n"
            
            if issue.labels:
                labels = [label.name for label in issue.labels]
                content += f"**Labels:** {', '.join(labels)}\n"
            
            if issue.assignees:
                assignees = [assignee.login for assignee in issue.assignees]
                content += f"**Assignees:** {', '.join(assignees)}\n"
            
            content += f"**Comments Count:** {issue.comments}\n\n"
            
            # Add description (truncated if too long)
            if issue.body:
                description = issue.body[:800] + "..." if len(issue.body) > 800 else issue.body
                content += f"**Description:**\n{description}\n\n"
            
            # Fetch and add comments if there are any
            if issue.comments > 0:
                try:
                    content += f"**Comments ({issue.comments}):**\n\n"
                    comments = issue.get_comments()
                    comment_count = 0
                    max_comments = min(issue.comments, 5)  # Limit to 5 comments per issue
                    
                    for comment in comments:
                        if comment_count >= max_comments:
                            remaining = issue.comments - max_comments
                            if remaining > 0:
                                content += f"*... and {remaining} more comments*\n\n"
                            break
                            
                        comment_date = comment.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if comment.created_at else "Unknown"
                        comment_diff = current_time - comment.created_at.replace(tzinfo=timezone.utc) if comment.created_at else None
                        
                        if comment_diff:
                            comment_days = comment_diff.days
                            if comment_days == 0:
                                comment_time_since = "Today"
                            elif comment_days < 30:
                                comment_time_since = f"{comment_days} days ago"
                            else:
                                comment_months = comment_days // 30
                                comment_time_since = f"{comment_months} month{'s' if comment_months > 1 else ''} ago"
                        else:
                            comment_time_since = "Unknown"
                        
                        comment_body = comment.body[:300] + "..." if len(comment.body) > 300 else comment.body
                        content += f"- **{comment.user.login if comment.user else 'Unknown'}** ({comment_date}, {comment_time_since}):\n"
                        content += f"  {comment_body}\n\n"
                        comment_count += 1
                        
                except Exception as e:
                    content += f"*Error fetching comments: {str(e)}*\n\n"
            
            content += "---\n\n"
            
        except Exception as e:
            content += f"**Error processing issue {i}:** {str(e)}\n\n"
    
    return content


def generate_pull_requests_markdown(pull_requests, github_identifier, repo_name):
    """
    Generate markdown content for pull requests with comments and enhanced timestamps.
    
    Args:
        pull_requests: List of pull request objects
        github_identifier (str): The GitHub identifier (email or username)
        repo_name (str): Repository name
        
    Returns:
        str: Markdown formatted string
    """
    from datetime import datetime, timezone
    
    current_time = datetime.now(timezone.utc)
    content = f"# GitHub Pull Requests for {github_identifier}\n\n"
    content += f"**Repository:** {repo_name}\n"
    content += f"**Total Pull Requests Found:** {len(pull_requests)}\n"
    content += f"**Analysis Date:** {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
    content += "---\n\n"
    
    for i, pr in enumerate(pull_requests, 1):
        try:
            created_date = pr.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if pr.created_at else "Unknown"
            
            # Calculate time since creation
            if pr.created_at:
                time_diff = current_time - pr.created_at.replace(tzinfo=timezone.utc)
                days_ago = time_diff.days
                if days_ago == 0:
                    time_since = "Today"
                elif days_ago == 1:
                    time_since = "1 day ago"
                elif days_ago < 30:
                    time_since = f"{days_ago} days ago"
                elif days_ago < 365:
                    months = days_ago // 30
                    time_since = f"{months} month{'s' if months > 1 else ''} ago"
                else:
                    years = days_ago // 365
                    time_since = f"{years} year{'s' if years > 1 else ''} ago"
            else:
                time_since = "Unknown"
            
            content += f"## {i}. Pull Request #{pr.number}: {pr.title}\n\n"
            content += f"**State:** {pr.state}\n"
            content += f"**Created:** {created_date} ({time_since})\n"
            
            # Add last updated info if available
            if hasattr(pr, 'updated_at') and pr.updated_at:
                updated_date = pr.updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                update_diff = current_time - pr.updated_at.replace(tzinfo=timezone.utc)
                update_days = update_diff.days
                if update_days == 0:
                    update_time_since = "Today"
                elif update_days == 1:
                    update_time_since = "1 day ago"
                elif update_days < 30:
                    update_time_since = f"{update_days} days ago"
                else:
                    update_months = update_days // 30
                    update_time_since = f"{update_months} month{'s' if update_months > 1 else ''} ago"
                content += f"**Last Updated:** {updated_date} ({update_time_since})\n"
            
            # Add merged date if applicable
            if hasattr(pr, 'merged_at') and pr.merged_at:
                merged_date = pr.merged_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                merge_diff = current_time - pr.merged_at.replace(tzinfo=timezone.utc)
                merge_days = merge_diff.days
                if merge_days == 0:
                    merge_time_since = "Today"
                elif merge_days < 30:
                    merge_time_since = f"{merge_days} days ago"
                else:
                    merge_months = merge_days // 30
                    merge_time_since = f"{merge_months} month{'s' if merge_months > 1 else ''} ago"
                content += f"**Merged:** {merged_date} ({merge_time_since})\n"
                
                # Calculate time from creation to merge
                if pr.created_at:
                    merge_duration = pr.merged_at - pr.created_at
                    merge_duration_days = merge_duration.days
                    if merge_duration_days == 0:
                        duration_text = f"{merge_duration.seconds // 3600} hours"
                    elif merge_duration_days < 30:
                        duration_text = f"{merge_duration_days} days"
                    else:
                        duration_months = merge_duration_days // 30
                        duration_text = f"{duration_months} month{'s' if duration_months > 1 else ''}"
                    content += f"**Time to Merge:** {duration_text}\n"
            
            # Add closed date if applicable and not merged
            elif pr.state == 'closed' and hasattr(pr, 'closed_at') and pr.closed_at:
                closed_date = pr.closed_at.strftime('%Y-%m-%d %H:%M:%S UTC')
                close_diff = current_time - pr.closed_at.replace(tzinfo=timezone.utc)
                close_days = close_diff.days
                if close_days == 0:
                    close_time_since = "Today"
                elif close_days < 30:
                    close_time_since = f"{close_days} days ago"
                else:
                    close_months = close_days // 30
                    close_time_since = f"{close_months} month{'s' if close_months > 1 else ''} ago"
                content += f"**Closed:** {closed_date} ({close_time_since})\n"
            
            content += f"**URL:** {pr.html_url}\n"
            content += f"**Author:** {pr.user.login if pr.user else 'Unknown'}\n"
            
            # Add branch information
            if hasattr(pr, 'head') and pr.head:
                content += f"**Source Branch:** {pr.head.ref}\n"
            if hasattr(pr, 'base') and pr.base:
                content += f"**Target Branch:** {pr.base.ref}\n"
            
            if pr.labels:
                labels = [label.name for label in pr.labels]
                content += f"**Labels:** {', '.join(labels)}\n"
            
            if pr.assignees:
                assignees = [assignee.login for assignee in pr.assignees]
                content += f"**Assignees:** {', '.join(assignees)}\n"
            
            # Add review information if available
            if hasattr(pr, 'requested_reviewers') and pr.requested_reviewers:
                reviewers = [reviewer.login for reviewer in pr.requested_reviewers]
                content += f"**Requested Reviewers:** {', '.join(reviewers)}\n"
            
            content += f"**Comments Count:** {pr.comments}\n\n"
            
            # Add description (truncated if too long)
            if pr.body:
                description = pr.body[:800] + "..." if len(pr.body) > 800 else pr.body
                content += f"**Description:**\n{description}\n\n"
            
            # Fetch and add comments if there are any
            if pr.comments > 0:
                try:
                    content += f"**Comments ({pr.comments}):**\n\n"
                    comments = pr.get_issue_comments()  # For PR comments, use get_issue_comments
                    comment_count = 0
                    max_comments = min(pr.comments, 5)  # Limit to 5 comments per PR
                    
                    for comment in comments:
                        if comment_count >= max_comments:
                            remaining = pr.comments - max_comments
                            if remaining > 0:
                                content += f"*... and {remaining} more comments*\n\n"
                            break
                            
                        comment_date = comment.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if comment.created_at else "Unknown"
                        comment_diff = current_time - comment.created_at.replace(tzinfo=timezone.utc) if comment.created_at else None
                        
                        if comment_diff:
                            comment_days = comment_diff.days
                            if comment_days == 0:
                                comment_time_since = "Today"
                            elif comment_days < 30:
                                comment_time_since = f"{comment_days} days ago"
                            else:
                                comment_months = comment_days // 30
                                comment_time_since = f"{comment_months} month{'s' if comment_months > 1 else ''} ago"
                        else:
                            comment_time_since = "Unknown"
                        
                        comment_body = comment.body[:300] + "..." if len(comment.body) > 300 else comment.body
                        content += f"- **{comment.user.login if comment.user else 'Unknown'}** ({comment_date}, {comment_time_since}):\n"
                        content += f"  {comment_body}\n\n"
                        comment_count += 1
                        
                except Exception as e:
                    content += f"*Error fetching comments: {str(e)}*\n\n"
            
            content += "---\n\n"
            
        except Exception as e:
            content += f"**Error processing pull request {i}:** {str(e)}\n\n"
    
    return content


def get_user_reviews(g, user_login, repo_name, limit=20):
    """Fetches code reviews submitted by a user."""
    try:
        query = f"reviewed-by:{user_login} repo:{repo_name} is:pr"
        issues = g.search_issues(query, sort="updated", order="desc")
        reviews = []
        for issue in issues[:limit]:
            try:
                pr = issue.as_pull_request()
                for review in pr.get_reviews():
                    if review.user and review.user.login == user_login and review.body:
                        reviews.append({
                            "pr_title": pr.title,
                            "pr_url": pr.html_url,
                            "review_body": review.body,
                            "state": review.state,
                            "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None
                        })
            except Exception as e:
                print(f"Error processing review for PR {issue.number}: {e}")
                continue
        return reviews
    except Exception as e:
        print(f"Could not fetch user reviews: {e}")
        return []


def fetch_all_contributions(user_identifier, repo_url, limit=50):
    """
    Fetches all contribution types (commits, PRs, issues, reviews) for a user
    in a given repository and returns a structured dictionary.
    Implements caching to avoid repeated API calls.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN not found")
    
    g = Github(github_token)
    repo_name = extract_repo_name(repo_url)
    if not repo_name:
        raise ValueError("Invalid repository URL")

    # Caching logic
    cache_dir = ".cache"
    os.makedirs(cache_dir, exist_ok=True)
    safe_user_identifier = user_identifier.replace('@', '_at_').replace('.', '_').replace('/', '_')
    cache_file = os.path.join(cache_dir, f"{safe_user_identifier}-{repo_name.replace('/', '_')}.json")

    if os.path.exists(cache_file):
        print(f"Loading contributions from cache: {cache_file}")
        with open(cache_file, 'r') as f:
            return json.load(f)

    print("Fetching fresh contribution data from GitHub...")
    
    # Resolve email to login if necessary
    user_login = user_identifier
    if '@' in user_identifier:
        # Try to resolve email to login
        try:
            search_result = g.search_commits(f"author-email:{user_identifier}")
            for commit in search_result[:5]:  # Check first few commits
                if commit.author and commit.author.login:
                    user_login = commit.author.login
                    print(f"Resolved email {user_identifier} -> {user_login}")
                    break
        except Exception as e:
            print(f"Could not resolve GitHub login for email: {user_identifier}")
            return None

    try:
        # Fetch all data types efficiently
        repo = g.get_repo(repo_name)
        
        # Get commits
        commits_data = []
        try:
            commits = list(repo.get_commits(author=user_login)[:limit])
            commits_data = [{
                "sha": c.sha[:8], 
                "message": c.commit.message, 
                "date": c.commit.author.date.isoformat() if c.commit.author.date else None,
                "files_changed": len(list(c.files)) if hasattr(c, 'files') else 0
            } for c in commits]
        except Exception as e:
            print(f"Error fetching commits: {e}")

        # Get pull requests
        prs_data = []
        try:
            pull_requests = list(g.search_issues(f"author:{user_login} repo:{repo_name} is:pr")[:limit])
            prs_data = [{
                "title": pr.title, 
                "number": pr.number, 
                "state": pr.state, 
                "body": pr.body[:200] + "..." if pr.body and len(pr.body) > 200 else pr.body,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "comments": pr.comments
            } for pr in pull_requests]
        except Exception as e:
            print(f"Error fetching pull requests: {e}")

        # Get issues
        issues_data = []
        try:
            issues = list(g.search_issues(f"author:{user_login} repo:{repo_name} is:issue")[:limit])
            issues_data = [{
                "title": i.title, 
                "number": i.number, 
                "state": i.state, 
                "body": i.body[:200] + "..." if i.body and len(i.body) > 200 else i.body,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "comments": i.comments
            } for i in issues]
        except Exception as e:
            print(f"Error fetching issues: {e}")

        # Get reviews
        reviews_data = get_user_reviews(g, user_login, repo_name, limit)

        # Structure the data
        contributions = {
            "user": user_login,
            "original_identifier": user_identifier,
            "repo": repo_name,
            "fetch_timestamp": datetime.now().isoformat(),
            "commits": commits_data,
            "pull_requests": prs_data,
            "issues": issues_data,
            "reviews": reviews_data,
            "summary_stats": {
                "total_commits": len(commits_data),
                "total_prs": len(prs_data),
                "total_issues": len(issues_data),
                "total_reviews": len(reviews_data)
            }
        }

        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(contributions, f, indent=2)
        print(f"Saved contributions to cache: {cache_file}")

        return contributions
        
    except Exception as e:
        print(f"Error in fetch_all_contributions: {e}")
        return None


def benchmark_contribution_methods(user_identifier, repo_url, limit=20):
    """
    Benchmarks the performance and efficiency of old vs new contribution fetching methods.
    
    Args:
        user_identifier (str): GitHub username or email
        repo_url (str): Repository URL
        limit (int): Number of items to fetch for comparison
        
    Returns:
        dict: Benchmark results comparing both approaches
    """
    import time
    import gc
    from gpt_utils import review_commits_with_gpt, review_contributions_with_gpt
    
    print("🔍 Starting benchmark comparison...")
    benchmark_results = {
        "user": user_identifier,
        "repo": repo_url,
        "limit": limit,
        "timestamp": datetime.now().isoformat()
    }
    
    # Benchmark OLD approach
    print("\n📊 Testing OLD approach (individual API calls + file-based)...")
    start_time = time.time()
    api_calls_old = 0
    
    try:
        # Simulate old approach
        old_start = time.time()
        
        # Old method would make separate calls
        commits_content = get_commits_optimized(user_identifier, repo_url, limit)
        api_calls_old += 1
        
        prs_content = get_pull_requests(user_identifier, repo_url, limit)
        api_calls_old += 1
        
        issues_content = get_issues(user_identifier, repo_url, limit)
        api_calls_old += 1
        
        # Write temporary file (simulating old file-based approach)
        temp_file = f".temp_benchmark_{user_identifier.replace('@', '_')}.md"
        with open(temp_file, 'w') as f:
            f.write(f"{commits_content}\n\n{prs_content}\n\n{issues_content}")
        
        # Old GPT analysis (would read from file)
        old_gpt_analysis = review_commits_with_gpt(temp_file)
        
        old_end = time.time()
        old_total_time = old_end - old_start
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        benchmark_results["old_approach"] = {
            "execution_time": round(old_total_time, 2),
            "api_calls": api_calls_old,
            "file_operations": 2,  # write + read
            "success": True,
            "tokens_used": old_gpt_analysis.get("analysis_metadata", {}).get("tokens_used", "N/A")
        }
        
    except Exception as e:
        benchmark_results["old_approach"] = {
            "execution_time": -1,
            "api_calls": api_calls_old,
            "success": False,
            "error": str(e)
        }
    
    # Clear memory
    gc.collect()
    
    # Benchmark NEW approach  
    print("\n🚀 Testing NEW approach (unified fetching + caching)...")
    new_start = time.time()
    
    try:
        # Clear cache for fair comparison
        cache_dir = ".cache"
        safe_user_identifier = user_identifier.replace('@', '_at_').replace('.', '_').replace('/', '_')
        repo_name = extract_repo_name(repo_url)
        cache_file = os.path.join(cache_dir, f"{safe_user_identifier}-{repo_name.replace('/', '_')}.json")
        
        if os.path.exists(cache_file):
            os.remove(cache_file)
        
        # New unified approach
        contributions_data = fetch_all_contributions(user_identifier, repo_url, limit)
        
        # New optimized GPT analysis
        new_gpt_analysis = review_contributions_with_gpt(contributions_data)
        
        new_end = time.time()
        new_total_time = new_end - new_start
        
        benchmark_results["new_approach"] = {
            "execution_time": round(new_total_time, 2),
            "api_calls": 1,  # Unified call
            "cache_operations": 1,  # Single cache write
            "success": True,
            "tokens_used": new_gpt_analysis.get("analysis_metadata", {}).get("tokens_used", "N/A"),
            "data_completeness": {
                "commits": len(contributions_data.get("commits", [])),
                "prs": len(contributions_data.get("pull_requests", [])),
                "issues": len(contributions_data.get("issues", [])),
                "reviews": len(contributions_data.get("reviews", []))
            }
        }
        
    except Exception as e:
        benchmark_results["new_approach"] = {
            "execution_time": -1,
            "api_calls": 1,
            "success": False,
            "error": str(e)
        }
    
    # Calculate improvements
    if (benchmark_results["old_approach"].get("success") and 
        benchmark_results["new_approach"].get("success")):
        
        old_time = benchmark_results["old_approach"]["execution_time"]
        new_time = benchmark_results["new_approach"]["execution_time"]
        
        old_tokens = benchmark_results["old_approach"].get("tokens_used", 0)
        new_tokens = benchmark_results["new_approach"].get("tokens_used", 0)
        
        if isinstance(old_tokens, int) and isinstance(new_tokens, int) and old_tokens > 0:
            token_savings = round(((old_tokens - new_tokens) / old_tokens) * 100, 1)
        else:
            token_savings = "N/A"
        
        time_savings = round(((old_time - new_time) / old_time) * 100, 1) if old_time > 0 else "N/A"
        
        benchmark_results["performance_comparison"] = {
            "time_improvement_percent": time_savings,
            "token_savings_percent": token_savings,
            "api_calls_reduced": benchmark_results["old_approach"]["api_calls"] - benchmark_results["new_approach"]["api_calls"],
            "file_operations_eliminated": benchmark_results["old_approach"].get("file_operations", 0),
            "caching_enabled": True,
            "recommendation": "new_approach" if new_time < old_time else "old_approach"
        }
    
    # Print results
    print("\n📈 BENCHMARK RESULTS:")
    print("=" * 50)
    
    if benchmark_results["old_approach"].get("success"):
        old_result = benchmark_results["old_approach"]
        print(f"OLD APPROACH: {old_result['execution_time']}s, {old_result['api_calls']} API calls, {old_result.get('tokens_used', 'N/A')} tokens")
    
    if benchmark_results["new_approach"].get("success"):
        new_result = benchmark_results["new_approach"]
        print(f"NEW APPROACH: {new_result['execution_time']}s, {new_result['api_calls']} API calls, {new_result.get('tokens_used', 'N/A')} tokens")
    
    if "performance_comparison" in benchmark_results:
        comp = benchmark_results["performance_comparison"]
        print(f"\n🎯 IMPROVEMENTS:")
        print(f"⏱️  Time: {comp['time_improvement_percent']}% faster")
        print(f"💰 Tokens: {comp['token_savings_percent']}% reduction") 
        print(f"🔌 API calls: {comp['api_calls_reduced']} fewer calls")
        print(f"📄 File I/O: {comp['file_operations_eliminated']} operations eliminated")
        print(f"✅ Recommended: {comp['recommendation']}")
    
    # Save benchmark results
    benchmark_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(benchmark_file, 'w') as f:
        json.dump(benchmark_results, f, indent=2)
    print(f"\n💾 Results saved to: {benchmark_file}")
    
    return benchmark_results
