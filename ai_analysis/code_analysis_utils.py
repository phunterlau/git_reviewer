#!/usr/bin/env python3
"""
Code Analysis Utilities for Enhanced Founding Engineer Review

This module provides deep code analysis capabilities that go beyond metadata
to analyze actual code content, commit patches, and quality indicators.

Features:
- Commit patch analysis for code quality signals
- API design sense evaluation
- Code complexity assessment
- Anti-pattern detection
"""

import re
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from github import Github
from github.GithubException import GithubException


@dataclass
class CodeQualitySignal:
    """Represents a code quality signal found in commit analysis."""
    signal_type: str  # 'positive', 'negative', 'neutral'
    category: str     # 'documentation', 'testing', 'error_handling', 'api_design', etc.
    description: str
    evidence: str     # Code snippet or commit reference
    confidence: float # 0.0 to 1.0


@dataclass
class CommitAnalysis:
    """Analysis results for a single commit."""
    commit_sha: str
    commit_message: str
    author: str
    date: str
    files_changed: int
    additions: int
    deletions: int
    quality_signals: List[CodeQualitySignal]
    complexity_score: float
    api_design_score: float


class CodeAnalyzer:
    """Analyzes actual code content and commit patches for quality indicators."""
    
    def __init__(self, github_token: str):
        """Initialize the code analyzer with GitHub API access."""
        self.g = Github(github_token)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Define patterns for quality signal detection
        self._init_quality_patterns()
    
    def _init_quality_patterns(self):
        """Initialize regex patterns for detecting code quality signals."""
        
        # Positive signals
        self.positive_patterns = {
            'documentation': [
                r'"""[\s\S]*?"""',  # Python docstrings
                r'/\*\*[\s\S]*?\*/',  # JSDoc comments
                r'#\s*TODO:.*',  # Well-formatted TODOs
                r'#\s*FIXME:.*',  # Well-formatted FIXMEs
                r'//\s*.*explanation.*',  # Explanatory comments
            ],
            'testing': [
                r'def test_.*\(',  # Python test functions
                r'it\(.*,\s*function\(',  # JavaScript test functions
                r'describe\(.*,\s*function\(',  # JavaScript test suites
                r'@pytest\.fixture',  # pytest fixtures
                r'assert.*',  # Assertions
                r'expect\(.*\)\.to',  # Chai/Jest expectations
            ],
            'error_handling': [
                r'try:[\s\S]*?except.*:',  # Python try-except
                r'if\s+.*\s+is None:',  # None checks
                r'if\s+not\s+.*:',  # Defensive programming
                r'raise\s+.*Error\(',  # Proper exception raising
                r'\.catch\(',  # JavaScript error handling
            ],
            'api_design': [
                r'@app\.route\(',  # Flask routes
                r'@api\.route\(',  # API routes
                r'class.*APIView',  # Django API views
                r'def\s+(get|post|put|delete)_.*\(',  # RESTful methods
                r'pydantic',  # Input validation
                r'marshmallow',  # Serialization
            ]
        }
        
        # Negative signals (anti-patterns)
        self.negative_patterns = {
            'code_smell': [
                r'#.*commented.*out',  # Commented out code references
                r'print\(.*debug.*\)',  # Debug prints left in code
                r'console\.log\(',  # Console logs in production
                r'TODO.*urgent.*',  # Urgent TODOs (technical debt)
                r'HACK.*',  # Acknowledged hacks
                r'XXX.*',  # Problematic code markers
            ],
            'complexity': [
                r'if.*if.*if.*if.*:',  # Deeply nested conditionals
                r'for.*for.*for.*:',  # Deeply nested loops
                r'def\s+\w+\([^)]{100,}\)',  # Functions with many parameters
                r'class\s+\w+\([^)]{50,}\)',  # Classes with many inheritance
            ],
            'security': [
                r'eval\(',  # eval() usage
                r'exec\(',  # exec() usage
                r'\.raw\(',  # Raw SQL queries
                r'password\s*=\s*["\'].*["\']',  # Hardcoded passwords
                r'api_key\s*=\s*["\'].*["\']',  # Hardcoded API keys
            ]
        }
    
    def analyze_commit_patch(self, repo_full_name: str, commit_sha: str) -> CommitAnalysis:
        """
        Analyze a specific commit's patch for code quality signals.
        
        Args:
            repo_full_name: Repository name in format "owner/repo"
            commit_sha: Commit SHA to analyze
            
        Returns:
            CommitAnalysis object with detailed analysis
        """
        try:
            # Get commit details
            url = f"https://api.github.com/repos/{repo_full_name}/commits/{commit_sha}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            commit_data = response.json()
            
            # Extract basic commit info
            commit_message = commit_data.get('commit', {}).get('message', '')
            author = commit_data.get('commit', {}).get('author', {}).get('name', '')
            date = commit_data.get('commit', {}).get('author', {}).get('date', '')
            
            stats = commit_data.get('stats', {})
            files_changed = len(commit_data.get('files', []))
            additions = stats.get('additions', 0)
            deletions = stats.get('deletions', 0)
            
            # Analyze patch content
            quality_signals = []
            patch_content = ""
            
            for file_data in commit_data.get('files', []):
                if 'patch' in file_data:
                    patch_content += file_data['patch'] + "\n"
            
            # Detect quality signals in patch
            quality_signals.extend(self._detect_positive_signals(patch_content))
            quality_signals.extend(self._detect_negative_signals(patch_content))
            
            # Calculate complexity and API design scores
            complexity_score = self._calculate_complexity_score(patch_content, files_changed, additions)
            api_design_score = self._calculate_api_design_score(patch_content, commit_data.get('files', []))
            
            return CommitAnalysis(
                commit_sha=commit_sha,
                commit_message=commit_message,
                author=author,
                date=date,
                files_changed=files_changed,
                additions=additions,
                deletions=deletions,
                quality_signals=quality_signals,
                complexity_score=complexity_score,
                api_design_score=api_design_score
            )
            
        except Exception as e:
            print(f"⚠️ Error analyzing commit {commit_sha}: {e}")
            return CommitAnalysis(
                commit_sha=commit_sha,
                commit_message="",
                author="",
                date="",
                files_changed=0,
                additions=0,
                deletions=0,
                quality_signals=[],
                complexity_score=0.0,
                api_design_score=0.0
            )
    
    def _detect_positive_signals(self, patch_content: str) -> List[CodeQualitySignal]:
        """Detect positive code quality signals in patch content."""
        signals = []
        
        for category, patterns in self.positive_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, patch_content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    evidence = match.group(0)[:100]  # First 100 chars
                    if evidence.strip():  # Only non-empty matches
                        signals.append(CodeQualitySignal(
                            signal_type='positive',
                            category=category,
                            description=f"Added {category} improvement",
                            evidence=evidence,
                            confidence=0.8
                        ))
        
        return signals
    
    def _detect_negative_signals(self, patch_content: str) -> List[CodeQualitySignal]:
        """Detect negative code quality signals (anti-patterns) in patch content."""
        signals = []
        
        for category, patterns in self.negative_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, patch_content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    evidence = match.group(0)[:100]  # First 100 chars
                    if evidence.strip():  # Only non-empty matches
                        signals.append(CodeQualitySignal(
                            signal_type='negative',
                            category=category,
                            description=f"Potential {category} issue detected",
                            evidence=evidence,
                            confidence=0.7
                        ))
        
        return signals
    
    def _calculate_complexity_score(self, patch_content: str, files_changed: int, additions: int) -> float:
        """Calculate complexity score based on patch characteristics."""
        # Base score starts at 0.5
        score = 0.5
        
        # Adjust for change size
        if additions > 500:  # Large changes are more complex
            score += 0.2
        elif additions < 50:  # Small focused changes are simpler
            score -= 0.1
        
        # Adjust for file count
        if files_changed > 10:  # Many files touched
            score += 0.2
        elif files_changed == 1:  # Single file change
            score -= 0.1
        
        # Check for complexity indicators in patch
        complexity_indicators = [
            r'if.*if.*if',  # Nested conditionals
            r'for.*for.*for',  # Nested loops
            r'while.*while',  # Nested while loops
            r'lambda.*lambda',  # Nested lambdas
        ]
        
        for pattern in complexity_indicators:
            if re.search(pattern, patch_content):
                score += 0.1
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def _calculate_api_design_score(self, patch_content: str, files: List[Dict]) -> float:
        """Calculate API design sense score based on API-related changes."""
        score = 0.5  # Neutral starting point
        
        # Check if this commit touches API files
        api_files = ['api', 'router', 'handler', 'controller', 'endpoint']
        touches_api = any(
            any(keyword in file_data.get('filename', '').lower() for keyword in api_files)
            for file_data in files
        )
        
        if not touches_api:
            return 0.0  # No API changes to analyze
        
        # Positive API design patterns
        positive_api_patterns = [
            r'@app\.route.*methods=\[',  # Explicit HTTP methods
            r'def\s+(get|post|put|delete|patch)_\w+',  # RESTful method naming
            r'pydantic\.BaseModel',  # Input validation models
            r'response_model=',  # FastAPI response models
            r'status_code=',  # Explicit status codes
            r'HTTPException',  # Proper error handling
            r'@api\.doc',  # API documentation
            r'swagger',  # API documentation
        ]
        
        for pattern in positive_api_patterns:
            if re.search(pattern, patch_content, re.IGNORECASE):
                score += 0.1
        
        # Negative API design patterns
        negative_api_patterns = [
            r'@app\.route.*<',  # Generic route parameters
            r'request\.args\.get\(',  # Direct request parsing without validation
            r'return.*dict\(',  # Unstructured responses
            r'print\(',  # Debug prints in API code
        ]
        
        for pattern in negative_api_patterns:
            if re.search(pattern, patch_content, re.IGNORECASE):
                score -= 0.15
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def analyze_user_commits(self, username: str, max_commits: int = 10) -> List[CommitAnalysis]:
        """
        Analyze recent commits from a user across their repositories.
        
        Args:
            username: GitHub username
            max_commits: Maximum number of commits to analyze
            
        Returns:
            List of CommitAnalysis objects for the user's recent commits
        """
        print(f"🔍 Analyzing code content for {username} (max {max_commits} commits)...")
        
        analyses = []
        commits_analyzed = 0
        
        try:
            user = self.g.get_user(username)
            repos = list(user.get_repos(type='all', sort='updated', direction='desc')[:10])
            
            for repo in repos:
                if commits_analyzed >= max_commits:
                    break
                
                try:
                    # Get recent commits from this repo by the user
                    commits = list(repo.get_commits(author=username)[:3])  # Max 3 per repo
                    
                    for commit in commits:
                        if commits_analyzed >= max_commits:
                            break
                        
                        analysis = self.analyze_commit_patch(repo.full_name, commit.sha)
                        if analysis.quality_signals or analysis.additions > 0:  # Only include meaningful commits
                            analyses.append(analysis)
                            commits_analyzed += 1
                            
                except Exception as e:
                    print(f"⚠️ Error analyzing repo {repo.name}: {e}")
                    continue
            
            print(f"   ✅ Analyzed {len(analyses)} commits with code content")
            
        except Exception as e:
            print(f"⚠️ Error in commit analysis: {e}")
        
        return analyses
    
    def summarize_code_quality(self, analyses: List[CommitAnalysis]) -> Dict[str, Any]:
        """
        Summarize code quality findings across multiple commit analyses.
        
        Args:
            analyses: List of CommitAnalysis objects
            
        Returns:
            Summary dictionary with quality metrics and insights
        """
        if not analyses:
            return {
                'total_commits_analyzed': 0,
                'quality_score': 0.0,
                'positive_signals': {},
                'negative_signals': {},
                'avg_complexity_score': 0.0,
                'avg_api_design_score': 0.0,
                'top_quality_indicators': [],
                'top_concerns': []
            }
        
        # Aggregate signals by category
        positive_signals = {}
        negative_signals = {}
        
        for analysis in analyses:
            for signal in analysis.quality_signals:
                if signal.signal_type == 'positive':
                    positive_signals[signal.category] = positive_signals.get(signal.category, 0) + 1
                elif signal.signal_type == 'negative':
                    negative_signals[signal.category] = negative_signals.get(signal.category, 0) + 1
        
        # Calculate averages
        avg_complexity = sum(a.complexity_score for a in analyses) / len(analyses)
        avg_api_design = sum(a.api_design_score for a in analyses) / len(analyses) if any(a.api_design_score > 0 for a in analyses) else 0.0
        
        # Calculate overall quality score
        total_positive = sum(positive_signals.values())
        total_negative = sum(negative_signals.values())
        quality_score = min(max((total_positive - total_negative * 1.5) / len(analyses), 0), 10) / 10
        
        # Identify top indicators and concerns
        top_indicators = sorted(positive_signals.items(), key=lambda x: x[1], reverse=True)[:3]
        top_concerns = sorted(negative_signals.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'total_commits_analyzed': len(analyses),
            'quality_score': quality_score,
            'positive_signals': positive_signals,
            'negative_signals': negative_signals,
            'avg_complexity_score': avg_complexity,
            'avg_api_design_score': avg_api_design,
            'top_quality_indicators': [f"{cat}: {count}" for cat, count in top_indicators],
            'top_concerns': [f"{cat}: {count}" for cat, count in top_concerns]
        }


def get_golden_nuggets_from_commits(analyses: List[CommitAnalysis]) -> List[Dict[str, str]]:
    """
    Extract specific examples ("golden nuggets") for interview preparation.
    
    Args:
        analyses: List of CommitAnalysis objects
        
    Returns:
        List of golden nuggets with commit references and descriptions
    """
    nuggets = []
    
    for analysis in analyses:
        # Look for particularly interesting commits
        if analysis.quality_signals:
            # High-quality commit with multiple positive signals
            positive_signals = [s for s in analysis.quality_signals if s.signal_type == 'positive']
            if len(positive_signals) >= 2:
                nuggets.append({
                    'type': 'quality_improvement',
                    'commit_sha': analysis.commit_sha,
                    'description': f"Demonstrated code quality focus by {analysis.commit_message[:100]}",
                    'evidence': f"Added {len(positive_signals)} quality improvements including {', '.join(set(s.category for s in positive_signals[:3]))}",
                    'question_suggestion': f"Can you walk me through the thought process behind commit {analysis.commit_sha[:8]}?"
                })
        
        # API design improvements
        if analysis.api_design_score > 0.7:
            nuggets.append({
                'type': 'api_design',
                'commit_sha': analysis.commit_sha,
                'description': f"Showed strong API design sense in: {analysis.commit_message[:100]}",
                'evidence': f"API design score: {analysis.api_design_score:.2f}/1.0",
                'question_suggestion': f"Tell me about your API design philosophy, particularly in commit {analysis.commit_sha[:8]}"
            })
        
        # Complex problem solving
        if analysis.complexity_score > 0.7 and analysis.additions > 100:
            nuggets.append({
                'type': 'complex_problem_solving',
                'commit_sha': analysis.commit_sha,
                'description': f"Tackled complex problem: {analysis.commit_message[:100]}",
                'evidence': f"Modified {analysis.files_changed} files, {analysis.additions} additions",
                'question_suggestion': f"What was the most challenging part of implementing {analysis.commit_sha[:8]}?"
            })
    
    # Sort by relevance and return top 5
    return sorted(nuggets, key=lambda x: len(x['evidence']), reverse=True)[:5]
