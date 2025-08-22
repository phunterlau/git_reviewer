"""
GitHub data source for the Founding Engineer Review System.

This module handles all interactions with the GitHub API to collect
raw activity data for analysis.
"""

import os
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from github import Github
from github.GithubException import GithubException

from ..models.metrics import ActivityData


class GitHubDataSource:
    """GitHub API data source for collecting user activity data."""
    
    def __init__(self, github_token: str):
        """Initialize GitHub API client."""
        if not github_token:
            raise ValueError("GitHub token is required")
        
        self.g = Github(github_token)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def resolve_user_login(self, user_identifier: str) -> Optional[str]:
        """
        Resolve email or username to GitHub login.
        
        Args:
            user_identifier: GitHub username or email
            
        Returns:
            GitHub username or None if not found
        """
        if '@' not in user_identifier:
            # Already a username, verify it exists
            try:
                user = self.g.get_user(user_identifier)
                return user.login
            except GithubException:
                print(f"❌ User '{user_identifier}' not found")
                return None
        
        # Try to resolve email to username via commit search
        print(f"🔍 Resolving email {user_identifier} to GitHub username...")
        try:
            search_query = f"author-email:{user_identifier}"
            commits = self.g.search_commits(search_query)
            
            for commit in commits[:10]:
                if commit.author and commit.author.login:
                    print(f"✅ Resolved {user_identifier} -> {commit.author.login}")
                    return commit.author.login
        except Exception as e:
            print(f"⚠️  Could not resolve email: {e}")
        
        return None
    
    def get_user_events(self, username: str, months: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch user's public events from GitHub API.
        
        Args:
            username: GitHub username
            months: Number of months to look back
            
        Returns:
            List of events
        """
        print(f"📅 Fetching public events for {username} (last {months} months)...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        events = []
        
        try:
            user = self.g.get_user(username)
            user_events = user.get_events()
            
            for event in user_events:
                if event.created_at >= cutoff_date:
                    events.append({
                        'id': event.id,
                        'type': event.type,
                        'created_at': event.created_at.isoformat(),
                        'repo': event.repo.full_name if event.repo else None,
                        'payload': event.payload,
                        'public': event.public
                    })
            
            print(f"✅ Found {len(events)} recent events")
            return events
            
        except Exception as e:
            print(f"❌ Error fetching events: {e}")
            return []
    
    def get_commits_activity(self, username: str, months: int = 12, include_patches: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch commits across all accessible repositories.
        
        Args:
            username: GitHub username
            months: Number of months to look back
            include_patches: Whether to include code patches/diffs
            
        Returns:
            List of commit activities
        """
        print(f"📝 Fetching commits for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        commits = []
        
        try:
            # Use search API to find commits by author
            search_query = f"author:{username}"
            commit_results = self.g.search_commits(search_query, sort="author-date", order="desc")
            
            for commit in commit_results:
                if commit.commit.author.date >= cutoff_date:
                    commit_data = {
                        'sha': commit.sha,
                        'message': commit.commit.message,
                        'author_date': commit.commit.author.date.isoformat(),
                        'repository': commit.repository.full_name,
                        'url': commit.html_url,
                        'additions': commit.stats.additions,
                        'deletions': commit.stats.deletions,
                        'total_changes': commit.stats.total,
                        'files_changed': len(commit.files) if commit.files else 0
                    }
                    
                    if include_patches and commit.files:
                        commit_data['files'] = []
                        for file in commit.files:
                            file_data = {
                                'filename': file.filename,
                                'status': file.status,
                                'additions': file.additions,
                                'deletions': file.deletions,
                                'changes': file.changes
                            }
                            if file.patch:
                                file_data['patch'] = file.patch
                            commit_data['files'].append(file_data)
                    
                    commits.append(commit_data)
            
            print(f"✅ Found {len(commits)} commits")
            return commits
            
        except Exception as e:
            print(f"❌ Error fetching commits: {e}")
            return []
    
    def get_issues_activity(self, username: str, months: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch issues created by the user.
        
        Args:
            username: GitHub username
            months: Number of months to look back
            
        Returns:
            List of issue activities
        """
        print(f"🐛 Fetching issues for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        issues = []
        
        try:
            # Search for issues created by user
            search_query = f"author:{username} is:issue"
            issue_results = self.g.search_issues(search_query, sort="created", order="desc")
            
            for issue in issue_results:
                if issue.created_at >= cutoff_date:
                    issues.append({
                        'id': issue.id,
                        'number': issue.number,
                        'title': issue.title,
                        'body': issue.body[:500] if issue.body else "",  # Truncate for storage
                        'state': issue.state,
                        'created_at': issue.created_at.isoformat(),
                        'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
                        'closed_at': issue.closed_at.isoformat() if issue.closed_at else None,
                        'repository': issue.repository.full_name,
                        'url': issue.html_url,
                        'labels': [label.name for label in issue.labels],
                        'comments_count': issue.comments
                    })
            
            print(f"✅ Found {len(issues)} issues")
            return issues
            
        except Exception as e:
            print(f"❌ Error fetching issues: {e}")
            return []
    
    def get_pull_requests_activity(self, username: str, months: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch pull requests created by the user.
        
        Args:
            username: GitHub username
            months: Number of months to look back
            
        Returns:
            List of PR activities
        """
        print(f"🔀 Fetching pull requests for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        prs = []
        
        try:
            # Search for PRs created by user
            search_query = f"author:{username} is:pr"
            pr_results = self.g.search_issues(search_query, sort="created", order="desc")
            
            for pr_issue in pr_results:
                if pr_issue.created_at >= cutoff_date:
                    # Get the actual PR object for more details
                    try:
                        pr = pr_issue.repository.get_pull(pr_issue.number)
                        prs.append({
                            'id': pr.id,
                            'number': pr.number,
                            'title': pr.title,
                            'body': pr.body[:500] if pr.body else "",  # Truncate for storage
                            'state': pr.state,
                            'created_at': pr.created_at.isoformat(),
                            'updated_at': pr.updated_at.isoformat() if pr.updated_at else None,
                            'closed_at': pr.closed_at.isoformat() if pr.closed_at else None,
                            'merged_at': pr.merged_at.isoformat() if pr.merged_at else None,
                            'repository': pr.repository.full_name,
                            'url': pr.html_url,
                            'additions': pr.additions,
                            'deletions': pr.deletions,
                            'changed_files': pr.changed_files,
                            'commits': pr.commits,
                            'merged': pr.merged,
                            'draft': pr.draft,
                            'labels': [label.name for label in pr.labels],
                            'comments_count': pr.comments + pr.review_comments
                        })
                    except Exception as pr_error:
                        print(f"⚠️  Error getting PR details for #{pr_issue.number}: {pr_error}")
                        continue
            
            print(f"✅ Found {len(prs)} pull requests")
            return prs
            
        except Exception as e:
            print(f"❌ Error fetching pull requests: {e}")
            return []
    
    def get_comments_activity(self, username: str, months: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch issue and PR comments by the user using events API.
        
        Args:
            username: GitHub username
            months: Number of months to look back
            
        Returns:
            List of comment activities
        """
        print(f"💬 Fetching comments for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        comments = []
        
        try:
            # Get events and filter for comment events
            events = self.get_user_events(username, months)
            
            for event in events:
                if event['type'] in ['IssueCommentEvent', 'PullRequestReviewCommentEvent']:
                    comment_data = {
                        'id': event['id'],
                        'type': event['type'],
                        'created_at': event['created_at'],
                        'repository': event['repo'],
                        'url': event.get('payload', {}).get('comment', {}).get('html_url', ''),
                        'comment_body': event.get('payload', {}).get('comment', {}).get('body', '')[:200]  # Truncate
                    }
                    comments.append(comment_data)
            
            print(f"✅ Found {len(comments)} comments")
            return comments
            
        except Exception as e:
            print(f"❌ Error fetching comments: {e}")
            return []
    
    def get_reviews_activity(self, username: str, months: int = 12) -> List[Dict[str, Any]]:
        """
        Fetch code reviews by the user.
        
        Args:
            username: GitHub username
            months: Number of months to look back
            
        Returns:
            List of review activities
        """
        print(f"👀 Fetching code reviews for {username}...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        reviews = []
        
        try:
            # Search for PRs reviewed by user
            search_query = f"reviewed-by:{username} is:pr"
            pr_results = self.g.search_issues(search_query, sort="updated", order="desc")
            
            for pr_issue in pr_results:
                if pr_issue.updated_at >= cutoff_date:
                    try:
                        pr = pr_issue.repository.get_pull(pr_issue.number)
                        pr_reviews = pr.get_reviews()
                        
                        for review in pr_reviews:
                            if (review.user and review.user.login == username and 
                                review.submitted_at and review.submitted_at >= cutoff_date):
                                
                                reviews.append({
                                    'id': review.id,
                                    'pr_number': pr.number,
                                    'pr_title': pr.title,
                                    'state': review.state,
                                    'submitted_at': review.submitted_at.isoformat(),
                                    'repository': pr.repository.full_name,
                                    'url': review.html_url,
                                    'body': review.body[:200] if review.body else "",  # Truncate
                                    'commit_id': review.commit_id
                                })
                    except Exception as review_error:
                        print(f"⚠️  Error getting reviews for PR #{pr_issue.number}: {review_error}")
                        continue
            
            print(f"✅ Found {len(reviews)} code reviews")
            return reviews
            
        except Exception as e:
            print(f"❌ Error fetching reviews: {e}")
            return []
    
    def collect_comprehensive_activity(self, user_identifier: str, months: int = 12, include_patches: bool = False) -> ActivityData:
        """
        Collect all GitHub activities for a user in the specified time period.
        
        Args:
            user_identifier: GitHub username or email
            months: Number of months to look back
            include_patches: Whether to include code patches in commits
            
        Returns:
            ActivityData object with all collected data
        """
        print(f"🚀 Starting comprehensive activity collection for {user_identifier}")
        print(f"📅 Time range: Last {months} months")
        print("=" * 60)
        
        # Resolve to GitHub username
        username = self.resolve_user_login(user_identifier)
        if not username:
            raise ValueError(f"Could not resolve user: {user_identifier}")
        
        print(f"👤 Collecting data for: {username}")
        print()
        
        # Collect all activity types
        commits = self.get_commits_activity(username, months, include_patches)
        issues = self.get_issues_activity(username, months)
        pull_requests = self.get_pull_requests_activity(username, months)
        comments = self.get_comments_activity(username, months)
        reviews = self.get_reviews_activity(username, months)
        events = self.get_user_events(username, months)
        
        # Create timeline of all activities
        all_activities = []
        
        # Add commits to timeline
        for commit in commits:
            all_activities.append({
                'type': 'commit',
                'timestamp': commit['author_date'],
                'repository': commit['repository'],
                'data': commit
            })
        
        # Add issues to timeline
        for issue in issues:
            all_activities.append({
                'type': 'issue',
                'timestamp': issue['created_at'],
                'repository': issue['repository'],
                'data': issue
            })
        
        # Add PRs to timeline
        for pr in pull_requests:
            all_activities.append({
                'type': 'pull_request',
                'timestamp': pr['created_at'],
                'repository': pr['repository'],
                'data': pr
            })
        
        # Add reviews to timeline
        for review in reviews:
            all_activities.append({
                'type': 'review',
                'timestamp': review['submitted_at'],
                'repository': review['repository'],
                'data': review
            })
        
        # Sort timeline by timestamp (newest first)
        all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Calculate repository involvement
        repo_involvement = {}
        for activity in all_activities:
            repo = activity.get('repository')
            if repo:
                repo_involvement[repo] = repo_involvement.get(repo, 0) + 1
        
        # Create ActivityData object
        activity_data = ActivityData(
            commits=commits,
            issues=issues,
            pull_requests=pull_requests,
            comments=comments,
            reviews=reviews,
            events=events,
            timeline=all_activities,
            repository_involvement=repo_involvement,
            total_activities=len(all_activities)
        )
        
        print(f"\n📊 Collection Summary:")
        print("=" * 40)
        print(f"Total activities: {activity_data.total_activities}")
        print(f"  - Commits: {len(commits)}")
        print(f"  - Issues: {len(issues)}")
        print(f"  - Pull Requests: {len(pull_requests)}")
        print(f"  - Comments: {len(comments)}")
        print(f"  - Code Reviews: {len(reviews)}")
        print(f"Repositories involved: {len(repo_involvement)}")
        
        return activity_data
