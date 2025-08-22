#!/usr/bin/env python3
"""
Improved Hybrid Founding Engineer Analyzer

This implements the two-phase hybrid approach from the improved_founding_eng.md plan:
1. Heuristic-Based Triage (Fast & Scalable)
2. Targeted Deep Dive (Qualitative & Insightful)

Includes special "Maintainer Mode" for extreme cases like Linus Torvalds.
"""

import os
import re
import time
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timezone
from github import Github
import json


@dataclass
class ContributionCandidate:
    """A potential high-impact contribution identified during triage."""
    repo_name: str
    commit_sha: str
    commit_url: str
    message: str
    additions: int
    deletions: int
    files_changed: int
    created_at: str
    signal_score: float
    signal_reasons: List[str]
    contribution_type: str  # "commit", "pr", "merge_leadership"


@dataclass
class DeepAnalysisResult:
    """Result of deep analysis on a contribution."""
    candidate: ContributionCandidate
    code_quality_score: float
    collaboration_score: float
    impact_score: float
    final_score: float
    code_insights: Dict
    golden_nuggets: List[str]


class ImprovedHybridAnalyzer:
    """
    Hybrid analyzer implementing the two-phase approach from improved_founding_eng.md
    """
    
    def __init__(self, github_token: str):
        self.g = Github(github_token)
        
        # High-signal commit message keywords
        self.high_signal_keywords = [
            'feat', 'feature', 'add', 'implement', 'create',
            'refactor', 'restructure', 'redesign', 'rewrite',
            'perf', 'optimize', 'performance', 'speed', 'efficiency',
            'fix', 'bug', 'issue', 'resolve', 'patch',
            'security', 'vulnerability', 'exploit', 'auth',
            'algorithm', 'cache', 'memory', 'concurrent', 'async',
            'api', 'endpoint', 'service', 'architecture'
        ]
        
        # Code quality indicators to look for in patches
        self.quality_indicators = [
            'test', 'spec', 'unittest', 'pytest', 'jest',
            'docstring', 'documentation', 'comment', 'readme',
            'error handling', 'exception', 'try', 'catch',
            'validation', 'sanitize', 'validate', 'check',
            'logging', 'debug', 'trace', 'monitor'
        ]
        
        # File extensions that indicate substantial code work
        self.code_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
        }

    def analyze_contributor(self, username: str, max_contributions: int = 20) -> Dict:
        """
        Main analysis function implementing the two-phase hybrid approach.
        """
        print(f"🔍 IMPROVED HYBRID ANALYSIS for {username}")
        print("=" * 60)
        
        start_time = time.time()
        
        # Phase 1: Heuristic-Based Triage
        print("📊 PHASE 1: Heuristic-Based Triage")
        print("-" * 40)
        
        triage_results = self._phase1_triage(username, max_contributions * 3)  # Get more candidates for filtering
        
        # Check for maintainer mode
        maintainer_mode = self._detect_maintainer_mode(triage_results)
        
        if maintainer_mode:
            print("👑 MAINTAINER MODE DETECTED - Analyzing leadership contributions")
            return self._analyze_maintainer_contributions(username, triage_results)
        
        # Phase 2: Targeted Deep Dive
        print(f"\n📊 PHASE 2: Targeted Deep Dive")
        print("-" * 40)
        
        deep_results = self._phase2_deep_dive(triage_results[:max_contributions])
        
        # Calculate final scores and generate report
        final_analysis = self._generate_final_analysis(username, deep_results, triage_results)
        
        end_time = time.time()
        final_analysis['analysis_time'] = end_time - start_time
        
        return final_analysis

    def _phase1_triage(self, username: str, max_candidates: int) -> List[ContributionCandidate]:
        """
        Phase 1: Fast triage to identify high-potential contributions using metadata only.
        """
        candidates = []
        
        try:
            # 1. Search for high-signal commits using keywords
            print("   🔎 Searching for high-signal commits...")
            for keyword in self.high_signal_keywords[:10]:  # Limit to avoid rate limits
                try:
                    search_query = f"author:{username} {keyword}"
                    results = self.g.search_commits(search_query, sort="author-date", order="desc")
                    
                    for commit in list(results)[:5]:  # Top 5 per keyword
                        if len(candidates) >= max_candidates:
                            break
                        
                        candidate = self._analyze_commit_metadata(commit, [f"keyword:{keyword}"])
                        if candidate and not any(c.commit_sha == candidate.commit_sha for c in candidates):
                            candidates.append(candidate)
                            
                except Exception as e:
                    print(f"     ⚠️ Error searching for '{keyword}': {e}")
                    continue
                
                if len(candidates) >= max_candidates:
                    break
            
            # 2. Get user's recent activity for impact heuristics
            print("   📈 Analyzing recent activity for impact heuristics...")
            try:
                user = self.g.get_user(username)
                repos = list(user.get_repos(type='owner', sort='updated')[:10])
                
                for repo in repos:
                    try:
                        commits = list(repo.get_commits(author=username)[:10])
                        for commit in commits:
                            if len(candidates) >= max_candidates:
                                break
                            
                            # Check if already processed
                            if any(c.commit_sha == commit.sha for c in candidates):
                                continue
                            
                            candidate = self._analyze_commit_metadata(commit, ["recent_activity"])
                            if candidate and candidate.signal_score > 2.0:  # Only high-signal commits
                                candidates.append(candidate)
                    
                    except Exception as e:
                        print(f"     ⚠️ Error analyzing repo {repo.name}: {e}")
                        continue
                        
            except Exception as e:
                print(f"   ⚠️ Error getting user repos: {e}")
            
            # 3. Search for external contributions (PRs)
            print("   🤝 Searching for external contributions...")
            try:
                pr_results = self.g.search_issues(
                    f"author:{username} type:pr is:merged",
                    sort="updated",
                    order="desc"
                )
                
                for pr in list(pr_results)[:15]:
                    if len(candidates) >= max_candidates:
                        break
                    
                    candidate = self._analyze_pr_metadata(pr, ["external_pr"])
                    if candidate and not any(c.commit_url == candidate.commit_url for c in candidates):
                        candidates.append(candidate)
                        
            except Exception as e:
                print(f"   ⚠️ Error searching external PRs: {e}")
        
        except Exception as e:
            print(f"⚠️ Error in triage phase: {e}")
        
        # Sort by signal score and return top candidates
        candidates.sort(key=lambda c: c.signal_score, reverse=True)
        
        print(f"   ✅ Found {len(candidates)} candidate contributions")
        if candidates:
            print(f"   📊 Top signal score: {candidates[0].signal_score:.2f}")
            print(f"   📊 Average signal score: {sum(c.signal_score for c in candidates) / len(candidates):.2f}")
        
        return candidates

    def _analyze_commit_metadata(self, commit, signal_reasons: List[str]) -> Optional[ContributionCandidate]:
        """
        Analyze commit metadata to calculate signal score without fetching full diff.
        """
        try:
            # Get basic stats
            stats = commit.stats if hasattr(commit, 'stats') else None
            if not stats:
                return None
            
            additions = stats.additions
            deletions = stats.deletions
            total_changes = additions + deletions
            
            # Skip trivial changes
            if total_changes < 5:
                return None
            
            # Skip massive changes (likely auto-generated)
            if total_changes > 10000:
                return None
            
            # Calculate signal score based on metadata
            signal_score = 1.0
            reasons = signal_reasons.copy()
            
            # Message analysis
            message = commit.commit.message.lower()
            keyword_matches = sum(1 for keyword in self.high_signal_keywords if keyword in message)
            if keyword_matches > 0:
                signal_score += keyword_matches * 0.5
                reasons.append(f"keywords:{keyword_matches}")
            
            # Size heuristics (sweet spot for meaningful changes)
            if 20 <= total_changes <= 500:
                signal_score += 1.0
                reasons.append("good_size")
            elif 500 < total_changes <= 2000:
                signal_score += 0.5
                reasons.append("substantial_size")
            
            # Files changed heuristic - safely get count
            try:
                files_changed = len(list(commit.files)) if hasattr(commit, 'files') else 1
            except:
                files_changed = 1
            
            if 2 <= files_changed <= 10:
                signal_score += 0.5
                reasons.append("multi_file")
            
            return ContributionCandidate(
                repo_name=commit.repository.full_name if hasattr(commit, 'repository') else "unknown",
                commit_sha=commit.sha,
                commit_url=commit.html_url,
                message=commit.commit.message.split('\n')[0][:100],
                additions=additions,
                deletions=deletions,
                files_changed=files_changed,
                created_at=commit.commit.author.date.isoformat(),
                signal_score=signal_score,
                signal_reasons=reasons,
                contribution_type="commit"
            )
            
        except Exception as e:
            print(f"     ⚠️ Error analyzing commit metadata: {e}")
            return None

    def _analyze_pr_metadata(self, pr, signal_reasons: List[str]) -> Optional[ContributionCandidate]:
        """
        Analyze PR metadata to calculate signal score.
        """
        try:
            signal_score = 2.0  # PRs start with higher base score
            reasons = signal_reasons.copy()
            
            # Repository popularity bonus
            repo = pr.repository
            stars = repo.stargazers_count
            if stars > 1000:
                signal_score += math.log(stars) / 10
                reasons.append(f"popular_repo:{stars}")
            
            # Comments indicate discussion/complexity
            if pr.comments > 0:
                signal_score += min(pr.comments * 0.1, 1.0)
                reasons.append(f"discussion:{pr.comments}")
            
            return ContributionCandidate(
                repo_name=repo.full_name,
                commit_sha="",
                commit_url=pr.html_url,
                message=pr.title[:100],
                additions=0,  # Will be filled in deep dive
                deletions=0,
                files_changed=0,
                created_at=pr.created_at.isoformat(),
                signal_score=signal_score,
                signal_reasons=reasons,
                contribution_type="pr"
            )
            
        except Exception as e:
            print(f"     ⚠️ Error analyzing PR metadata: {e}")
            return None

    def _detect_maintainer_mode(self, candidates: List[ContributionCandidate]) -> bool:
        """
        Detect if this user is primarily a maintainer (lots of merge commits).
        """
        if not candidates:
            return False
        
        merge_indicators = 0
        total_candidates = len(candidates)
        
        for candidate in candidates:
            message = candidate.message.lower()
            if any(indicator in message for indicator in ['merge', 'pull request', 'pr #']):
                merge_indicators += 1
        
        merge_ratio = merge_indicators / total_candidates if total_candidates > 0 else 0
        
        # If >70% of activity is merges, activate maintainer mode
        is_maintainer = merge_ratio > 0.7
        
        print(f"   🔍 Merge activity: {merge_indicators}/{total_candidates} ({merge_ratio:.1%})")
        print(f"   👑 Maintainer mode: {'ACTIVATED' if is_maintainer else 'Standard analysis'}")
        
        return is_maintainer

    def _analyze_maintainer_contributions(self, username: str, candidates: List[ContributionCandidate]) -> Dict:
        """
        Special analysis mode for maintainers who primarily merge others' work.
        """
        print("   🔍 Analyzing maintainer leadership patterns...")
        
        try:
            user = self.g.get_user(username)
            repos = list(user.get_repos(type='owner', sort='stars', direction='desc')[:5])
            
            maintainer_analysis = {
                'analysis_type': 'maintainer_leadership',
                'major_projects': [],
                'leadership_score': 0,
                'stewardship_indicators': [],
                'repository_impact': {},
                'total_stars_managed': 0
            }
            
            for repo in repos:
                try:
                    project_data = {
                        'name': repo.full_name,
                        'stars': repo.stargazers_count,
                        'forks': repo.forks_count,
                        'language': repo.language,
                        'description': repo.description
                    }
                    
                    # Calculate leadership score based on project impact
                    if repo.stargazers_count > 1000:
                        leadership_points = math.log(repo.stargazers_count) * 2
                        maintainer_analysis['leadership_score'] += leadership_points
                        maintainer_analysis['stewardship_indicators'].append(
                            f"Maintains {repo.name} ({repo.stargazers_count:,} stars)"
                        )
                    
                    maintainer_analysis['major_projects'].append(project_data)
                    maintainer_analysis['total_stars_managed'] += repo.stargazers_count
                    
                except Exception as e:
                    print(f"     ⚠️ Error analyzing repo {repo.name}: {e}")
                    continue
            
            # Calculate final maintainer g-index based on project impact
            projects_by_stars = sorted(maintainer_analysis['major_projects'], 
                                     key=lambda p: p['stars'], reverse=True)
            
            g_index = 0
            for i, project in enumerate(projects_by_stars, 1):
                # For maintainers, g-index is projects with impact score >= i
                impact_score = math.log(project['stars'] + 1)
                if impact_score >= i:
                    g_index = i
                else:
                    break
            
            maintainer_analysis['g_index'] = g_index
            maintainer_analysis['top_contributions'] = candidates[:10]
            
            print(f"   ✅ Leadership score: {maintainer_analysis['leadership_score']:.2f}")
            print(f"   ✅ Total stars managed: {maintainer_analysis['total_stars_managed']:,}")
            print(f"   ✅ Maintainer G-Index: {g_index}")
            
            return maintainer_analysis
            
        except Exception as e:
            print(f"   ⚠️ Error in maintainer analysis: {e}")
            return {'analysis_type': 'maintainer_leadership', 'error': str(e)}

    def _phase2_deep_dive(self, candidates: List[ContributionCandidate]) -> List[DeepAnalysisResult]:
        """
        Phase 2: Deep analysis of top candidates with full diff analysis.
        """
        results = []
        
        print(f"   🔍 Deep diving into top {len(candidates)} contributions...")
        
        for i, candidate in enumerate(candidates, 1):
            try:
                print(f"   📋 Analyzing {i}/{len(candidates)}: {candidate.repo_name}")
                
                if candidate.contribution_type == "pr":
                    result = self._deep_analyze_pr(candidate)
                else:
                    result = self._deep_analyze_commit(candidate)
                
                if result:
                    results.append(result)
                    print(f"      ✅ Final score: {result.final_score:.2f}")
                
            except Exception as e:
                print(f"      ⚠️ Error in deep analysis: {e}")
                continue
        
        return results

    def _deep_analyze_commit(self, candidate: ContributionCandidate) -> Optional[DeepAnalysisResult]:
        """
        Deep analysis of a commit with full diff analysis.
        """
        try:
            repo = self.g.get_repo(candidate.repo_name)
            commit = repo.get_commit(candidate.commit_sha)
            
            # Analyze code quality from diff
            code_insights = self._analyze_code_quality(commit.files)
            code_quality_score = code_insights['quality_score']
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(repo, commit.stats)
            
            # Generate golden nuggets
            golden_nuggets = self._extract_golden_nuggets(commit, code_insights)
            
            # Final score combines all factors
            final_score = (candidate.signal_score * 0.3 + 
                          code_quality_score * 0.4 + 
                          impact_score * 0.3)
            
            return DeepAnalysisResult(
                candidate=candidate,
                code_quality_score=code_quality_score,
                collaboration_score=0,  # No collaboration for direct commits
                impact_score=impact_score,
                final_score=final_score,
                code_insights=code_insights,
                golden_nuggets=golden_nuggets
            )
            
        except Exception as e:
            print(f"      ⚠️ Error analyzing commit: {e}")
            return None

    def _deep_analyze_pr(self, candidate: ContributionCandidate) -> Optional[DeepAnalysisResult]:
        """
        Deep analysis of a PR with collaboration metrics.
        """
        try:
            repo = self.g.get_repo(candidate.repo_name)
            pr_number = int(candidate.commit_url.split('/')[-1])
            pr = repo.get_pull(pr_number)
            
            # Analyze code quality from PR files
            files = list(pr.get_files())
            code_insights = self._analyze_code_quality(files)
            code_quality_score = code_insights['quality_score']
            
            # Analyze collaboration
            collaboration_score = self._analyze_pr_collaboration(pr)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(repo, None)
            
            # Generate golden nuggets
            golden_nuggets = self._extract_pr_golden_nuggets(pr, code_insights)
            
            # Final score
            final_score = (candidate.signal_score * 0.2 + 
                          code_quality_score * 0.3 + 
                          collaboration_score * 0.2 + 
                          impact_score * 0.3)
            
            return DeepAnalysisResult(
                candidate=candidate,
                code_quality_score=code_quality_score,
                collaboration_score=collaboration_score,
                impact_score=impact_score,
                final_score=final_score,
                code_insights=code_insights,
                golden_nuggets=golden_nuggets
            )
            
        except Exception as e:
            print(f"      ⚠️ Error analyzing PR: {e}")
            return None

    def _analyze_code_quality(self, files) -> Dict:
        """
        Analyze code quality from file diffs (implements Section 1 of the plan).
        """
        quality_score = 1.0
        
        # Safely convert files to list if it's a PaginatedList
        try:
            file_list = list(files) if hasattr(files, '__iter__') else files
        except:
            file_list = []
        
        insights = {
            'total_files': len(file_list),
            'code_files': 0,
            'test_files': 0,
            'doc_files': 0,
            'quality_indicators': [],
            'anti_patterns': [],
            'complexity_signals': []
        }
        
        try:
            for file in file_list:
                filename = file.filename
                patch = file.patch or ""
                
                # Classify file type
                if any(filename.endswith(ext) for ext in self.code_extensions):
                    insights['code_files'] += 1
                elif 'test' in filename.lower() or filename.endswith(('.test.js', '_test.py', '.spec.js')):
                    insights['test_files'] += 1
                elif filename.endswith(('.md', '.rst', '.txt')):
                    insights['doc_files'] += 1
                
                # Analyze patch content
                if patch:
                    # Look for quality indicators
                    for indicator in self.quality_indicators:
                        if indicator.lower() in patch.lower():
                            insights['quality_indicators'].append(indicator)
                            quality_score += 0.1
                    
                    # Look for complexity signals
                    complexity_keywords = ['algorithm', 'optimize', 'performance', 'concurrent', 'async']
                    for keyword in complexity_keywords:
                        if keyword in patch.lower():
                            insights['complexity_signals'].append(keyword)
                            quality_score += 0.2
                    
                    # Check for anti-patterns
                    if 'todo' in patch.lower() or 'fixme' in patch.lower():
                        insights['anti_patterns'].append('TODO/FIXME comments')
                        quality_score -= 0.1
        
        except Exception as e:
            print(f"        ⚠️ Error analyzing code quality: {e}")
        
        # Bonus for test files
        if insights['test_files'] > 0:
            quality_score += 1.0
            insights['quality_indicators'].append('Includes tests')
        
        insights['quality_score'] = min(quality_score, 5.0)  # Cap at 5.0
        return insights

    def _analyze_pr_collaboration(self, pr) -> float:
        """
        Analyze collaboration quality from PR comments (implements Section 2 of the plan).
        """
        collaboration_score = 1.0
        
        try:
            # Get review comments
            review_comments = list(pr.get_review_comments())
            issue_comments = list(pr.get_issue_comments())
            
            total_comments = len(review_comments) + len(issue_comments)
            
            if total_comments > 0:
                collaboration_score += min(total_comments * 0.2, 2.0)
            
            # Analyze comment quality (simplified)
            substantive_comments = 0
            for comment in (review_comments + issue_comments)[:10]:  # Limit to avoid rate limits
                if len(comment.body) > 50:  # Substantial comments
                    substantive_comments += 1
            
            if substantive_comments > 0:
                collaboration_score += substantive_comments * 0.3
        
        except Exception as e:
            print(f"        ⚠️ Error analyzing collaboration: {e}")
        
        return min(collaboration_score, 5.0)

    def _calculate_impact_score(self, repo, stats) -> float:
        """
        Calculate impact score based on repository importance (implements Section 3 of the plan).
        """
        try:
            # Repository popularity factor
            stars = repo.stargazers_count
            forks = repo.forks_count
            
            # Logarithmic scaling for popularity
            popularity_score = math.log(stars + 1) + math.log(forks + 1)
            
            # Normalize to reasonable range
            impact_score = min(popularity_score / 5, 5.0)
            
            return impact_score
        
        except Exception as e:
            print(f"        ⚠️ Error calculating impact: {e}")
            return 1.0

    def _extract_golden_nuggets(self, commit, code_insights) -> List[str]:
        """
        Extract specific examples for interview questions (implements Section 4 of the plan).
        """
        nuggets = []
        
        try:
            # Extract from commit message
            message = commit.commit.message
            if len(message) > 50:
                nuggets.append(f"Commit message shows clear communication: '{message[:100]}...'")
            
            # Extract from code insights
            if code_insights['quality_indicators']:
                nuggets.append(f"Demonstrates good practices: {', '.join(code_insights['quality_indicators'][:3])}")
            
            if code_insights['complexity_signals']:
                nuggets.append(f"Works with complex concepts: {', '.join(code_insights['complexity_signals'][:3])}")
            
            # File analysis
            if code_insights['test_files'] > 0:
                nuggets.append(f"Includes {code_insights['test_files']} test files - shows testing discipline")
        
        except Exception as e:
            print(f"        ⚠️ Error extracting golden nuggets: {e}")
        
        return nuggets

    def _extract_pr_golden_nuggets(self, pr, code_insights) -> List[str]:
        """
        Extract golden nuggets from PR.
        """
        nuggets = []
        
        try:
            # PR description analysis
            if pr.body and len(pr.body) > 100:
                nuggets.append(f"Detailed PR description shows planning and communication skills")
            
            # Add code insights
            nuggets.extend(self._extract_golden_nuggets(pr, code_insights))
        
        except Exception as e:
            print(f"        ⚠️ Error extracting PR nuggets: {e}")
        
        return nuggets

    def _generate_final_analysis(self, username: str, deep_results: List[DeepAnalysisResult], 
                                all_candidates: List[ContributionCandidate]) -> Dict:
        """
        Generate final analysis report with g-index and insights.
        """
        if not deep_results:
            return {
                'username': username,
                'g_index': 0,
                'total_contributions': 0,
                'analysis_type': 'standard',
                'error': 'No contributions analyzed'
            }
        
        # Sort by final score
        deep_results.sort(key=lambda r: r.final_score, reverse=True)
        
        # Calculate g-index
        g_index = 0
        for i, result in enumerate(deep_results, 1):
            if result.final_score >= i:
                g_index = i
            else:
                break
        
        # Collect all golden nuggets
        all_nuggets = []
        for result in deep_results:
            all_nuggets.extend(result.golden_nuggets)
        
        # Generate summary insights
        avg_code_quality = sum(r.code_quality_score for r in deep_results) / len(deep_results)
        avg_collaboration = sum(r.collaboration_score for r in deep_results) / len(deep_results)
        avg_impact = sum(r.impact_score for r in deep_results) / len(deep_results)
        
        return {
            'username': username,
            'analysis_type': 'standard',
            'g_index': g_index,
            'total_contributions': len(deep_results),
            'total_candidates_found': len(all_candidates),
            'top_score': deep_results[0].final_score,
            'average_scores': {
                'code_quality': avg_code_quality,
                'collaboration': avg_collaboration,
                'impact': avg_impact
            },
            'top_contributions': [
                {
                    'repo': r.candidate.repo_name,
                    'title': r.candidate.message,
                    'score': r.final_score,
                    'url': r.candidate.commit_url,
                    'type': r.candidate.contribution_type
                }
                for r in deep_results[:10]
            ],
            'golden_nuggets': all_nuggets[:15],  # Top 15 interview insights
            'phase1_candidates': len(all_candidates),
            'phase2_analyzed': len(deep_results)
        }


def test_improved_analyzer():
    """
    Test the improved analyzer, especially on the Linus Torvalds case.
    """
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        return
    
    analyzer = ImprovedHybridAnalyzer(token)
    
    # Test with Linus Torvalds (the extreme case)
    print("🧪 TESTING IMPROVED HYBRID ANALYZER")
    print("=" * 80)
    
    start_time = time.time()
    
    results = analyzer.analyze_contributor("torvalds", max_contributions=15)
    
    end_time = time.time()
    
    print(f"\n🎯 FINAL RESULTS:")
    print(f"   Analysis Type: {results.get('analysis_type', 'unknown')}")
    print(f"   G-Index: {results.get('g_index', 0)}")
    print(f"   Analysis Time: {end_time - start_time:.2f} seconds")
    
    if results.get('analysis_type') == 'maintainer_leadership':
        print(f"   Leadership Score: {results.get('leadership_score', 0):.2f}")
        print(f"   Total Stars Managed: {results.get('total_stars_managed', 0):,}")
        print(f"   Major Projects: {len(results.get('major_projects', []))}")
    else:
        print(f"   Total Contributions: {results.get('total_contributions', 0)}")
        print(f"   Candidates Found: {results.get('total_candidates_found', 0)}")
        print(f"   Top Score: {results.get('top_score', 0):.2f}")
    
    # Print top contributions
    top_contribs = results.get('top_contributions', [])
    if top_contribs:
        print(f"\n📊 Top Contributions:")
        for i, contrib in enumerate(top_contribs[:5], 1):
            print(f"   {i}. {contrib.get('repo', 'Unknown')}")
            print(f"      {contrib.get('title', 'No title')[:80]}...")
            print(f"      Score: {contrib.get('score', 0):.2f}")
            print(f"      Type: {contrib.get('type', 'unknown')}")
    
    # Print golden nuggets
    nuggets = results.get('golden_nuggets', [])
    if nuggets:
        print(f"\n💎 Golden Nuggets for Interviews:")
        for i, nugget in enumerate(nuggets[:5], 1):
            print(f"   {i}. {nugget}")
    
    return results


if __name__ == "__main__":
    test_improved_analyzer()
