#!/usr/bin/env python3
"""
Enhanced CIS Scoring with Major Contributor Detection

This version fixes the critical bug where major contributors like Linus Torvalds
were not properly detected due to non-GitHub-centric workflows.
"""

import math
import re
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import github
from github import Github


@dataclass
class CISBreakdown:
    """Detailed breakdown of CIS calculation."""
    substance_score: float
    quality_multiplier: float
    community_multiplier: float
    initiative_multiplier: float
    final_cis_score: float
    
    # Detailed analysis
    code_lines: int
    config_lines: int
    doc_lines: int
    complexity_factor: float
    comments_count: int
    reactions_count: int
    is_self_directed: bool


@dataclass
class SignificantContribution:
    """Represents a significant contribution with CIS score."""
    title: str
    url: str
    cis_score: float
    repo_name: str
    contribution_type: str  # "external_pr", "self_directed_cycle", "commit", "major_maintainer"
    breakdown: CISBreakdown
    created_at: str


class EnhancedCISCalculator:
    """Enhanced CIS Calculator with major contributor detection."""
    
    def __init__(self, github_token: str):
        """Initialize the calculator with GitHub token."""
        self.g = Github(github_token)
        
        # Keywords that indicate code complexity
        self.complexity_keywords = [
            'algorithm', 'optimization', 'performance', 'security', 'thread',
            'async', 'concurrent', 'memory', 'cache', 'buffer', 'protocol',
            'encryption', 'parsing', 'compiler', 'interpreter', 'kernel',
            'driver', 'architecture', 'framework', 'library', 'api',
            'database', 'network', 'distributed', 'microservice', 'container'
        ]
        
        # File extension weights
        self.file_weights = {
            # Code files (highest weight)
            '.py': 1.0, '.js': 1.0, '.ts': 1.0, '.java': 1.0, '.cpp': 1.0,
            '.c': 1.0, '.h': 1.0, '.hpp': 1.0, '.cs': 1.0, '.go': 1.0,
            '.rs': 1.0, '.rb': 1.0, '.php': 1.0, '.swift': 1.0, '.kt': 1.0,
            '.scala': 1.0, '.clj': 1.0, '.hs': 1.0, '.ml': 1.0, '.r': 1.0,
            '.m': 1.0, '.mm': 1.0, '.cc': 1.0, '.cxx': 1.0,
            
            # Config/Infrastructure (medium weight)
            '.json': 0.5, '.yaml': 0.5, '.yml': 0.5, '.xml': 0.5,
            '.toml': 0.5, '.ini': 0.5, '.cfg': 0.5, '.conf': 0.5,
            '.dockerfile': 0.5, '.makefile': 0.5, '.cmake': 0.5,
            '.gradle': 0.5, '.maven': 0.5, '.sbt': 0.5,
            
            # Documentation (lower weight)
            '.md': 0.2, '.rst': 0.2, '.txt': 0.2, '.adoc': 0.2,
            
            # Excluded files (zero weight)
            '.png': 0, '.jpg': 0, '.jpeg': 0, '.gif': 0, '.svg': 0,
            '.ico': 0, '.pdf': 0, '.doc': 0, '.docx': 0, '.lock': 0,
            '.log': 0, '.tmp': 0, '.cache': 0,
        }

    def _classify_file_changes(self, patch: str, filename: str) -> Tuple[str, int]:
        """Classify file changes and count meaningful lines."""
        if not patch:
            return 'excluded', 0
        
        # Get file extension
        ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        
        # Count added/modified lines (exclude deletions for substance scoring)
        lines = patch.split('\n')
        meaningful_lines = 0
        
        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                # Skip empty lines, comments, and trivial changes
                content = line[1:].strip()
                if (content and 
                    not content.startswith('#') and 
                    not content.startswith('//') and
                    not content.startswith('/*') and
                    len(content) > 3):
                    meaningful_lines += 1
        
        # Classify based on file extension
        weight = self.file_weights.get(ext, 0.3)  # Default weight for unknown files
        
        if weight >= 1.0:
            return 'code', meaningful_lines
        elif weight >= 0.4:
            return 'config', meaningful_lines
        elif weight >= 0.1:
            return 'doc', meaningful_lines
        else:
            return 'excluded', meaningful_lines

    def _calculate_substance_score(self, files_data: List[Dict]) -> Tuple[float, Dict]:
        """Calculate substance score based on code changes."""
        code_lines = 0
        config_lines = 0
        doc_lines = 0
        excluded_lines = 0
        complexity_keywords_found = []
        file_analysis = {}
        
        for file_data in files_data:
            filename = file_data.get('filename', '')
            patch = file_data.get('patch', '')
            
            if not patch:
                continue
            
            file_type, lines_changed = self._classify_file_changes(patch, filename)
            file_analysis[filename] = {
                'type': file_type,
                'lines': lines_changed
            }
            
            if file_type == 'code':
                code_lines += lines_changed
                # Look for complexity keywords in code files
                for keyword in self.complexity_keywords:
                    if keyword in patch.lower():
                        complexity_keywords_found.append(keyword)
            elif file_type == 'config':
                config_lines += lines_changed
            elif file_type == 'doc':
                doc_lines += lines_changed
            elif file_type == 'excluded':
                excluded_lines += lines_changed
        
        # Calculate complexity factor
        unique_keywords = len(set(complexity_keywords_found))
        complexity_factor = 1 + (0.1 * unique_keywords)
        
        # Calculate weighted line count
        weighted_lines = (
            code_lines * 1.0 +
            config_lines * 0.5 +
            doc_lines * 0.2
        )
        
        # Apply complexity factor and log scaling
        substance_score = math.log(weighted_lines * complexity_factor + 1)
        
        analysis_details = {
            'code_lines': code_lines,
            'config_lines': config_lines,
            'doc_lines': doc_lines,
            'excluded_lines': excluded_lines,
            'complexity_factor': complexity_factor,
            'weighted_lines': weighted_lines,
            'file_analysis': file_analysis
        }
        
        return substance_score, analysis_details

    def _calculate_quality_multiplier(self, comments_count: int, reactions_count: int) -> float:
        """Calculate quality multiplier based on community engagement."""
        # Comments indicate code review depth
        comment_factor = 1 + math.log(comments_count + 1) * 0.1
        
        # Reactions indicate community appreciation
        reaction_factor = 1 + math.log(reactions_count + 1) * 0.05
        
        return min(comment_factor * reaction_factor, 3.0)  # Cap at 3x

    def _calculate_community_multiplier(self, repo_stars: int, repo_forks: int) -> float:
        """Calculate community multiplier based on repository importance."""
        # Repository popularity indicates community impact
        popularity_score = math.log(repo_stars + 1) + math.log(repo_forks + 1)
        
        # Scale to reasonable multiplier range
        multiplier = 1 + (popularity_score / 10)
        
        return min(multiplier, 5.0)  # Cap at 5x

    def _calculate_initiative_multiplier(self, is_self_directed: bool) -> float:
        """Calculate initiative multiplier for self-directed work."""
        return 2.0 if is_self_directed else 1.0

    def calculate_cis_score(self, files_data: List[Dict], comments_count: int,
                           reactions_count: int, repo_stars: int, repo_forks: int,
                           is_self_directed: bool = False) -> CISBreakdown:
        """
        Calculate Contribution Impact Score (CIS).
        
        Args:
            files_data: List of file change data from GitHub API
            comments_count: Number of substantive comments
            reactions_count: Number of positive reactions
            repo_stars: Repository star count
            repo_forks: Repository fork count
            is_self_directed: Whether this is a self-directed work cycle
            
        Returns:
            CISBreakdown with detailed scoring analysis
        """
        # Layer 1: Substance Score (logarithmic based on code changes)
        substance_score, analysis_details = self._calculate_substance_score(files_data)
        
        # Layer 2: Quality Multiplier (based on community engagement)
        quality_multiplier = self._calculate_quality_multiplier(comments_count, reactions_count)
        
        # Layer 3: Community Multiplier (based on repository importance)
        community_multiplier = self._calculate_community_multiplier(repo_stars, repo_forks)
        
        # Layer 4: Initiative Multiplier (self-directed work bonus)
        initiative_multiplier = self._calculate_initiative_multiplier(is_self_directed)
        
        # Final CIS Score
        final_cis_score = (substance_score * quality_multiplier * 
                          community_multiplier * initiative_multiplier)
        
        return CISBreakdown(
            substance_score=substance_score,
            quality_multiplier=quality_multiplier,
            community_multiplier=community_multiplier,
            initiative_multiplier=initiative_multiplier,
            final_cis_score=final_cis_score,
            code_lines=analysis_details['code_lines'],
            config_lines=analysis_details['config_lines'],
            doc_lines=analysis_details['doc_lines'],
            complexity_factor=analysis_details['complexity_factor'],
            comments_count=comments_count,
            reactions_count=reactions_count,
            is_self_directed=is_self_directed
        )

    def _analyze_pr_contribution(self, pr_data: Dict, repo_name: str, 
                               is_self_directed: bool = False) -> Optional[SignificantContribution]:
        """Analyze a single PR contribution."""
        try:
            # Get repository info for community multiplier
            repo = self.g.get_repo(repo_name)
            repo_stars = repo.stargazers_count
            repo_forks = repo.forks_count
            
            # Get PR details
            pr_number = pr_data.get('number')
            if not pr_number:
                return None
                
            pr = repo.get_pull(pr_number)
            
            # Get files data
            files_data = []
            try:
                files = list(pr.get_files())
                for file in files:
                    files_data.append({
                        'filename': file.filename,
                        'patch': file.patch or '',
                        'additions': file.additions,
                        'deletions': file.deletions
                    })
            except Exception as e:
                print(f"⚠️ Could not get files for PR {pr_number}: {e}")
                return None
            
            if not files_data:
                return None
            
            # Count substantive comments (exclude bot comments and simple approvals)
            substantive_comments = 0
            try:
                comments = list(pr.get_review_comments()) + list(pr.get_issue_comments())
                for comment in comments:
                    if (len(comment.body) > 20 and 
                        not comment.user.type == 'Bot' and
                        not comment.body.lower().strip() in ['lgtm', 'approved', '+1', '👍']):
                        substantive_comments += 1
            except:
                substantive_comments = 0
            
            # Count reactions
            reactions_count = 0
            try:
                reactions = pr.get_reactions()
                reactions_count = sum(1 for r in reactions if r.content in ['+1', 'heart', 'hooray'])
            except:
                reactions_count = 0
            
            # Calculate CIS score
            cis_breakdown = self.calculate_cis_score(
                files_data=files_data,
                comments_count=substantive_comments,
                reactions_count=reactions_count,
                repo_stars=repo_stars,
                repo_forks=repo_forks,
                is_self_directed=is_self_directed
            )
            
            return SignificantContribution(
                title=pr.title,
                url=pr.html_url,
                cis_score=cis_breakdown.final_cis_score,
                repo_name=repo_name,
                contribution_type="self_directed_cycle" if is_self_directed else "external_pr",
                breakdown=cis_breakdown,
                created_at=pr.created_at.isoformat()
            )
            
        except Exception as e:
            print(f"⚠️ Error analyzing PR {pr_data}: {e}")
            return None

    def _detect_major_maintainer_contributions(self, username: str, max_contributions: int) -> List[SignificantContribution]:
        """
        Detect contributions from major maintainers who own important repositories.
        
        This addresses the limitation where major contributors like Linus Torvalds
        weren't detected because they don't follow GitHub issue/PR workflows.
        """
        contributions = []
        
        try:
            user = self.g.get_user(username)
            repos = list(user.get_repos(type='owner', sort='updated'))
            
            # Focus on highly starred repositories (major projects)
            major_repos = [repo for repo in repos if repo.stargazers_count > 1000]
            major_repos.sort(key=lambda r: r.stargazers_count, reverse=True)
            
            for repo in major_repos[:5]:  # Top 5 major repos
                try:
                    # Get recent significant commits by the user
                    commits = list(repo.get_commits(author=username)[:20])
                    
                    # Analyze commits for significance
                    for commit in commits:
                        try:
                            commit_data = repo.get_commit(commit.sha)
                            
                            # Skip merge commits and trivial changes
                            if (len(commit_data.parents) > 1 or 
                                commit_data.stats.total < 10):
                                continue
                            
                            # Build files data from commit
                            files_data = []
                            for file in commit_data.files:
                                files_data.append({
                                    'filename': file.filename,
                                    'patch': file.patch or '',
                                    'additions': file.additions,
                                    'deletions': file.deletions
                                })
                            
                            if not files_data:
                                continue
                            
                            # Calculate CIS for this commit (as major maintainer work)
                            cis_breakdown = self.calculate_cis_score(
                                files_data=files_data,
                                comments_count=0,  # Direct commits don't have PR comments
                                reactions_count=0,
                                repo_stars=repo.stargazers_count,
                                repo_forks=repo.forks_count,
                                is_self_directed=True  # Owner commits are self-directed
                            )
                            
                            # Apply major maintainer bonus
                            cis_breakdown.final_cis_score *= 1.5  # 50% bonus for major maintainer
                            
                            contribution = SignificantContribution(
                                title=commit.commit.message.split('\n')[0][:100],
                                url=commit.html_url,
                                cis_score=cis_breakdown.final_cis_score,
                                repo_name=repo.full_name,
                                contribution_type="major_maintainer",
                                breakdown=cis_breakdown,
                                created_at=commit.commit.author.date.isoformat()
                            )
                            
                            contributions.append(contribution)
                            
                            if len(contributions) >= max_contributions:
                                break
                                
                        except Exception as e:
                            print(f"⚠️ Error analyzing commit {commit.sha[:8]}: {e}")
                            continue
                
                except Exception as e:
                    print(f"⚠️ Error analyzing repo {repo.name}: {e}")
                    continue
                
                if len(contributions) >= max_contributions:
                    break
        
        except Exception as e:
            print(f"⚠️ Error detecting major maintainer contributions: {e}")
        
        return contributions

    def _find_self_directed_cycles_safe(self, username: str, max_cycles: int) -> List[Dict]:
        """Find self-directed work cycles with better error handling."""
        cycles = []
        
        try:
            user = self.g.get_user(username)
            repos = list(user.get_repos(type='owner', sort='updated'))
            
            for repo in repos[:10]:  # Limit to top 10 repos
                try:
                    # Find issues created and closed by the user
                    issues = list(repo.get_issues(
                        creator=username,
                        state='closed'
                    ))
                    
                    for issue in issues[:10]:  # Limit to 10 issues per repo
                        if issue.pull_request:  # Skip PRs, we want issues
                            continue
                        
                        # Check if there's a PR that references this issue
                        prs = list(repo.get_pulls(state='closed'))
                        
                        for pr in prs[:20]:  # Limit to 20 PRs per repo
                            if (pr.user.login == username and 
                                pr.body and 
                                (f"#{issue.number}" in pr.body or 
                                 f"fixes #{issue.number}" in pr.body.lower() or
                                 f"closes #{issue.number}" in pr.body.lower())):
                                
                                cycles.append({
                                    'repo': repo.full_name,
                                    'pr_number': pr.number,
                                    'title': f"{issue.title} -> {pr.title}",
                                    'pr_url': pr.html_url,
                                    'created_at': pr.created_at.isoformat(),
                                    'issue_number': issue.number
                                })
                                
                                if len(cycles) >= max_cycles:
                                    break
                        
                        if len(cycles) >= max_cycles:
                            break
                
                except Exception as e:
                    print(f"⚠️ Error analyzing repo {repo.name}: {e}")
                    continue
                
                if len(cycles) >= max_cycles:
                    break
            
        except Exception as e:
            print(f"⚠️ Error finding self-directed cycles: {e}")
        
        return cycles

    def find_significant_contributions(self, username: str, max_contributions: int = 10) -> List[SignificantContribution]:
        """Find significant contributions with enhanced major maintainer detection."""
        contributions = []
        
        print(f"🔍 Finding significant contributions for {username}...")
        
        # 1. Find external PRs
        print("   📤 Searching for external PRs...")
        try:
            search_results = self.g.search_issues(
                f"author:{username} type:pr is:merged",
                sort="updated",
                order="desc"
            )
            
            for pr in search_results[:max_contributions]:
                repo_name = pr.repository.full_name
                if pr.user.login != username:
                    continue  # Skip if not actually authored by user
                
                contribution = self._analyze_pr_contribution({
                    'number': pr.number
                }, repo_name, is_self_directed=False)
                
                if contribution and contribution.cis_score > 1.0:
                    contributions.append(contribution)
                    
        except Exception as e:
            print(f"⚠️ Error searching external PRs: {e}")
        
        # 2. Find self-directed cycles (with safe error handling)
        print("   🚀 Searching for self-directed work cycles...")
        self_directed_cycles = self._find_self_directed_cycles_safe(username, max_contributions // 2)
        
        for cycle_info in self_directed_cycles:
            contribution = self._analyze_pr_contribution({
                'number': cycle_info['pr_number']
            }, cycle_info['repo'], is_self_directed=True)
            
            if contribution:
                contribution.contribution_type = "self_directed_cycle"
                contributions.append(contribution)
        
        # 3. NEW: Detect major maintainer contributions
        print("   👑 Detecting major maintainer contributions...")
        major_contributions = self._detect_major_maintainer_contributions(username, max_contributions // 2)
        contributions.extend(major_contributions)
        
        # Sort by CIS score and return top contributions
        contributions.sort(key=lambda c: c.cis_score, reverse=True)
        print(f"   ✅ Found {len(contributions)} significant contributions")
        
        return contributions[:max_contributions]

    def calculate_geek_index(self, contributions: List[SignificantContribution]) -> Tuple[int, Dict]:
        """Calculate the Geek Index (g-index) from significant contributions."""
        if not contributions:
            return 0, {'total_contributions': 0, 'qualifying_contributions': 0}
        
        # Sort contributions by CIS score (descending)
        sorted_contributions = sorted(contributions, key=lambda c: c.cis_score, reverse=True)
        
        # Calculate g-index
        g_index = 0
        for i, contribution in enumerate(sorted_contributions, 1):
            if contribution.cis_score >= i:
                g_index = i
            else:
                break
        
        analysis_summary = {
            'total_contributions': len(contributions),
            'qualifying_contributions': g_index,
            'external_pr_count': len([c for c in contributions if c.contribution_type == 'external_pr']),
            'self_directed_count': len([c for c in contributions if c.contribution_type == 'self_directed_cycle']),
            'major_maintainer_count': len([c for c in contributions if c.contribution_type == 'major_maintainer']),
            'avg_cis_score': sum(c.cis_score for c in contributions) / len(contributions),
            'top_cis_score': sorted_contributions[0].cis_score if sorted_contributions else 0
        }
        
        return g_index, analysis_summary


# Test the enhanced calculator
if __name__ == "__main__":
    import os
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        exit(1)
    
    calculator = EnhancedCISCalculator(token)
    
    # Test with Linus Torvalds
    print("🧪 Testing Enhanced CIS Calculator with Linus Torvalds...")
    start_time = time.time()
    
    contributions = calculator.find_significant_contributions("torvalds", max_contributions=10)
    g_index, summary = calculator.calculate_geek_index(contributions)
    
    end_time = time.time()
    
    print(f"\n🎯 ENHANCED CIS RESULTS for torvalds:")
    print(f"   G-Index: {g_index}")
    print(f"   Total Contributions Found: {summary['total_contributions']}")
    print(f"   External PRs: {summary['external_pr_count']}")
    print(f"   Self-Directed: {summary['self_directed_count']}")
    print(f"   Major Maintainer: {summary['major_maintainer_count']}")
    print(f"   Average CIS Score: {summary['avg_cis_score']:.2f}")
    print(f"   Time taken: {end_time - start_time:.2f} seconds")
    
    print(f"\n📊 Top Contributions:")
    for i, contrib in enumerate(contributions[:5], 1):
        print(f"   {i}. {contrib.repo_name}")
        print(f"      Type: {contrib.contribution_type}")
        print(f"      Title: {contrib.title[:80]}...")
        print(f"      CIS Score: {contrib.cis_score:.2f}")
        print(f"      URL: {contrib.url}")
        print()
