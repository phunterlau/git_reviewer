"""
Engineering Craftsmanship Analyzer

Implements Category 2 analysis: Problem-Solving & Engineering Craftsmanship
Analyzes workflow discipline, PR quality, testing habits, and structured development.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from collections import defaultdict

from ..models.metrics import EngineeringCraftsmanshipMetrics, ActivityData


class EngineeringCraftsmanshipAnalyzer:
    """Analyzer for Category 2: Problem-Solving & Engineering Craftsmanship."""
    
    def __init__(self):
        """Initialize analyzer with pattern definitions."""
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize detection patterns for craftsmanship analysis."""
        
        # Commit-issue linking patterns
        self.issue_linking_patterns = [
            r'closes?\s+#(\d+)',
            r'fixes?\s+#(\d+)', 
            r'resolves?\s+#(\d+)',
            r'addresses?\s+#(\d+)',
            r'implements?\s+#(\d+)',
            r'refs?\s+#(\d+)',
            r'see\s+#(\d+)',
            r'related\s+to\s+#(\d+)'
        ]
        
        # Testing file patterns
        self.test_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests?/.*\.py$',
            r'spec/.*\.py$',
            r'.*\.test\.(js|ts)$',
            r'.*\.spec\.(js|ts)$',
            r'__tests__/.*\.(js|ts)$'
        ]
        
        # Documentation patterns
        self.doc_patterns = [
            r'readme.*\.md$',
            r'docs?/.*\.md$',
            r'.*\.rst$',
            r'changelog.*',
            r'contributing.*',
            r'license.*'
        ]
        
        # Code quality indicators
        self.quality_indicators = {
            'type_hints': [r':\s*\w+\s*=', r'->\s*\w+:', r'typing\.', r'from typing'],
            'docstrings': [r'""".*?"""', r"'''.*?'''"],
            'error_handling': [r'try:', r'except', r'raise', r'finally:'],
            'validation': [r'assert\s+', r'validate', r'check', r'verify'],
            'logging': [r'log\.|logger\.', r'logging\.']
        }
    
    def analyze_commit_issue_linking(self, commits: List[Dict]) -> float:
        """
        Analyze the ratio of commits that reference issues.
        
        Args:
            commits: List of commit data
            
        Returns:
            Ratio of commits that link to issues (0-1)
        """
        if not commits:
            return 0.0
        
        linked_commits = 0
        
        for commit in commits:
            message = commit.get('message', '')
            
            # Check for issue linking patterns
            for pattern in self.issue_linking_patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    linked_commits += 1
                    break  # Count each commit only once
        
        return linked_commits / len(commits)
    
    def analyze_pr_turnaround_times(self, pull_requests: List[Dict]) -> Dict[str, float]:
        """
        Analyze PR turnaround times by size category.
        
        Args:
            pull_requests: List of PR data
            
        Returns:
            Dict mapping size category to average turnaround hours
        """
        size_categories = {'S': [], 'M': [], 'L': []}
        
        for pr in pull_requests:
            if pr.get('merged_at') and pr.get('created_at'):
                # Calculate turnaround time
                created = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00'))
                merged = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                turnaround_hours = (merged - created).total_seconds() / 3600
                
                # Categorize by size (using file changes and additions)
                changed_files = pr.get('changed_files', 0)
                additions = pr.get('additions', 0)
                
                # Size heuristics
                if changed_files <= 3 and additions <= 100:
                    size_categories['S'].append(turnaround_hours)
                elif changed_files <= 10 and additions <= 500:
                    size_categories['M'].append(turnaround_hours)
                else:
                    size_categories['L'].append(turnaround_hours)
        
        # Calculate averages
        avg_turnarounds = {}
        for size, times in size_categories.items():
            if times:
                avg_turnarounds[size] = sum(times) / len(times)
            else:
                avg_turnarounds[size] = 0.0
        
        return avg_turnarounds
    
    def analyze_testing_commitment(self, commits: List[Dict]) -> float:
        """
        Analyze commitment to testing by examining test file changes.
        
        Args:
            commits: List of commit data
            
        Returns:
            Testing commitment ratio (0-1)
        """
        if not commits:
            return 0.0
        
        commits_with_tests = 0
        total_commits_with_files = 0
        
        for commit in commits:
            if 'files' in commit and commit['files']:
                total_commits_with_files += 1
                
                # Check if any files are test files
                for file_info in commit['files']:
                    filename = file_info['filename']
                    
                    for pattern in self.test_patterns:
                        if re.match(pattern, filename, re.IGNORECASE):
                            commits_with_tests += 1
                            break  # Count each commit only once
                    else:
                        continue
                    break
        
        if total_commits_with_files == 0:
            return 0.0
        
        return commits_with_tests / total_commits_with_files
    
    def analyze_structured_workflow(self, commits: List[Dict], pull_requests: List[Dict]) -> float:
        """
        Analyze overall structured workflow adherence.
        
        Args:
            commits: List of commit data
            pull_requests: List of PR data
            
        Returns:
            Structured workflow score (0-1)
        """
        workflow_indicators = []
        
        # 1. Commit message quality
        if commits:
            quality_messages = 0
            for commit in commits:
                message = commit.get('message', '')
                # Good commit messages are descriptive and follow conventions
                if (len(message) > 20 and 
                    not message.lower().startswith(('fix', 'update', 'change')) and
                    any(char in message for char in [':','(','['])):
                    quality_messages += 1
            
            workflow_indicators.append(quality_messages / len(commits))
        
        # 2. PR description quality
        if pull_requests:
            quality_prs = 0
            for pr in pull_requests:
                body = pr.get('body', '')
                title = pr.get('title', '')
                # Good PRs have descriptions and meaningful titles
                if len(body) > 50 and len(title) > 10:
                    quality_prs += 1
            
            workflow_indicators.append(quality_prs / len(pull_requests))
        
        # 3. Branching discipline (inferred from PR patterns)
        if pull_requests:
            feature_branch_prs = 0
            for pr in pull_requests:
                title = pr.get('title', '').lower()
                # Look for feature branch indicators
                if any(keyword in title for keyword in ['feat', 'feature', 'add', 'implement']):
                    feature_branch_prs += 1
            
            workflow_indicators.append(min(feature_branch_prs / len(pull_requests), 1.0))
        
        # Return average of all indicators
        if workflow_indicators:
            return sum(workflow_indicators) / len(workflow_indicators)
        else:
            return 0.0
    
    def analyze_code_review_thoroughness(self, reviews: List[Dict]) -> float:
        """
        Analyze thoroughness of code reviews given by the user.
        
        Args:
            reviews: List of review data
            
        Returns:
            Review thoroughness score (0-1)
        """
        if not reviews:
            return 0.0
        
        thoroughness_scores = []
        
        for review in reviews:
            body = review.get('body', '')
            state = review.get('state', '')
            
            score = 0.0
            
            # Score based on review content length and type
            if state == 'APPROVED':
                score += 0.3
            elif state == 'CHANGES_REQUESTED':
                score += 0.5  # Higher score for detailed feedback
            elif state == 'COMMENTED':
                score += 0.4
            
            # Score based on comment length (proxy for thoroughness)
            if len(body) > 100:
                score += 0.3
            elif len(body) > 50:
                score += 0.2
            elif len(body) > 20:
                score += 0.1
            
            # Score based on specificity indicators
            if any(word in body.lower() for word in ['line', 'function', 'method', 'variable']):
                score += 0.2
            
            if any(word in body.lower() for word in ['suggest', 'consider', 'maybe', 'could']):
                score += 0.2
            
            thoroughness_scores.append(min(score, 1.0))
        
        return sum(thoroughness_scores) / len(thoroughness_scores)
    
    def analyze_documentation_quality(self, commits: List[Dict]) -> float:
        """
        Analyze documentation quality and maintenance.
        
        Args:
            commits: List of commit data
            
        Returns:
            Documentation quality score (0-1)
        """
        if not commits:
            return 0.0
        
        doc_commits = 0
        total_commits_with_files = 0
        
        for commit in commits:
            if 'files' in commit and commit['files']:
                total_commits_with_files += 1
                
                # Check for documentation files
                for file_info in commit['files']:
                    filename = file_info['filename'].lower()
                    
                    for pattern in self.doc_patterns:
                        if re.match(pattern, filename, re.IGNORECASE):
                            doc_commits += 1
                            break
                    else:
                        continue
                    break
        
        if total_commits_with_files == 0:
            return 0.0
        
        return doc_commits / total_commits_with_files
    
    def analyze_error_handling_patterns(self, commits: List[Dict]) -> List[str]:
        """
        Analyze error handling and defensive programming patterns.
        
        Args:
            commits: List of commit data
            
        Returns:
            List of error handling patterns found
        """
        patterns_found = set()
        
        for commit in commits:
            if 'files' in commit:
                for file_info in commit['files']:
                    if 'patch' in file_info:
                        patch_content = file_info['patch']
                        
                        # Look for error handling patterns
                        for category, indicators in self.quality_indicators.items():
                            for indicator in indicators:
                                if re.search(indicator, patch_content, re.IGNORECASE):
                                    patterns_found.add(category)
        
        return list(patterns_found)
    
    def analyze(self, activity_data: ActivityData) -> EngineeringCraftsmanshipMetrics:
        """
        Perform comprehensive engineering craftsmanship analysis.
        
        Args:
            activity_data: Raw GitHub activity data
            
        Returns:
            EngineeringCraftsmanshipMetrics with analysis results
        """
        print("🛠️ Analyzing Engineering Craftsmanship...")
        
        commits = activity_data.commits
        pull_requests = activity_data.pull_requests
        reviews = activity_data.reviews
        
        # Perform all analyses
        commit_issue_linking_ratio = self.analyze_commit_issue_linking(commits)
        pr_turnaround_times = self.analyze_pr_turnaround_times(pull_requests)
        testing_commitment_ratio = self.analyze_testing_commitment(commits)
        structured_workflow_score = self.analyze_structured_workflow(commits, pull_requests)
        code_review_thoroughness = self.analyze_code_review_thoroughness(reviews)
        documentation_quality_score = self.analyze_documentation_quality(commits)
        error_handling_patterns = self.analyze_error_handling_patterns(commits)
        
        # Create metrics object
        metrics = EngineeringCraftsmanshipMetrics(
            commit_issue_linking_ratio=commit_issue_linking_ratio,
            pr_turnaround_times=pr_turnaround_times,
            testing_commitment_ratio=testing_commitment_ratio,
            structured_workflow_score=structured_workflow_score,
            code_review_thoroughness=code_review_thoroughness,
            documentation_quality_score=documentation_quality_score,
            error_handling_patterns=error_handling_patterns
        )
        
        print(f"✅ Craftsmanship Analysis Complete:")
        print(f"  - Commit-Issue Linking: {commit_issue_linking_ratio:.2f}")
        print(f"  - Testing Commitment: {testing_commitment_ratio:.2f}")
        print(f"  - Structured Workflow: {structured_workflow_score:.2f}")
        print(f"  - Review Thoroughness: {code_review_thoroughness:.2f}")
        
        return metrics
