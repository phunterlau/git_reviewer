#!/usr/bin/env python3
"""
Contribution Impact Score (CIS) System for Founding Engineer Review

This module implements a robust, gaming-resistant scoring system inspired by the h-index
that evaluates the true impact and quality of a candidate's contributions.

The CIS prevents gaming through multi-layered scoring:
1. Substance Score: Filters for real technical work vs documentation/config changes
2. Quality Multiplier: Rewards engineering best practices (tests, documentation)
3. Community Multiplier: Measures external validation and project significance
4. Initiative Multiplier: Rewards self-directed work and ownership

Final Geek Index (g-index): A candidate has g-index of 'g' if they have 'g' contributions
each with CIS >= g, similar to h-index but for engineering contributions.
"""

import re
import math
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from github import Github
from github.GithubException import GithubException


@dataclass
class ContributionAnalysis:
    """Detailed analysis of a single contribution (PR or self-directed work cycle)."""
    contribution_id: str  # PR URL or issue-PR pair
    contribution_type: str  # 'external_pr', 'self_directed_cycle'
    repo_name: str
    repo_stars: int
    repo_forks: int
    title: str
    description: str
    
    # Raw metrics
    total_lines_changed: int
    files_changed: int
    lines_by_type: Dict[str, int]  # 'code', 'config', 'doc', 'excluded'
    
    # CIS Components
    substance_score: float
    quality_multiplier: float
    community_multiplier: float
    initiative_multiplier: float
    
    # Final score
    cis_score: float
    
    # Supporting evidence
    complexity_keywords: List[str]
    test_files_touched: bool
    substantive_comments: int
    self_directed: bool


@dataclass
class GeekIndexResult:
    """Final geek index calculation with detailed breakdown."""
    username: str
    total_contributions: int
    geek_index: int
    contributions: List[ContributionAnalysis]
    index_breakdown: Dict[str, Any]


class ContributionImpactScorer:
    """Calculates robust, gaming-resistant contribution impact scores."""
    
    def __init__(self, github_token: str):
        """Initialize the CIS scorer with GitHub API access."""
        self.g = Github(github_token)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Initialize patterns for analysis
        self._init_analysis_patterns()
    
    def _init_analysis_patterns(self):
        """Initialize patterns for code analysis and complexity detection."""
        
        # File type classification patterns
        self.code_extensions = {
            '.py', '.js', '.ts', '.rs', '.go', '.java', '.cpp', '.c', '.cs', 
            '.php', '.rb', '.swift', '.kt', '.scala', '.clj', '.hs', '.ml',
            '.r', '.jl', '.dart', '.elm', '.zig', '.nim'
        }
        
        self.config_extensions = {
            '.json', '.yml', '.yaml', '.toml', '.xml', '.ini', '.cfg', '.conf',
            '.properties', '.env', '.gitignore', '.dockerignore'
        }
        
        self.doc_extensions = {
            '.md', '.rst', '.txt', '.adoc', '.org', '.tex'
        }
        
        self.excluded_patterns = {
            'package-lock.json', 'yarn.lock', 'Cargo.lock', 'composer.lock',
            'requirements.txt', 'Pipfile.lock', 'poetry.lock', 'go.sum',
            '.bin', '.exe', '.so', '.dll', '.dylib', '.a', '.o',
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pdf',
            '.log', '.out', '.tmp', '.cache', '.DS_Store'
        }
        
        # Complexity keywords that indicate sophisticated code
        self.complexity_keywords = {
            'python': ['async', 'await', 'class', 'def', 'try', 'except', 'finally', 
                      'with', 'yield', 'lambda', 'decorator', '__init__', '__enter__', '__exit__'],
            'javascript': ['async', 'await', 'class', 'function', 'try', 'catch', 'finally',
                          'promise', 'generator', 'prototype', 'constructor'],
            'rust': ['impl', 'trait', 'struct', 'enum', 'match', 'async', 'await',
                    'unsafe', 'macro', 'generic'],
            'go': ['func', 'struct', 'interface', 'goroutine', 'channel', 'select',
                  'defer', 'panic', 'recover'],
            'general': ['algorithm', 'optimization', 'concurrent', 'parallel', 'mutex',
                       'atomic', 'cache', 'database', 'api', 'protocol']
        }
        
        # Test file patterns
        self.test_patterns = [
            r'test_.*\.py$', r'.*_test\.py$', r'.*\.test\.js$', r'.*\.spec\.js$',
            r'.*_test\.go$', r'.*\.test\.ts$', r'.*\.spec\.ts$', r'test.*\.rs$',
            r'tests?/', r'spec/', r'__tests__/'
        ]
    
    def classify_file_changes(self, patch_content: str, filename: str) -> Tuple[str, int]:
        """
        Classify file changes by type and count meaningful lines.
        
        Args:
            patch_content: The patch content for this file
            filename: Name of the file being changed
            
        Returns:
            Tuple of (file_type, meaningful_lines_changed)
        """
        # Check if file should be excluded
        if any(pattern in filename.lower() for pattern in self.excluded_patterns):
            return 'excluded', 0
        
        # Get file extension
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Classify file type
        if file_ext in self.code_extensions:
            file_type = 'code'
        elif file_ext in self.config_extensions:
            file_type = 'config'
        elif file_ext in self.doc_extensions:
            file_type = 'doc'
        else:
            file_type = 'code'  # Default to code for unknown extensions
        
        # Count meaningful lines (additions, not deletions or context)
        meaningful_lines = 0
        for line in patch_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                meaningful_lines += 1
        
        return file_type, meaningful_lines
    
    def detect_complexity_indicators(self, patch_content: str, language: str = None) -> List[str]:
        """
        Detect complexity indicators in the patch content.
        
        Args:
            patch_content: The patch content to analyze
            language: Optional language hint for better keyword detection
            
        Returns:
            List of complexity keywords found
        """
        patch_lower = patch_content.lower()
        found_keywords = set()
        
        # Check language-specific keywords
        if language and language in self.complexity_keywords:
            for keyword in self.complexity_keywords[language]:
                if re.search(r'\b' + re.escape(keyword) + r'\b', patch_lower):
                    found_keywords.add(keyword)
        
        # Check general complexity keywords
        for keyword in self.complexity_keywords['general']:
            if re.search(r'\b' + re.escape(keyword) + r'\b', patch_lower):
                found_keywords.add(keyword)
        
        return list(found_keywords)
    
    def check_test_inclusion(self, files_changed: List[str]) -> bool:
        """
        Check if the contribution includes test files.
        
        Args:
            files_changed: List of filenames that were changed
            
        Returns:
            True if test files were included
        """
        for filename in files_changed:
            for pattern in self.test_patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    return True
        return False
    
    def calculate_substance_score(self, lines_by_type: Dict[str, int], 
                                complexity_keywords: List[str]) -> float:
        """
        Calculate the substance score based on what was actually changed.
        
        Formula: log((Code*1.0 + Config*0.5 + Doc*0.2) * ComplexityFactor + 1)
        ComplexityFactor = 1 + (0.1 * num_complexity_keywords)
        """
        weighted_lines = (
            lines_by_type.get('code', 0) * 1.0 +
            lines_by_type.get('config', 0) * 0.5 +
            lines_by_type.get('doc', 0) * 0.2
        )
        
        complexity_factor = 1 + (0.1 * len(complexity_keywords))
        
        substance_score = math.log(weighted_lines * complexity_factor + 1)
        
        return substance_score
    
    def calculate_quality_multiplier(self, test_files_touched: bool) -> float:
        """
        Calculate quality multiplier based on engineering best practices.
        
        Args:
            test_files_touched: Whether tests were included in the contribution
            
        Returns:
            Quality multiplier (1.0 or 1.5)
        """
        return 1.5 if test_files_touched else 1.0
    
    def calculate_community_multiplier(self, repo_stars: int, substantive_comments: int) -> float:
        """
        Calculate community multiplier based on project significance and discussion.
        
        Formula: 1 + log10(repo_stars + 1) + log(substantive_comments + 1)
        """
        repo_factor = math.log10(repo_stars + 1)
        discussion_factor = math.log(substantive_comments + 1)
        
        return 1 + repo_factor + discussion_factor
    
    def calculate_initiative_multiplier(self, is_self_directed: bool) -> float:
        """
        Calculate initiative multiplier for self-directed work.
        
        Args:
            is_self_directed: Whether this was a self-directed work cycle
            
        Returns:
            Initiative multiplier (1.0 or 2.0)
        """
        return 2.0 if is_self_directed else 1.0
    
    def analyze_pr_contribution(self, pr_url: str, username: str) -> Optional[ContributionAnalysis]:
        """
        Analyze a single PR contribution and calculate its CIS score.
        
        Args:
            pr_url: URL of the pull request
            username: Username of the contributor
            
        Returns:
            ContributionAnalysis object or None if analysis fails
        """
        try:
            # Extract repo and PR number from URL
            parts = pr_url.replace('https://github.com/', '').split('/')
            if len(parts) >= 4 and parts[2] == 'pull':
                repo_name = f"{parts[0]}/{parts[1]}"
                pr_number = int(parts[3])
            else:
                return None
            
            # Get PR details
            pr_api_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
            pr_response = requests.get(pr_api_url, headers=self.headers)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            # Get repository details
            repo_api_url = f"https://api.github.com/repos/{repo_name}"
            repo_response = requests.get(repo_api_url, headers=self.headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            
            # Get files changed in the PR
            files_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/files"
            files_response = requests.get(files_url, headers=self.headers)
            files_response.raise_for_status()
            files_data = files_response.json()
            
            # Analyze file changes
            lines_by_type = {'code': 0, 'config': 0, 'doc': 0, 'excluded': 0}
            total_lines_changed = 0
            files_changed = []
            all_patch_content = ""
            
            for file_info in files_data:
                filename = file_info.get('filename', '')
                files_changed.append(filename)
                
                patch = file_info.get('patch', '')
                all_patch_content += patch + "\n"
                
                file_type, meaningful_lines = self.classify_file_changes(patch, filename)
                lines_by_type[file_type] += meaningful_lines
                total_lines_changed += meaningful_lines
            
            # Detect complexity
            language = repo_data.get('language', '').lower() if repo_data.get('language') else None
            complexity_keywords = self.detect_complexity_indicators(all_patch_content, language)
            
            # Check for tests
            test_files_touched = self.check_test_inclusion(files_changed)
            
            # Count substantive comments (filter out short ones)
            substantive_comments = 0
            try:
                comments_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments"
                comments_response = requests.get(comments_url, headers=self.headers)
                if comments_response.status_code == 200:
                    comments_data = comments_response.json()
                    for comment in comments_data:
                        body = comment.get('body', '')
                        # Consider comments with >20 chars as substantive
                        if len(body.strip()) > 20:
                            substantive_comments += 1
            except:
                pass  # Non-critical if we can't get comments
            
            # Determine if self-directed (check if PR author opened a related issue)
            is_self_directed = False
            pr_author = pr_data.get('user', {}).get('login', '')
            if pr_author == username:
                # This is a simplified check - in reality we'd need to check if they opened related issues
                is_self_directed = 'fixes #' in pr_data.get('body', '').lower() or 'closes #' in pr_data.get('body', '').lower()
            
            # Calculate CIS components
            substance_score = self.calculate_substance_score(lines_by_type, complexity_keywords)
            quality_multiplier = self.calculate_quality_multiplier(test_files_touched)
            community_multiplier = self.calculate_community_multiplier(
                repo_data.get('stargazers_count', 0), 
                substantive_comments
            )
            initiative_multiplier = self.calculate_initiative_multiplier(is_self_directed)
            
            # Calculate final CIS score
            cis_score = substance_score * quality_multiplier * community_multiplier * initiative_multiplier
            
            return ContributionAnalysis(
                contribution_id=pr_url,
                contribution_type='self_directed_cycle' if is_self_directed else 'external_pr',
                repo_name=repo_name,
                repo_stars=repo_data.get('stargazers_count', 0),
                repo_forks=repo_data.get('forks_count', 0),
                title=pr_data.get('title', ''),
                description=pr_data.get('body', '')[:200] + '...' if pr_data.get('body') else '',
                total_lines_changed=total_lines_changed,
                files_changed=len(files_changed),
                lines_by_type=lines_by_type,
                substance_score=substance_score,
                quality_multiplier=quality_multiplier,
                community_multiplier=community_multiplier,
                initiative_multiplier=initiative_multiplier,
                cis_score=cis_score,
                complexity_keywords=complexity_keywords,
                test_files_touched=test_files_touched,
                substantive_comments=substantive_comments,
                self_directed=is_self_directed
            )
            
        except Exception as e:
            print(f"⚠️ Error analyzing PR {pr_url}: {e}")
            return None
    
    def find_user_contributions(self, username: str, max_contributions: int = 20) -> List[str]:
        """
        Find significant contributions by a user (merged PRs to external repos).
        
        Args:
            username: GitHub username
            max_contributions: Maximum number of contributions to find
            
        Returns:
            List of PR URLs
        """
        print(f"🔍 Finding contributions by {username}...")
        
        try:
            # Search for PRs authored by the user
            search_query = f"author:{username} is:pr is:merged"
            
            url = f"https://api.github.com/search/issues"
            params = {
                'q': search_query,
                'sort': 'updated',
                'order': 'desc',
                'per_page': min(max_contributions, 100)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            search_results = response.json()
            
            pr_urls = []
            user_repos = set()
            
            # Get user's own repositories to filter out self-contributions
            try:
                user = self.g.get_user(username)
                user_repos = {repo.full_name for repo in user.get_repos()}
            except:
                pass
            
            for item in search_results.get('items', []):
                pr_url = item.get('html_url', '')
                if pr_url and '/pull/' in pr_url:
                    # Extract repo name to check if it's external
                    parts = pr_url.replace('https://github.com/', '').split('/')
                    if len(parts) >= 2:
                        repo_name = f"{parts[0]}/{parts[1]}"
                        # Only include external repositories
                        if repo_name not in user_repos:
                            pr_urls.append(pr_url)
            
            print(f"   ✅ Found {len(pr_urls)} external contributions")
            return pr_urls[:max_contributions]
            
        except Exception as e:
            print(f"⚠️ Error finding contributions: {e}")
            return []
    
    def calculate_geek_index(self, username: str, max_contributions: int = 20) -> GeekIndexResult:
        """
        Calculate the complete Geek Index for a user.
        
        Args:
            username: GitHub username
            max_contributions: Maximum contributions to analyze
            
        Returns:
            GeekIndexResult with complete analysis
        """
        print(f"🧮 Calculating Geek Index for {username}...")
        
        # Find contributions
        pr_urls = self.find_user_contributions(username, max_contributions)
        
        # Analyze each contribution
        contributions = []
        for pr_url in pr_urls:
            analysis = self.analyze_pr_contribution(pr_url, username)
            if analysis and analysis.cis_score > 0:
                contributions.append(analysis)
        
        # Sort by CIS score (descending)
        contributions.sort(key=lambda x: x.cis_score, reverse=True)
        
        # Calculate g-index
        geek_index = 0
        for i, contribution in enumerate(contributions, 1):
            if contribution.cis_score >= i:
                geek_index = i
            else:
                break
        
        # Create breakdown
        index_breakdown = {
            'total_contributions_found': len(pr_urls),
            'valid_contributions_analyzed': len(contributions),
            'geek_index': geek_index,
            'average_cis_score': sum(c.cis_score for c in contributions) / len(contributions) if contributions else 0,
            'score_distribution': {
                'substance_scores': [c.substance_score for c in contributions[:10]],
                'quality_multipliers': [c.quality_multiplier for c in contributions[:10]],
                'community_multipliers': [c.community_multiplier for c in contributions[:10]],
                'initiative_multipliers': [c.initiative_multiplier for c in contributions[:10]]
            },
            'top_contributions': [
                {
                    'title': c.title,
                    'repo': c.repo_name,
                    'cis_score': c.cis_score,
                    'repo_stars': c.repo_stars
                } for c in contributions[:5]
            ]
        }
        
        print(f"   ✅ Geek Index calculated: {geek_index}")
        print(f"   📊 Analyzed {len(contributions)} valid contributions")
        
        return GeekIndexResult(
            username=username,
            total_contributions=len(contributions),
            geek_index=geek_index,
            contributions=contributions,
            index_breakdown=index_breakdown
        )
