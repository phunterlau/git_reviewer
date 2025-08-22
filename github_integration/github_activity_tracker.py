#!/usr/bin/env python3
"""
GitHub Activity Tracker

A comprehensive tool to fetch all GitHub activities (commits, issues, PRs, comments, reviews)
for a specific user in the last 365 days across all repositories they have access to.

Usage:
    uv run python github_activity_tracker.py --user phunterlau
    uv run python github_activity_tracker.py --user user@example.com --days 180 --format json
    uv run python github_activity_tracker.py --user phunterlau --include-private --save-raw
"""

import os
import json
import argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import requests
from github import Github
from github.GithubException import GithubException


class GitHubActivityTracker:
    def __init__(self, github_token):
        """Initialize the tracker with GitHub token."""
        if not github_token:
            raise ValueError("GitHub token is required")
        
        self.g = Github(github_token)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def resolve_user_login(self, user_identifier):
        """
        Resolve email or username to GitHub login.
        
        Args:
            user_identifier (str): GitHub username or email
            
        Returns:
            str: GitHub username or None if not found
        """
        if '@' not in user_identifier:
            # Already a username, verify it exists
            try:
                user = self.g.get_user(user_identifier)
                return user.login
            except GithubException:
                print(f"❌ User '{user_identifier}' not found")
                return None
        
        # Try to resolve email to username
        print(f"🔍 Resolving email {user_identifier} to GitHub username...")
        
        # Method 1: Search commits by author email
        try:
            search_query = f"author-email:{user_identifier}"
            commits = self.g.search_commits(search_query)
            
            for commit in commits[:10]:  # Check first 10 commits
                if commit.author and commit.author.login:
                    print(f"✅ Resolved {user_identifier} -> {commit.author.login}")
                    return commit.author.login
        except Exception as e:
            print(f"⚠️  Commit search failed: {e}")
        
        # Method 2: Try GraphQL API for more comprehensive search
        try:
            query = """
            query($email: String!) {
              search(query: $email, type: USER, first: 5) {
                nodes {
                  ... on User {
                    login
                    email
                  }
                }
              }
            }
            """
            
            response = requests.post(
                'https://api.github.com/graphql',
                headers={'Authorization': f'Bearer {self.token}'},
                json={'query': query, 'variables': {'email': user_identifier}},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('data', {}).get('search', {}).get('nodes', [])
                for user in users:
                    if user.get('email') == user_identifier:
                        print(f"✅ Resolved via GraphQL {user_identifier} -> {user['login']}")
                        return user['login']
        except Exception as e:
            print(f"⚠️  GraphQL search failed: {e}")
        
        print(f"❌ Could not resolve email {user_identifier} to GitHub username")
        return None
    
    def _analyze_file_type(self, filename):
        """
        Analyze file type and determine if content should be included.
        
        Args:
            filename (str): The filename to analyze
            
        Returns:
            tuple: (file_type, should_include_content)
        """
        import os
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        basename = os.path.basename(filename.lower())
        
        # Binary and media files - exclude
        binary_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp',
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
            '.mp3', '.wav', '.flac', '.aac', '.ogg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib', '.app',
            '.bin', '.dat', '.db', '.sqlite', '.sqlite3'
        }
        
        # Cache and temporary files - exclude
        cache_patterns = {
            '__pycache__', '.pytest_cache', 'node_modules', '.git',
            '.DS_Store', 'thumbs.db', '.vscode', '.idea',
            'dist', 'build', 'target', 'out', 'bin', 'obj',
            '.cache', 'coverage', '.nyc_output'
        }
        
        # Lock and generated files - exclude
        lock_files = {
            'package-lock.json', 'yarn.lock', 'poetry.lock', 'pipfile.lock',
            'gemfile.lock', 'composer.lock', 'go.sum'
        }
        
        # Data files and large content files - exclude
        data_file_patterns = {
            # Large data files
            '.csv', '.tsv', '.xlsx', '.xls',
            # Database dumps and exports
            '.sql', '.dump', '.backup',
            # Log files
            '.log', '.logs',
            # Large JSON data files (but keep small config JSONs)
            # We'll handle JSON specially below
        }
        
        # Large/generated JSON files to exclude
        large_json_files = {
            'package-lock.json', 'yarn.lock', 'composer.lock',
            'manifest.json', 'webpack-stats.json', 'tsconfig.json',
            'coverage.json', 'test-results.json', 'benchmark.json',
            'data.json', 'dataset.json', 'output.json', 'results.json'
        }
        
        # Check if should be excluded
        if ext in binary_extensions:
            return 'binary', False
        
        if basename in lock_files:
            return 'lock_file', False
        
        if ext in data_file_patterns:
            return 'data_file', False
        
        # Special handling for JSON files - exclude large data files but keep configs
        if ext == '.json':
            if basename in large_json_files:
                return 'large_json_data', False
            # Check file size indicators in name
            if any(pattern in basename for pattern in ['data', 'dataset', 'output', 'results', 'dump', 'export', 'backup']):
                return 'json_data', False
            # Very long filenames often indicate generated files
            if len(basename) > 50:
                return 'generated_json', False
        
        if any(pattern in filename.lower() for pattern in cache_patterns):
            return 'cache', False
        
        # Determine file type for included files
        code_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react_typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c_header',
            '.hpp': 'cpp_header',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch'
        }
        
        config_extensions = {
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'config',
            '.conf': 'config',
            '.env': 'environment',
            '.properties': 'properties'
        }
        
        # Specific config JSON files that should be included
        config_json_files = {
            'package.json', 'tsconfig.json', 'jsconfig.json',
            'babel.config.json', 'eslint.config.json', '.eslintrc.json',
            'prettier.config.json', '.prettierrc.json',
            'jest.config.json', 'webpack.config.json',
            'vscode/settings.json', 'vscode/launch.json', 'vscode/tasks.json',
            '.vscode/settings.json', '.vscode/launch.json', '.vscode/tasks.json',
            'manifest.json', 'composer.json', 'bower.json'
        }
        
        markup_extensions = {
            '.html': 'html',
            '.htm': 'html',
            '.xml': 'xml',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less'
        }
        
        doc_extensions = {
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.txt': 'text',
            '.rtf': 'rich_text',
            '.tex': 'latex'
        }
        
        # Categorize file type
        if ext in code_extensions:
            return code_extensions[ext], True
        elif ext in config_extensions:
            return config_extensions[ext], True
        elif ext == '.json':
            # Only include specific config JSON files
            if basename in config_json_files or any(config_name in filename for config_name in config_json_files):
                return 'json_config', True
            else:
                return 'json_data', False  # Exclude other JSON files as data
        elif ext in markup_extensions:
            return markup_extensions[ext], True
        elif ext in doc_extensions:
            return doc_extensions[ext], True
        elif basename in ['dockerfile', 'makefile', 'rakefile', 'justfile']:
            return basename, True
        elif ext in ['.gitignore', '.gitattributes', '.gitmodules']:
            return 'git_config', True
        elif filename.lower().startswith('readme'):
            return 'readme', True
        elif filename.lower().startswith('license'):
            return 'license', True
        elif filename.lower().startswith('changelog'):
            return 'changelog', True
        else:
            # Unknown text file - include but mark as unknown
            return 'unknown_text', True
    
    def _extract_change_summary(self, patch, file_type):
        """
        Extract a meaningful summary of changes from a patch.
        
        Args:
            patch (str): The git patch/diff content
            file_type (str): The type of file being changed
            
        Returns:
            dict: Summary of changes
        """
        if not patch:
            return {}
        
        lines = patch.split('\n')
        added_lines = []
        removed_lines = []
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:].strip())
        
        summary = {
            'lines_added': len(added_lines),
            'lines_removed': len(removed_lines),
        }
        
        # Extract key additions (non-empty, meaningful lines)
        meaningful_additions = [line for line in added_lines if line and not line.isspace() and len(line) > 3]
        if meaningful_additions:
            summary['key_additions'] = meaningful_additions[:5]  # First 5 meaningful additions
        
        # Extract key removals
        meaningful_removals = [line for line in removed_lines if line and not line.isspace() and len(line) > 3]
        if meaningful_removals:
            summary['key_removals'] = meaningful_removals[:5]  # First 5 meaningful removals
        
        # Code-specific analysis
        if file_type in ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust']:
            # Look for function/method definitions
            function_patterns = {
                'python': ['def ', 'class '],
                'javascript': ['function ', 'const ', 'let ', 'var '],
                'typescript': ['function ', 'const ', 'let ', 'interface ', 'type '],
                'java': ['public ', 'private ', 'protected ', 'class ', 'interface '],
                'cpp': ['void ', 'int ', 'class ', 'struct '],
                'go': ['func ', 'type ', 'var '],
                'rust': ['fn ', 'struct ', 'enum ', 'impl ']
            }
            
            if file_type in function_patterns:
                patterns = function_patterns[file_type]
                new_functions = []
                for line in meaningful_additions:
                    if any(pattern in line for pattern in patterns):
                        new_functions.append(line[:100])  # Truncate long function definitions
                
                if new_functions:
                    summary['new_functions'] = new_functions[:3]  # First 3 function definitions
        
        return summary
    
    def _get_file_type_emoji(self, file_type):
        """Get emoji representation for file type."""
        type_emojis = {
            'python': '🐍',
            'javascript': '📜',
            'typescript': '📘',
            'react': '⚛️',
            'react_typescript': '⚛️',
            'java': '☕',
            'c': '🔧',
            'cpp': '⚙️',
            'csharp': '🔷',
            'php': '🐘',
            'ruby': '💎',
            'go': '🐹',
            'rust': '🦀',
            'swift': '🍎',
            'kotlin': '🎯',
            'scala': '📊',
            'r': '📊',
            'sql': '🗄️',
            'shell': '🐚',
            'bash': '🐚',
            'json': '📋',
            'yaml': '📄',
            'toml': '📄',
            'html': '🌐',
            'css': '🎨',
            'scss': '🎨',
            'markdown': '📝',
            'dockerfile': '🐳',
            'makefile': '🔨',
            'git_config': '📚',
            'readme': '📖',
            'license': '📜',
            'changelog': '📰',
            'config': '⚙️',
            'environment': '🌍',
            'text': '📄',
            'binary': '📦',
            'unknown_text': '📄'
        }
        return type_emojis.get(file_type, '📄')
    
    def get_user_events(self, username, days=365):
        """
        Fetch user's public events from GitHub API.
        
        Args:
            username (str): GitHub username
            days (int): Number of days to look back
            
        Returns:
            list: List of events
        """
        print(f"📅 Fetching public events for {username} (last {days} days)...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        events = []
        
        try:
            user = self.g.get_user(username)
            user_events = user.get_events()
            
            for event in user_events:
                if event.created_at and event.created_at >= cutoff_date:
                    events.append(event)
                else:
                    # Events are ordered by date, so we can break early
                    break
                    
            print(f"✅ Found {len(events)} recent events")
            return events
            
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []
    
    def get_commits_activity(self, username, days=365, include_patches=False):
        """
        Fetch commits across all accessible repositories.
        
        Args:
            username (str): GitHub username
            days (int): Number of days to look back
            
        Returns:
            list: List of commit activities
        """
        print(f"📝 Fetching commits for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        commits = []
        
        try:
            # Use search API to find commits by author
            search_query = f"author:{username}"
            commit_results = self.g.search_commits(search_query, sort="author-date", order="desc")
            
            for commit in commit_results:
                if commit.commit.author and commit.commit.author.date:
                    if commit.commit.author.date >= cutoff_date:
                        # Get detailed file changes
                        file_changes = []
                        total_additions = 0
                        total_deletions = 0
                        
                        try:
                            # Fetch detailed commit data with file changes
                            detailed_commit = self.g.get_repo(commit.repository.full_name).get_commit(commit.sha)
                            
                            if hasattr(detailed_commit, 'files') and detailed_commit.files:
                                for file in detailed_commit.files:
                                    # Determine file type and whether to include content
                                    file_type, should_include_content = self._analyze_file_type(file.filename)
                                    
                                    # Skip binary, cache, and other non-essential files
                                    if not should_include_content:
                                        continue
                                    
                                    file_change = {
                                        'filename': file.filename,
                                        'file_type': file_type,
                                        'status': file.status,  # 'added', 'modified', 'removed', 'renamed'
                                        'additions': file.additions,
                                        'deletions': file.deletions,
                                        'changes': file.changes
                                    }
                                    
                                    # Include patch/diff only if requested and file is text-based
                                    if include_patches and file.patch and file_type != 'binary':
                                        # Clean and truncate patch content
                                        patch_content = file.patch
                                        if len(patch_content) > 2000:
                                            patch_content = patch_content[:2000] + "\n... [truncated for brevity]"
                                        file_change['patch'] = patch_content
                                        
                                        # Extract key changes for summary
                                        file_change['change_summary'] = self._extract_change_summary(file.patch, file_type)
                                    
                                    # Add previous filename for renames
                                    if hasattr(file, 'previous_filename') and file.previous_filename:
                                        file_change['previous_filename'] = file.previous_filename
                                    
                                    file_changes.append(file_change)
                                    total_additions += file.additions
                                    total_deletions += file.deletions
                            
                        except Exception as e:
                            print(f"⚠️  Could not fetch file details for commit {commit.sha[:8]}: {e}")
                            # Fallback to basic stats if available
                            if hasattr(commit, 'stats') and commit.stats:
                                total_additions = commit.stats.additions
                                total_deletions = commit.stats.deletions
                        
                        commits.append({
                            'type': 'commit',
                            'timestamp': commit.commit.author.date.isoformat(),
                            'repository': commit.repository.full_name,
                            'sha': commit.sha,
                            'message': commit.commit.message,
                            'url': commit.html_url,
                            'additions': total_additions,
                            'deletions': total_deletions,
                            'files_changed': len(file_changes),
                            'file_changes': file_changes
                        })
                    else:
                        break  # Commits are sorted by date
            
            print(f"✅ Found {len(commits)} commits")
            return commits
            
        except Exception as e:
            print(f"❌ Error fetching commits: {e}")
            return []
    
    def get_issues_activity(self, username, days=365):
        """
        Fetch issues created by the user.
        
        Args:
            username (str): GitHub username
            days (int): Number of days to look back
            
        Returns:
            list: List of issue activities
        """
        print(f"🐛 Fetching issues for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        issues = []
        
        try:
            # Search for issues created by user
            search_query = f"author:{username} is:issue"
            issue_results = self.g.search_issues(search_query, sort="created", order="desc")
            
            for issue in issue_results:
                if issue.created_at and issue.created_at >= cutoff_date:
                    issues.append({
                        'type': 'issue',
                        'timestamp': issue.created_at.isoformat(),
                        'repository': issue.repository.full_name if hasattr(issue, 'repository') else 'Unknown',
                        'number': issue.number,
                        'title': issue.title,
                        'body': issue.body[:500] + "..." if issue.body and len(issue.body) > 500 else issue.body,
                        'state': issue.state,
                        'url': issue.html_url,
                        'comments_count': issue.comments,
                        'labels': [label.name for label in issue.labels] if issue.labels else []
                    })
                else:
                    break
            
            print(f"✅ Found {len(issues)} issues")
            return issues
            
        except Exception as e:
            print(f"❌ Error fetching issues: {e}")
            return []
    
    def get_pull_requests_activity(self, username, days=365):
        """
        Fetch pull requests created by the user.
        
        Args:
            username (str): GitHub username
            days (int): Number of days to look back
            
        Returns:
            list: List of PR activities
        """
        print(f"🔀 Fetching pull requests for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        prs = []
        
        try:
            # Search for PRs created by user
            search_query = f"author:{username} is:pr"
            pr_results = self.g.search_issues(search_query, sort="created", order="desc")
            
            for pr_issue in pr_results:
                if pr_issue.created_at and pr_issue.created_at >= cutoff_date:
                    try:
                        pr = pr_issue.as_pull_request()
                        prs.append({
                            'type': 'pull_request',
                            'timestamp': pr_issue.created_at.isoformat(),
                            'repository': pr_issue.repository.full_name if hasattr(pr_issue, 'repository') else 'Unknown',
                            'number': pr_issue.number,
                            'title': pr_issue.title,
                            'body': pr_issue.body[:500] + "..." if pr_issue.body and len(pr_issue.body) > 500 else pr_issue.body,
                            'state': pr_issue.state,
                            'url': pr_issue.html_url,
                            'merged': pr.merged if hasattr(pr, 'merged') else False,
                            'mergeable': pr.mergeable if hasattr(pr, 'mergeable') else None,
                            'additions': pr.additions if hasattr(pr, 'additions') else 0,
                            'deletions': pr.deletions if hasattr(pr, 'deletions') else 0,
                            'changed_files': pr.changed_files if hasattr(pr, 'changed_files') else 0,
                            'comments_count': pr_issue.comments
                        })
                    except Exception as e:
                        print(f"⚠️  Could not fetch PR details for #{pr_issue.number}: {e}")
                else:
                    break
            
            print(f"✅ Found {len(prs)} pull requests")
            return prs
            
        except Exception as e:
            print(f"❌ Error fetching pull requests: {e}")
            return []
    
    def get_comments_activity(self, username, days=365):
        """
        Fetch issue and PR comments by the user using events API.
        
        Args:
            username (str): GitHub username
            days (int): Number of days to look back
            
        Returns:
            list: List of comment activities
        """
        print(f"💬 Fetching comments for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        comments = []
        
        try:
            # Get events and filter for comment events
            events = self.get_user_events(username, days)
            
            for event in events:
                if event.type in ['IssueCommentEvent', 'PullRequestReviewCommentEvent']:
                    if event.created_at >= cutoff_date:
                        payload = event.payload
                        comment_data = {
                            'type': 'comment',
                            'timestamp': event.created_at.isoformat(),
                            'repository': event.repo.name if event.repo else 'Unknown',
                            'event_type': event.type,
                            'url': payload.get('comment', {}).get('html_url', '') if payload else '',
                        }
                        
                        if payload and 'comment' in payload:
                            comment = payload['comment']
                            comment_data.update({
                                'body': comment.get('body', '')[:500] + "..." if comment.get('body', '') and len(comment.get('body', '')) > 500 else comment.get('body', ''),
                                'comment_id': comment.get('id'),
                            })
                        
                        if payload and 'issue' in payload:
                            issue = payload['issue']
                            comment_data.update({
                                'issue_number': issue.get('number'),
                                'issue_title': issue.get('title', '')
                            })
                        
                        comments.append(comment_data)
            
            print(f"✅ Found {len(comments)} comments")
            return comments
            
        except Exception as e:
            print(f"❌ Error fetching comments: {e}")
            return []
    
    def get_reviews_activity(self, username, days=365):
        """
        Fetch code reviews by the user.
        
        Args:
            username (str): GitHub username
            days (int): Number of days to look back
            
        Returns:
            list: List of review activities
        """
        print(f"👀 Fetching code reviews for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        reviews = []
        
        try:
            # Search for PRs reviewed by user
            search_query = f"reviewed-by:{username} is:pr"
            pr_results = self.g.search_issues(search_query, sort="updated", order="desc")
            
            for pr_issue in pr_results:
                if pr_issue.updated_at and pr_issue.updated_at >= cutoff_date:
                    try:
                        pr = pr_issue.as_pull_request()
                        pr_reviews = pr.get_reviews()
                        
                        for review in pr_reviews:
                            if (review.user and review.user.login == username and 
                                review.submitted_at and review.submitted_at >= cutoff_date):
                                
                                reviews.append({
                                    'type': 'review',
                                    'timestamp': review.submitted_at.isoformat(),
                                    'repository': pr_issue.repository.full_name if hasattr(pr_issue, 'repository') else 'Unknown',
                                    'pr_number': pr_issue.number,
                                    'pr_title': pr_issue.title,
                                    'review_state': review.state,
                                    'body': review.body[:500] + "..." if review.body and len(review.body) > 500 else review.body,
                                    'url': review.html_url if hasattr(review, 'html_url') else pr_issue.html_url
                                })
                    except Exception as e:
                        print(f"⚠️  Could not fetch reviews for PR #{pr_issue.number}: {e}")
                else:
                    break
            
            print(f"✅ Found {len(reviews)} code reviews")
            return reviews
            
        except Exception as e:
            print(f"❌ Error fetching reviews: {e}")
            return []
    
    def get_comprehensive_activity(self, user_identifier, days=365, include_private=False, include_patches=False):
        """
        Get all GitHub activities for a user in the specified time period.
        
        Args:
            user_identifier (str): GitHub username or email
            days (int): Number of days to look back (default: 365)
            include_private (bool): Whether to include private repo activities
            
        Returns:
            dict: Comprehensive activity data
        """
        print(f"🚀 Starting comprehensive activity analysis for {user_identifier}")
        print(f"📅 Time range: Last {days} days")
        print("=" * 60)
        
        # Resolve to GitHub username
        username = self.resolve_user_login(user_identifier)
        if not username:
            return None
        
        print(f"👤 Analyzing user: {username}")
        print()
        
        # Collect all activities
        activities = {
            'user': username,
            'original_identifier': user_identifier,
            'analysis_period_days': days,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'include_private': include_private,
        }
        
        # Fetch different types of activities
        activities['commits'] = self.get_commits_activity(username, days, include_patches)
        activities['issues'] = self.get_issues_activity(username, days)
        activities['pull_requests'] = self.get_pull_requests_activity(username, days)
        activities['comments'] = self.get_comments_activity(username, days)
        activities['reviews'] = self.get_reviews_activity(username, days)
        
        # Create timeline of all activities
        all_activities = []
        for activity_type in ['commits', 'issues', 'pull_requests', 'comments', 'reviews']:
            all_activities.extend(activities[activity_type])
        
        # Sort by timestamp (newest first)
        all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities['timeline'] = all_activities
        
        # Generate summary statistics
        activities['summary'] = {
            'total_activities': len(all_activities),
            'commits_count': len(activities['commits']),
            'issues_count': len(activities['issues']),
            'pull_requests_count': len(activities['pull_requests']),
            'comments_count': len(activities['comments']),
            'reviews_count': len(activities['reviews']),
            'repositories_involved': len(set(item.get('repository', 'Unknown') for item in all_activities if item.get('repository'))),
            'date_range': {
                'start': (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(),
                'end': datetime.now(timezone.utc).isoformat()
            }
        }
        
        # Repository breakdown
        repo_stats = defaultdict(int)
        for activity in all_activities:
            if activity.get('repository'):
                repo_stats[activity['repository']] += 1
        
        activities['repository_breakdown'] = dict(sorted(repo_stats.items(), key=lambda x: x[1], reverse=True))
        
        print("\n📊 Activity Summary:")
        print("=" * 40)
        summary = activities['summary']
        print(f"Total activities: {summary['total_activities']}")
        print(f"  - Commits: {summary['commits_count']}")
        print(f"  - Issues: {summary['issues_count']}")
        print(f"  - Pull Requests: {summary['pull_requests_count']}")
        print(f"  - Comments: {summary['comments_count']}")
        print(f"  - Code Reviews: {summary['reviews_count']}")
        print(f"Repositories involved: {summary['repositories_involved']}")
        
        if activities['repository_breakdown']:
            print(f"\nTop repositories:")
            for repo, count in list(activities['repository_breakdown'].items())[:5]:
                print(f"  - {repo}: {count} activities")
        
        return activities


def get_file_type_emoji(file_type):
    """Get emoji representation for file type."""
    type_emojis = {
        'python': '🐍',
        'javascript': '📜',
        'typescript': '📘',
        'react': '⚛️',
        'react_typescript': '⚛️',
        'java': '☕',
        'c': '🔧',
        'cpp': '⚙️',
        'csharp': '🔷',
        'php': '🐘',
        'ruby': '💎',
        'go': '🐹',
        'rust': '🦀',
        'swift': '🍎',
        'kotlin': '🎯',
        'scala': '📊',
        'r': '📊',
        'sql': '🗄️',
        'shell': '🐚',
        'bash': '🐚',
        'json': '📋',
        'json_config': '⚙️',
        'json_data': '📊',
        'yaml': '📄',
        'toml': '📄',
        'html': '🌐',
        'css': '🎨',
        'scss': '🎨',
        'markdown': '📝',
        'dockerfile': '🐳',
        'makefile': '🔨',
        'git_config': '📚',
        'readme': '📖',
        'license': '📜',
        'changelog': '📰',
        'config': '⚙️',
        'environment': '🌍',
        'text': '📄',
        'binary': '📦',
        'unknown_text': '📄',
        'data_file': '📊',
        'large_json_data': '📊',
        'generated_json': '🤖',
        'lock_file': '🔒',
        'cache': '💾'
    }
    return type_emojis.get(file_type, '📄')


def save_activity_data(activities, output_format='json', save_raw=False):
    """
    Save activity data to file.
    
    Args:
        activities (dict): Activity data
        output_format (str): Output format ('json' or 'markdown')
        save_raw (bool): Whether to save raw data as well
        
    Returns:
        str: Output filename
    """
    if not activities:
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    user = activities['user']
    days = activities['analysis_period_days']
    
    if output_format == 'json':
        filename = f"github_activity_{user}_{days}days_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(activities, f, indent=2)
        print(f"\n💾 Activity data saved to: {filename}")
        
    elif output_format == 'markdown':
        filename = f"github_activity_{user}_{days}days_{timestamp}.md"
        
        with open(filename, 'w') as f:
            f.write(f"# GitHub Activity Report: {user}\n\n")
            f.write(f"**Analysis Period:** {days} days\n")
            f.write(f"**Generated:** {activities['analysis_timestamp']}\n\n")
            
            # Summary
            summary = activities['summary']
            f.write("## Summary\n\n")
            f.write(f"- **Total Activities:** {summary['total_activities']}\n")
            f.write(f"- **Commits:** {summary['commits_count']}\n")
            f.write(f"- **Issues:** {summary['issues_count']}\n")
            f.write(f"- **Pull Requests:** {summary['pull_requests_count']}\n")
            f.write(f"- **Comments:** {summary['comments_count']}\n")
            f.write(f"- **Code Reviews:** {summary['reviews_count']}\n")
            f.write(f"- **Repositories:** {summary['repositories_involved']}\n\n")
            
            # Repository breakdown
            if activities['repository_breakdown']:
                f.write("## Repository Activity\n\n")
                for repo, count in activities['repository_breakdown'].items():
                    f.write(f"- **{repo}:** {count} activities\n")
                f.write("\n")
            
            # Timeline
            f.write("## Activity Timeline\n\n")
            for activity in activities['timeline']:
                timestamp = datetime.fromisoformat(activity['timestamp'].replace('Z', '+00:00'))
                f.write(f"### {timestamp.strftime('%Y-%m-%d %H:%M')} - {activity['type'].title()}\n")
                f.write(f"**Repository:** {activity.get('repository', 'Unknown')}\n")
                
                if activity['type'] == 'commit':
                    f.write(f"**Message:** {activity.get('message', '').split(chr(10))[0]}\n")
                    f.write(f"**Changes:** +{activity.get('additions', 0)}/-{activity.get('deletions', 0)} ({activity.get('files_changed', 0)} files)\n")
                    
                    # Add detailed file changes
                    file_changes = activity.get('file_changes', [])
                    if file_changes:
                        f.write(f"**Files Modified:**\n")
                        for file_change in file_changes[:10]:  # Limit to first 10 files for readability
                            status_emoji = {
                                'added': '✅',
                                'modified': '📝', 
                                'removed': '❌',
                                'renamed': '🔄'
                            }.get(file_change.get('status', ''), '📄')
                            
                            file_type = file_change.get('file_type', 'unknown')
                            type_emoji = get_file_type_emoji(file_type)
                            
                            f.write(f"  - {status_emoji} {type_emoji} `{file_change.get('filename', '')}` ")
                            f.write(f"(+{file_change.get('additions', 0)}/-{file_change.get('deletions', 0)}) *[{file_type}]*\n")
                            
                            if file_change.get('previous_filename'):
                                f.write(f"    ↳ *renamed from: {file_change['previous_filename']}*\n")
                            
                            # Add change summary if available
                            change_summary = file_change.get('change_summary', {})
                            if change_summary and change_summary.get('key_additions'):
                                f.write(f"    ↳ *Key additions: {', '.join(change_summary['key_additions'][:2])}*\n")
                            
                            if change_summary and change_summary.get('new_functions'):
                                f.write(f"    ↳ *New functions: {', '.join(change_summary['new_functions'][:2])}*\n")
                        
                        if len(file_changes) > 10:
                            f.write(f"  - ... and {len(file_changes) - 10} more files\n")
                        f.write("\n")
                elif activity['type'] in ['issue', 'pull_request']:
                    f.write(f"**Title:** {activity.get('title', '')}\n")
                    f.write(f"**State:** {activity.get('state', '')}\n")
                elif activity['type'] == 'comment':
                    f.write(f"**Issue:** #{activity.get('issue_number', '')} - {activity.get('issue_title', '')}\n")
                elif activity['type'] == 'review':
                    f.write(f"**PR:** #{activity.get('pr_number', '')} - {activity.get('pr_title', '')}\n")
                    f.write(f"**Review State:** {activity.get('review_state', '')}\n")
                
                f.write(f"**URL:** {activity.get('url', '')}\n\n")
        
        print(f"\n📄 Markdown report saved to: {filename}")
    
    # Save raw JSON data if requested
    if save_raw and output_format != 'json':
        raw_filename = f"github_activity_{user}_{days}days_{timestamp}_raw.json"
        with open(raw_filename, 'w') as f:
            json.dump(activities, f, indent=2)
        print(f"💾 Raw data saved to: {raw_filename}")
    
    return filename


def main():
    """Main function to run the GitHub Activity Tracker."""
    parser = argparse.ArgumentParser(
        description="Track comprehensive GitHub activities for a user",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user phunterlau
  %(prog)s --user user@example.com --days 180 --format json
  %(prog)s --user phunterlau --include-private --save-raw
  %(prog)s --user trivialfis --days 90 --format markdown --include-patches
        """
    )
    
    parser.add_argument(
        '--user', '-u',
        required=True,
        help='GitHub username or email address'
    )
    
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=365,
        help='Number of days to look back (default: 365, max: 365)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'markdown'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--include-private',
        action='store_true',
        help='Include private repository activities (requires appropriate token permissions)'
    )
    
    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='Also save raw JSON data when using markdown format'
    )
    
    parser.add_argument(
        '--include-patches',
        action='store_true',
        help='Include code patches/diffs in file changes (increases data size significantly)'
    )
    
    args = parser.parse_args()
    
    # Validate days
    if args.days > 365:
        print("⚠️  Warning: Maximum 365 days supported, using 365")
        args.days = 365
    
    print("🔍 GitHub Activity Tracker")
    print("=" * 50)
    print(f"User: {args.user}")
    print(f"Period: {args.days} days")
    print(f"Format: {args.format}")
    print(f"Include private: {args.include_private}")
    print()
    
    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ ERROR: GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub Personal Access Token:")
        print("export GITHUB_TOKEN=your_token_here")
        print("\nGenerate a token at: https://github.com/settings/tokens")
        if args.include_private:
            print("For private repositories, ensure your token has 'repo' scope")
        return 1
    
    try:
        # Initialize tracker
        tracker = GitHubActivityTracker(github_token)
        
        # Get comprehensive activity
        activities = tracker.get_comprehensive_activity(
            args.user, 
            args.days, 
            args.include_private,
            args.include_patches
        )
        
        if not activities:
            print("❌ Failed to fetch activity data")
            return 1
        
        # Save results
        output_file = save_activity_data(activities, args.format, args.save_raw)
        
        if output_file:
            print(f"\n✅ Analysis completed successfully!")
            print(f"📁 Output saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
