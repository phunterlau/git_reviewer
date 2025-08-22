"""
Initiative and Ownership Analyzer

Implements Category 3 analysis: Initiative, Curiosity & Product Sense
Analyzes self-directed work cycles, first responder behavior, and ownership indicators.
"""

import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from ..models.metrics import InitiativeOwnershipMetrics, ActivityData


class InitiativeOwnershipAnalyzer:
    """Analyzer for Category 3: Initiative, Curiosity & Product Sense."""
    
    def __init__(self):
        """Initialize analyzer with ownership detection patterns."""
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize patterns for detecting ownership and initiative."""
        
        # Ownership-indicating keywords in commits/issues
        self.ownership_keywords = [
            'implement', 'create', 'build', 'develop', 'design',
            'architect', 'refactor', 'optimize', 'improve',
            'introduce', 'add', 'enhance', 'extend'
        ]
        
        # Problem identification keywords
        self.problem_keywords = [
            'fix', 'bug', 'issue', 'problem', 'error', 'broken',
            'performance', 'slow', 'memory', 'leak', 'crash'
        ]
        
        # Innovation/learning keywords
        self.innovation_keywords = [
            'experiment', 'try', 'explore', 'research', 'investigate',
            'prototype', 'poc', 'proof of concept', 'spike',
            'new', 'novel', 'alternative', 'better'
        ]
        
        # Personal project indicators
        self.personal_project_indicators = [
            'learning', 'practice', 'tutorial', 'example',
            'demo', 'sample', 'test', 'experiment',
            'my', 'personal', 'side', 'hobby'
        ]
    
    def analyze_self_directed_work_cycles(self, issues: List[Dict], pull_requests: List[Dict], commits: List[Dict]) -> Tuple[int, List[str]]:
        """
        Identify self-directed work cycles where user creates issue and resolves it.
        
        Args:
            issues: List of issue data
            pull_requests: List of PR data  
            commits: List of commit data
            
        Returns:
            Tuple of (cycle_count, ownership_indicators)
        """
        cycles = 0
        ownership_indicators = []
        
        # Extract issue numbers from user's issues
        user_issues = set()
        for issue in issues:
            user_issues.add(issue.get('number'))
        
        # Look for commits/PRs that reference these issues
        issue_linking_patterns = [
            r'closes?\s+#(\d+)',
            r'fixes?\s+#(\d+)', 
            r'resolves?\s+#(\d+)',
            r'implements?\s+#(\d+)'
        ]
        
        resolved_issues = set()
        
        # Check commits for issue resolution
        for commit in commits:
            message = commit.get('message', '')
            
            for pattern in issue_linking_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                for match in matches:
                    issue_num = int(match)
                    if issue_num in user_issues:
                        resolved_issues.add(issue_num)
        
        # Check PRs for issue resolution
        for pr in pull_requests:
            body = pr.get('body', '') + ' ' + pr.get('title', '')
            
            for pattern in issue_linking_patterns:
                matches = re.findall(pattern, body, re.IGNORECASE)
                for match in matches:
                    issue_num = int(match)
                    if issue_num in user_issues:
                        resolved_issues.add(issue_num)
        
        cycles = len(resolved_issues)
        
        # Generate ownership indicators
        if cycles > 0:
            ownership_indicators.append(f"Self-directed cycles: Created and resolved {cycles} issues")
        
        # Additional ownership signals from commit messages
        ownership_commits = 0
        for commit in commits:
            message = commit.get('message', '').lower()
            if any(keyword in message for keyword in self.ownership_keywords):
                ownership_commits += 1
        
        if ownership_commits > len(commits) * 0.3:  # More than 30% of commits show ownership
            ownership_indicators.append(f"High ownership language: {ownership_commits}/{len(commits)} commits")
        
        return cycles, ownership_indicators
    
    def analyze_first_responder_behavior(self, comments: List[Dict], activity_data: ActivityData) -> int:
        """
        Analyze first responder behavior on issues/PRs the user didn't create.
        
        Args:
            comments: List of comment data
            activity_data: Full activity data for context
            
        Returns:
            Number of first responder instances
        """
        # This is a simplified analysis since we need issue/PR creation timestamps
        # In a full implementation, we would need to fetch issue details for timing
        
        first_responder_count = 0
        
        # Look for comment patterns that indicate helpful first responses
        helpful_patterns = [
            r'i can help',
            r'let me',
            r'i\'ll take',
            r'working on',
            r'investigating',
            r'reproduced',
            r'confirmed',
            r'looks like',
            r'the issue is',
            r'try this'
        ]
        
        for comment in comments:
            comment_body = comment.get('comment_body', '').lower()
            
            if any(re.search(pattern, comment_body) for pattern in helpful_patterns):
                first_responder_count += 1
        
        return first_responder_count
    
    def analyze_personal_project_quality(self, activity_data: ActivityData) -> Tuple[float, List[str]]:
        """
        Analyze quality and innovation of personal projects.
        
        Args:
            activity_data: Full activity data
            
        Returns:
            Tuple of (quality_score, learning_indicators)
        """
        repo_analysis = defaultdict(lambda: {'commits': 0, 'innovation': 0, 'quality': 0})
        learning_indicators = []
        
        # Analyze repository involvement
        for repo, activity_count in activity_data.repository_involvement.items():
            # Skip very low activity repos
            if activity_count < 3:
                continue
            
            repo_analysis[repo]['commits'] = activity_count
            
            # Look for innovation signals in commits related to this repo
            for commit in activity_data.commits:
                if commit.get('repository') == repo:
                    message = commit.get('message', '').lower()
                    
                    # Innovation indicators
                    if any(keyword in message for keyword in self.innovation_keywords):
                        repo_analysis[repo]['innovation'] += 1
                    
                    # Quality indicators (documentation, tests, structure)
                    if any(keyword in message for keyword in ['doc', 'test', 'readme', 'ci']):
                        repo_analysis[repo]['quality'] += 1
        
        # Calculate overall quality score
        if not repo_analysis:
            return 0.0, learning_indicators
        
        quality_scores = []
        for repo, metrics in repo_analysis.items():
            if metrics['commits'] > 0:
                innovation_ratio = metrics['innovation'] / metrics['commits']
                quality_ratio = metrics['quality'] / metrics['commits']
                repo_score = (innovation_ratio + quality_ratio) / 2
                quality_scores.append(repo_score)
                
                if innovation_ratio > 0.2:
                    learning_indicators.append(f"Experimental work in {repo}")
                if quality_ratio > 0.3:
                    learning_indicators.append(f"Quality focus in {repo}")
        
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return overall_quality, learning_indicators
    
    def analyze_open_source_contributions(self, activity_data: ActivityData) -> Tuple[int, List[str]]:
        """
        Analyze contributions to open source projects.
        
        Args:
            activity_data: Full activity data
            
        Returns:
            Tuple of (contribution_count, contribution_evidence)
        """
        contribution_count = 0
        contribution_evidence = []
        
        # Well-known open source organizations/repos
        known_oss_orgs = {
            'pytorch', 'tensorflow', 'huggingface', 'microsoft', 'google',
            'facebook', 'apache', 'numpy', 'pandas', 'scikit-learn',
            'kubernetes', 'docker', 'rust-lang', 'python', 'golang'
        }
        
        # Analyze repository involvement for OSS contributions
        for repo in activity_data.repository_involvement.keys():
            repo_lower = repo.lower()
            org = repo.split('/')[0].lower() if '/' in repo else repo.lower()
            
            # Check if it's a known OSS project
            if org in known_oss_orgs:
                contribution_count += 1
                contribution_evidence.append(f"Contributed to {repo}")
            
            # Check for typical OSS repo patterns
            elif any(keyword in repo_lower for keyword in ['awesome', 'tutorial', 'example', 'docs']):
                contribution_count += 1
                contribution_evidence.append(f"Community contribution: {repo}")
        
        # Analyze PRs for external contributions
        external_prs = 0
        for pr in activity_data.pull_requests:
            repo = pr.get('repository', '')
            if repo and any(org in repo.lower() for org in known_oss_orgs):
                external_prs += 1
        
        if external_prs > 0:
            contribution_evidence.append(f"{external_prs} PRs to major OSS projects")
        
        return contribution_count, contribution_evidence
    
    def analyze_problem_identification_score(self, issues: List[Dict], commits: List[Dict]) -> float:
        """
        Analyze ability to identify and articulate problems.
        
        Args:
            issues: List of issue data
            commits: List of commit data
            
        Returns:
            Problem identification score (0-1)
        """
        problem_identification_signals = 0
        total_signals = 0
        
        # Analyze issue creation for problem identification
        for issue in issues:
            total_signals += 1
            title = issue.get('title', '').lower()
            body = issue.get('body', '').lower()
            
            # Look for clear problem statements
            if any(keyword in title + ' ' + body for keyword in self.problem_keywords):
                problem_identification_signals += 1
            
            # Look for detailed problem descriptions
            if len(body) > 100:  # Detailed description
                problem_identification_signals += 0.5
        
        # Analyze commits for problem-solving patterns
        for commit in commits:
            total_signals += 1
            message = commit.get('message', '').lower()
            
            if any(keyword in message for keyword in self.problem_keywords):
                problem_identification_signals += 1
        
        if total_signals == 0:
            return 0.0
        
        return min(problem_identification_signals / total_signals, 1.0)
    
    def analyze_solution_creativity(self, commits: List[Dict], pull_requests: List[Dict]) -> List[str]:
        """
        Analyze creativity and innovation in solutions.
        
        Args:
            commits: List of commit data
            pull_requests: List of PR data
            
        Returns:
            List of creativity indicators
        """
        creativity_indicators = []
        
        # Look for innovative approaches in commit messages
        innovation_count = 0
        for commit in commits:
            message = commit.get('message', '').lower()
            
            if any(keyword in message for keyword in self.innovation_keywords):
                innovation_count += 1
        
        if innovation_count > len(commits) * 0.15:  # More than 15% show innovation
            creativity_indicators.append(f"Experimental approach: {innovation_count} innovative commits")
        
        # Analyze PR descriptions for creative solutions
        creative_prs = 0
        for pr in pull_requests:
            body = pr.get('body', '').lower()
            
            if any(keyword in body for keyword in self.innovation_keywords):
                creative_prs += 1
            
            # Look for alternative solution discussions
            if any(phrase in body for phrase in ['alternative', 'different approach', 'better way']):
                creative_prs += 1
        
        if creative_prs > 0:
            creativity_indicators.append(f"Creative problem solving in {creative_prs} PRs")
        
        return creativity_indicators
    
    def analyze(self, activity_data: ActivityData) -> InitiativeOwnershipMetrics:
        """
        Perform comprehensive initiative and ownership analysis.
        
        Args:
            activity_data: Raw GitHub activity data
            
        Returns:
            InitiativeOwnershipMetrics with analysis results
        """
        print("🚀 Analyzing Initiative & Ownership...")
        
        commits = activity_data.commits
        issues = activity_data.issues
        pull_requests = activity_data.pull_requests
        comments = activity_data.comments
        
        # Perform all analyses
        self_directed_cycles, ownership_indicators = self.analyze_self_directed_work_cycles(
            issues, pull_requests, commits
        )
        
        first_responder_instances = self.analyze_first_responder_behavior(comments, activity_data)
        
        personal_project_quality, learning_indicators = self.analyze_personal_project_quality(activity_data)
        
        open_source_contributions, contribution_evidence = self.analyze_open_source_contributions(activity_data)
        
        problem_identification_score = self.analyze_problem_identification_score(issues, commits)
        
        solution_creativity_indicators = self.analyze_solution_creativity(commits, pull_requests)
        
        # Combine all ownership indicators
        all_ownership_indicators = ownership_indicators + learning_indicators + contribution_evidence
        
        # Create metrics object
        metrics = InitiativeOwnershipMetrics(
            self_directed_work_cycles=self_directed_cycles,
            first_responder_instances=first_responder_instances,
            personal_project_quality=personal_project_quality,
            open_source_contributions=open_source_contributions,
            ownership_indicators=all_ownership_indicators,
            problem_identification_score=problem_identification_score,
            solution_creativity_indicators=solution_creativity_indicators,
            learning_trajectory_indicators=learning_indicators
        )
        
        print(f"✅ Initiative Analysis Complete:")
        print(f"  - Self-Directed Cycles: {self_directed_cycles}")
        print(f"  - First Responder: {first_responder_instances}")
        print(f"  - OSS Contributions: {open_source_contributions}")
        print(f"  - Personal Project Quality: {personal_project_quality:.2f}")
        
        return metrics
