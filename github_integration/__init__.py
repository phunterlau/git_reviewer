"""
GitHub Integration - Optimized GitHub API interaction with caching and rate limiting
"""

from .github_utils import (
    get_commits_optimized, 
    get_commits,
    get_commits_original,
    fetch_all_contributions,
    extract_repo_name,
    benchmark_contribution_methods,
    get_issues,
    get_pull_requests
)

__all__ = [
    'get_commits_optimized',
    'get_commits', 
    'get_commits_original',
    'fetch_all_contributions',
    'extract_repo_name',
    'benchmark_contribution_methods',
    'get_issues',
    'get_pull_requests'
]
