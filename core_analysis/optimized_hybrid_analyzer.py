#!/usr/bin/env python3
"""
Optimized Hybrid Analyzer - Reduced API calls to avoid rate limits
"""

import os
import time
import math
from typing import Dict, List, Optional
from dataclasses import dataclass
from github import Github


@dataclass
class SimpleContribution:
    """Simplified contribution for efficient analysis."""
    repo_name: str
    title: str
    url: str
    score: float
    type: str
    created_at: str


class OptimizedHybridAnalyzer:
    """
    Optimized analyzer that minimizes API calls while implementing the hybrid approach.
    """
    
    def __init__(self, github_token: str):
        self.g = Github(github_token)

    def analyze_contributor(self, username: str, max_contributions: int = 10) -> Dict:
        """
        Optimized analysis with minimal API calls.
        """
        print(f"🔍 OPTIMIZED HYBRID ANALYSIS for {username}")
        print("=" * 50)
        
        start_time = time.time()
        results = {
            'username': username,
            'analysis_type': 'standard',
            'g_index': 0,
            'contributions': [],
            'analysis_time': 0,
            'api_calls_made': 0
        }
        
        try:
            # Phase 1: Quick user profile analysis
            print("📊 Phase 1: User Profile Analysis")
            user, user_repos = self._get_user_profile(username)
            results['api_calls_made'] += 2
            
            # Check for maintainer mode
            major_repos = [r for r in user_repos if r.stargazers_count > 1000]
            if len(major_repos) > 0:
                print(f"   👑 Found {len(major_repos)} major repositories - analyzing as maintainer")
                return self._analyze_as_maintainer(username, user, major_repos, start_time)
            
            # Phase 2: Recent contributions analysis
            print("📊 Phase 2: Recent Contributions Analysis")
            contributions = self._analyze_recent_contributions(username, user_repos[:5], max_contributions)
            results['api_calls_made'] += len(user_repos[:5]) * 2  # Commits + PR search per repo
            
            # Phase 3: External contributions via search
            print("📊 Phase 3: External Contributions (Limited Search)")
            external_contribs = self._analyze_external_contributions(username, max_contributions // 2)
            results['api_calls_made'] += 1  # One search query
            
            contributions.extend(external_contribs)
            
            # Calculate final results
            if contributions:
                contributions.sort(key=lambda c: c.score, reverse=True)
                results['contributions'] = contributions[:max_contributions]
                results['g_index'] = self._calculate_g_index(results['contributions'])
                results['top_score'] = contributions[0].score
                results['total_contributions'] = len(contributions)
            
            end_time = time.time()
            results['analysis_time'] = end_time - start_time
            
            print(f"✅ Analysis complete in {results['analysis_time']:.2f}s with {results['api_calls_made']} API calls")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in analysis: {e}")
            results['error'] = str(e)
            return results

    def _get_user_profile(self, username: str):
        """Get basic user profile and repositories."""
        user = self.g.get_user(username)
        repos = list(user.get_repos(type='owner', sort='stars', direction='desc')[:10])
        
        print(f"   👤 User: {user.name or username}")
        print(f"   📁 Public repos: {user.public_repos}")
        print(f"   ⭐ Total stars: {sum(r.stargazers_count for r in repos)}")
        
        return user, repos

    def _analyze_as_maintainer(self, username: str, user, major_repos: List, start_time: float) -> Dict:
        """Analyze user as a project maintainer."""
        print("   🔍 Analyzing maintainer contributions...")
        
        leadership_score = 0
        total_stars = 0
        projects = []
        
        for repo in major_repos:
            project_impact = math.log(repo.stargazers_count + 1) * 2
            leadership_score += project_impact
            total_stars += repo.stargazers_count
            
            projects.append({
                'name': repo.full_name,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'language': repo.language,
                'impact_score': project_impact
            })
        
        # Calculate maintainer g-index
        projects.sort(key=lambda p: p['impact_score'], reverse=True)
        g_index = 0
        for i, project in enumerate(projects, 1):
            if project['impact_score'] >= i:
                g_index = i
            else:
                break
        
        end_time = time.time()
        
        return {
            'username': username,
            'analysis_type': 'maintainer_leadership',
            'g_index': g_index,
            'leadership_score': leadership_score,
            'total_stars_managed': total_stars,
            'major_projects': projects,
            'analysis_time': end_time - start_time,
            'api_calls_made': 2 + len(major_repos)  # User + repos + repo details
        }

    def _analyze_recent_contributions(self, username: str, repos: List, max_contribs: int) -> List[SimpleContribution]:
        """Analyze recent contributions in user's repositories."""
        contributions = []
        
        print(f"   🔍 Analyzing recent work in {len(repos)} repositories...")
        
        for repo in repos:
            try:
                # Get recent commits - handle empty repositories
                commits = list(repo.get_commits(author=username)[:5])
                
                if not commits:
                    continue
                
                for commit in commits:
                    try:
                        # Skip merge commits (safely check parents)
                        try:
                            parents_count = len(list(commit.parents))
                            if parents_count > 1:
                                continue
                        except:
                            # If we can't determine parent count, assume it's not a merge
                            pass
                        
                        # Safely access commit data
                        if not hasattr(commit, 'commit') or not commit.commit:
                            continue
                        
                        if not hasattr(commit.commit, 'message') or not commit.commit.message:
                            continue
                        
                        # Calculate simple score
                        score = 1.0
                        
                        # Repository popularity bonus
                        if repo.stargazers_count > 0:
                            score += math.log(repo.stargazers_count + 1) / 5
                        
                        # Message quality bonus
                        message = commit.commit.message.lower()
                        quality_keywords = ['feat', 'fix', 'refactor', 'perf', 'implement']
                        keyword_bonus = sum(0.2 for keyword in quality_keywords if keyword in message)
                        score += keyword_bonus
                        
                        contributions.append(SimpleContribution(
                            repo_name=repo.full_name,
                            title=commit.commit.message.split('\n')[0][:80],
                            url=commit.html_url,
                            score=score,
                            type='own_repo_commit',
                            created_at=commit.commit.author.date.isoformat()
                        ))
                        
                        if len(contributions) >= max_contribs:
                            break
                    
                    except Exception as e:
                        print(f"       ⚠️ Error processing commit in {repo.name}: {e}")
                        continue
                
                if len(contributions) >= max_contribs:
                    break
                    
            except Exception as e:
                print(f"     ⚠️ Error analyzing {repo.name}: {e}")
                continue
        
        print(f"   ✅ Found {len(contributions)} own repository contributions")
        return contributions

    def _analyze_external_contributions(self, username: str, max_contribs: int) -> List[SimpleContribution]:
        """Analyze external contributions with minimal API calls."""
        contributions = []
        
        print("   🔍 Searching for external contributions...")
        
        try:
            # Single search for merged PRs
            pr_results = self.g.search_issues(
                f"author:{username} type:pr is:merged",
                sort="updated",
                order="desc"
            )
            
            count = 0
            for pr in pr_results:
                if count >= max_contribs:
                    break
                
                try:
                    repo = pr.repository
                    
                    # Calculate score based on repository popularity
                    score = 2.0  # Base score for external PR
                    if repo.stargazers_count > 0:
                        score += math.log(repo.stargazers_count + 1) / 3
                    
                    # Comments indicate discussion
                    if pr.comments > 0:
                        score += min(pr.comments * 0.1, 1.0)
                    
                    contributions.append(SimpleContribution(
                        repo_name=repo.full_name,
                        title=pr.title[:80],
                        url=pr.html_url,
                        score=score,
                        type='external_pr',
                        created_at=pr.created_at.isoformat()
                    ))
                    
                    count += 1
                    
                except Exception as e:
                    print(f"     ⚠️ Error analyzing PR: {e}")
                    continue
            
            print(f"   ✅ Found {len(contributions)} external contributions")
            
        except Exception as e:
            print(f"   ⚠️ Error searching external PRs: {e}")
        
        return contributions

    def _calculate_g_index(self, contributions: List[SimpleContribution]) -> int:
        """Calculate g-index from contribution scores."""
        if not contributions:
            return 0
        
        # Sort by score descending
        sorted_contribs = sorted(contributions, key=lambda c: c.score, reverse=True)
        
        g_index = 0
        for i, contrib in enumerate(sorted_contribs, 1):
            if contrib.score >= i:
                g_index = i
            else:
                break
        
        return g_index


def test_optimized_analyzer():
    """Test the optimized analyzer."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Please set GITHUB_TOKEN environment variable")
        return
    
    analyzer = OptimizedHybridAnalyzer(token)
    
    # Test with both users
    for username in ['trivialfis', 'torvalds']:
        print(f"\n🧪 TESTING {username.upper()}")
        print("=" * 60)
        
        results = analyzer.analyze_contributor(username, max_contributions=8)
        
        print(f"\n🎯 RESULTS:")
        print(f"   Analysis Type: {results.get('analysis_type')}")
        print(f"   G-Index: {results.get('g_index', 0)}")
        print(f"   Analysis Time: {results.get('analysis_time', 0):.2f}s")
        print(f"   API Calls: {results.get('api_calls_made', 0)}")
        
        if results.get('analysis_type') == 'maintainer_leadership':
            print(f"   Leadership Score: {results.get('leadership_score', 0):.2f}")
            print(f"   Stars Managed: {results.get('total_stars_managed', 0):,}")
            
            projects = results.get('major_projects', [])
            if projects:
                print(f"   Major Projects:")
                for proj in projects[:3]:
                    print(f"     - {proj['name']}: {proj['stars']:,} stars")
        else:
            print(f"   Total Contributions: {results.get('total_contributions', 0)}")
            if results.get('top_score'):
                print(f"   Top Score: {results.get('top_score'):.2f}")
            
            contribs = results.get('contributions', [])
            if contribs:
                print(f"   Top Contributions:")
                for i, contrib in enumerate(contribs[:3], 1):
                    print(f"     {i}. {contrib.repo_name} ({contrib.type})")
                    print(f"        {contrib.title}")
                    print(f"        Score: {contrib.score:.2f}")
        
        if 'error' in results:
            print(f"   ❌ Error: {results['error']}")
        
        print()


if __name__ == "__main__":
    test_optimized_analyzer()
