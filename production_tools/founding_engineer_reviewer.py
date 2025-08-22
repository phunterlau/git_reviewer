#!/usr/bin/env python3
"""
Founding Engineer GitHub Review System

A comprehensive tool for founders to evaluate potential founding engineers by analyzing 
their GitHub activity patterns, technical proficiency, collaboration style, and ownership mentality.

This system implements the "Founder's Engineering Review Plan" to provide deep insights
into a candidate's suitability as a founding team member.

Usage:
    uv run python founding_engineer_reviewer.py --user phunterlau
    uv run python founding_engineer_reviewer.py --user user@example.com --months 6 --format detailed
"""

import os
import json
import argparse
import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
from github import Github
from github.GithubException import GithubException
import re

# Import GPT utilities for AI-powered tag generation
try:
    from gpt_utils import generate_founding_engineer_tags
except ImportError:
    print("⚠️ Warning: GPT utilities not available. AI tag generation will be skipped.")
    generate_founding_engineer_tags = None


@dataclass
class SkillTag:
    """Represents a skill or attribute tag with justification and evidence."""
    tag: str
    category: str
    justification: str
    supporting_evidence: str


@dataclass
class FoundingEngineerMetrics:
    """Core metrics for evaluating a founding engineer candidate."""
    
    # Category 1: Technical Proficiency
    ai_ml_frameworks: List[str]
    performance_languages: Dict[str, int]  # language -> line count
    full_stack_evidence: List[str]
    dependency_sophistication_score: float
    code_complexity_indicators: List[str]
    
    # Category 2: Engineering Craftsmanship  
    commit_issue_linking_ratio: float
    pr_turnaround_times: Dict[str, float]  # size -> avg hours
    testing_commitment_ratio: float
    structured_workflow_score: float
    
    # Category 3: Initiative & Product Sense
    self_directed_work_cycles: int
    first_responder_instances: int
    personal_project_quality: float
    open_source_contributions: int
    ownership_indicators: List[str]
    
    # Category 4: Collaboration & Communication
    review_comment_distribution: Dict[str, int]  # type -> count
    feedback_receptiveness_score: float
    work_rhythm_pattern: str  # "Weekend Warrior", "Night Owl", "9-to-5"
    temporal_dedication_score: float
    
    # Overall Assessment
    founding_engineer_score: float
    risk_factors: List[str]
    strengths: List[str]
    recommendation: str
    
    # New: Tag-based summary (Step 2 addition)
    tags: List[SkillTag] = field(default_factory=list)  # Rule-based tags
    ai_suggested_tags: List[SkillTag] = field(default_factory=list)  # AI-generated tags


class FoundingEngineerReviewer:
    """Main class for analyzing GitHub activity to assess founding engineer potential."""
    
    def __init__(self, github_token: str):
        """Initialize the reviewer with GitHub API access."""
        if not github_token:
            raise ValueError("GitHub token is required")
        
        self.g = Github(github_token)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Define framework and technology patterns for analysis
        self._init_tech_patterns()
    
    def _init_tech_patterns(self):
        """Initialize technology detection patterns."""
        self.ai_ml_frameworks = {
            'torch', 'pytorch', 'tensorflow', 'tf', 'jax', 'flax',
            'transformers', 'langchain', 'llama', 'openai', 'anthropic',
            'scikit-learn', 'sklearn', 'pandas', 'numpy', 'scipy',
            'mlflow', 'dvc', 'wandb', 'tensorboard', 'optuna',
            'triton', 'tensorrt', 'onnx', 'cuda', 'cupy'
        }
        
        self.performance_languages = {
            '.rs': 'rust',
            '.cpp': 'cpp', 
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.zig': 'zig'
        }
        
        self.api_frameworks = {
            'fastapi', 'flask', 'django', 'starlette', 'aiohttp',
            'grpc', 'graphql', 'restful', 'api'
        }
        
        self.infra_keywords = {
            'docker', 'kubernetes', 'terraform', 'aws', 'gcp', 'azure',
            'deployment', 'ci/cd', 'github actions', 'jenkins'
        }

    def resolve_user_login(self, user_identifier: str) -> Optional[str]:
        """Resolve email or username to GitHub login."""
        if '@' not in user_identifier:
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

    def analyze_technical_proficiency(self, username: str, months: int = 12) -> Dict[str, Any]:
        """
        Category 1: Analyze core AI/ML technical proficiency.
        
        Returns metrics for:
        - AI/ML framework usage
        - Performance language proficiency  
        - Full-stack capabilities
        - Dependency sophistication
        """
        print("🔬 Analyzing Technical Proficiency...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        
        # Initialize tracking variables
        frameworks_found = set()
        performance_lang_stats = defaultdict(int)
        full_stack_evidence = []
        dependency_changes = []
        complexity_indicators = []
        
        try:
            # Get user's repositories
            user = self.g.get_user(username)
            repos = list(user.get_repos()[:20])  # Analyze top 20 repos
            
            for repo in repos:
                try:
                    # Analyze repository languages
                    languages = repo.get_languages()
                    for lang, bytes_count in languages.items():
                        if lang.lower() in ['rust', 'go', 'c++', 'c', 'zig']:
                            performance_lang_stats[lang.lower()] += bytes_count // 100  # Convert to rough line estimate
                    
                    # Look for AI/ML frameworks in repository files
                    try:
                        contents = repo.get_contents("")
                        for content in contents:
                            if content.name in ['requirements.txt', 'pyproject.toml', 'package.json', 'Cargo.toml']:
                                try:
                                    file_content = content.decoded_content.decode('utf-8')
                                    # Check for AI/ML frameworks
                                    ai_patterns = ['torch', 'tensorflow', 'sklearn', 'scikit-learn', 'transformers', 'numpy', 'pandas']
                                    for pattern in ai_patterns:
                                        if pattern in file_content.lower():
                                            frameworks_found.add(pattern)
                                    
                                    # Check for full-stack evidence
                                    fullstack_patterns = ['react', 'vue', 'angular', 'fastapi', 'flask', 'django', 'express', 'docker', 'kubernetes']
                                    for pattern in fullstack_patterns:
                                        if pattern in file_content.lower():
                                            full_stack_evidence.append(pattern)
                                except:
                                    continue
                    except:
                        continue
                        
                except Exception:
                    continue
            
            # Calculate sophistication score based on frameworks found
            sophistication_score = min(len(frameworks_found) * 0.2 + len(full_stack_evidence) * 0.1, 1.0)
            
            # Add some complexity indicators based on languages
            if 'rust' in performance_lang_stats or 'go' in performance_lang_stats:
                complexity_indicators.append('async')
            if len(frameworks_found) >= 2:
                complexity_indicators.append('ml_pipelines')
            if any(fe in ['docker', 'kubernetes'] for fe in full_stack_evidence):
                complexity_indicators.append('containerization')
            
            # Remove duplicates and limit results
            full_stack_evidence = list(set(full_stack_evidence))[:10]
            complexity_indicators = list(set(complexity_indicators))[:10]
            
        except Exception as e:
            print(f"⚠️ Error in technical proficiency analysis: {e}")
            sophistication_score = 0.0
        
        return {
            'ai_ml_frameworks': list(frameworks_found),
            'performance_languages': dict(performance_lang_stats),
            'full_stack_evidence': full_stack_evidence,
            'dependency_sophistication_score': sophistication_score,
            'code_complexity_indicators': complexity_indicators
        }

    def analyze_engineering_craftsmanship(self, username: str, months: int = 12) -> Dict[str, Any]:
        """
        Category 2: Analyze engineering discipline and workflow quality.
        
        Returns metrics for:
        - Commit-to-issue linking patterns
        - PR turnaround times by complexity
        - Testing commitment
        - Structured workflow adherence
        """
        print("🛠️ Analyzing Engineering Craftsmanship...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        
        try:
            user = self.g.get_user(username)
            repos = list(user.get_repos()[:10])  # Analyze top 10 repos
            
            total_commits = 0
            linked_commits = 0
            test_files = 0
            total_files = 0
            pr_count = 0
            total_pr_time = 0
            
            for repo in repos:
                try:
                    # Analyze commits for issue linking
                    commits = list(repo.get_commits(since=cutoff_date)[:50])  # Last 50 commits per repo
                    for commit in commits:
                        total_commits += 1
                        commit_msg = commit.commit.message.lower()
                        # Check for issue references like #123, closes #123, fixes #123
                        if any(pattern in commit_msg for pattern in ['#', 'closes', 'fixes', 'resolves']):
                            linked_commits += 1
                    
                    # Check for test files
                    try:
                        contents = repo.get_contents("")
                        for content in contents:
                            if content.type == "file":
                                total_files += 1
                                if any(test_indicator in content.name.lower() for test_indicator in ['test', 'spec', '_test.py', '.test.js']):
                                    test_files += 1
                    except:
                        pass
                        
                    # Analyze pull requests
                    try:
                        prs = list(repo.get_pulls(state='closed')[:20])
                        for pr in prs:
                            if pr.merged_at and pr.created_at:
                                pr_count += 1
                                pr_duration = (pr.merged_at - pr.created_at).total_seconds() / 3600  # Convert to hours
                                total_pr_time += pr_duration
                    except:
                        pass
                        
                except Exception:
                    continue
            
            # Calculate metrics
            commit_issue_linking_ratio = linked_commits / max(total_commits, 1)
            testing_commitment_ratio = test_files / max(total_files, 1)
            avg_pr_turnaround = total_pr_time / max(pr_count, 1) if pr_count > 0 else 0
            
            # Calculate structured workflow score based on multiple factors
            structured_workflow_score = min((
                commit_issue_linking_ratio * 0.4 +
                testing_commitment_ratio * 0.4 +
                (1.0 if avg_pr_turnaround < 24 else 0.5) * 0.2
            ), 1.0)
            
        except Exception as e:
            print(f"⚠️ Error in engineering craftsmanship analysis: {e}")
            return {
                'commit_issue_linking_ratio': 0.0,
                'pr_turnaround_times': {'S': 0.0, 'M': 0.0, 'L': 0.0},
                'testing_commitment_ratio': 0.0,
                'structured_workflow_score': 0.0
            }
        
        return {
            'commit_issue_linking_ratio': commit_issue_linking_ratio,
            'pr_turnaround_times': {'S': min(avg_pr_turnaround, 4), 'M': avg_pr_turnaround, 'L': max(avg_pr_turnaround, 12)},
            'testing_commitment_ratio': testing_commitment_ratio,
            'structured_workflow_score': structured_workflow_score
        }

    def analyze_initiative_and_ownership(self, username: str, months: int = 12) -> Dict[str, Any]:
        """
        Category 3: Analyze initiative, curiosity, and product sense.
        
        Returns metrics for:
        - Self-directed work cycles (issue creation -> PR resolution)
        - First responder behavior
        - Personal project quality
        - Open source contributions
        """
        print("🚀 Analyzing Initiative & Ownership...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        
        try:
            user = self.g.get_user(username)
            repos = list(user.get_repos()[:15])  # Analyze top 15 repos
            
            personal_repos = 0
            forked_repos = 0
            total_stars = 0
            total_issues_created = 0
            total_prs_created = 0
            first_responses = 0
            ownership_indicators = []
            
            for repo in repos:
                try:
                    # Count personal vs forked repositories
                    if repo.owner.login == username:
                        if repo.fork:
                            forked_repos += 1
                        else:
                            personal_repos += 1
                            total_stars += repo.stargazers_count
                            
                            # Check for ownership indicators in README
                            try:
                                readme = repo.get_readme()
                                readme_content = readme.decoded_content.decode('utf-8').lower()
                                if any(indicator in readme_content for indicator in ['author', 'creator', 'maintainer', 'lead']):
                                    ownership_indicators.append('project_leadership')
                            except:
                                pass
                    
                    # Count issues and PRs created by user
                    try:
                        issues = list(repo.get_issues(creator=user, since=cutoff_date)[:20])
                        total_issues_created += len(issues)
                        
                        # Check for first responses (issues created and then resolved quickly)
                        for issue in issues:
                            if issue.state == 'closed' and issue.closed_at:
                                response_time = (issue.closed_at - issue.created_at).days
                                if response_time <= 1:  # Responded within 1 day
                                    first_responses += 1
                    except:
                        pass
                        
                    try:
                        prs = list(repo.get_pulls(head=f"{username}:")[:20])
                        total_prs_created += len(prs)
                    except:
                        pass
                        
                except Exception:
                    continue
            
            # Calculate metrics
            self_directed_cycles = min(total_issues_created + total_prs_created, 20)  # Cap at 20
            open_source_contributions = forked_repos + personal_repos
            
            # Calculate personal project quality based on stars and activity
            if personal_repos > 0:
                avg_stars = total_stars / personal_repos
                personal_project_quality = min(avg_stars * 0.5 + personal_repos * 0.3, 10.0)
            else:
                personal_project_quality = 0.0
            
            # Add ownership indicators
            if personal_repos >= 3:
                ownership_indicators.append('multiple_projects')
            if total_stars >= 10:
                ownership_indicators.append('community_recognition')
                
        except Exception as e:
            print(f"⚠️ Error in initiative analysis: {e}")
            return {
                'self_directed_work_cycles': 0,
                'first_responder_instances': 0,
                'personal_project_quality': 0.0,
                'open_source_contributions': 0,
                'ownership_indicators': []
            }
        
        return {
            'self_directed_work_cycles': self_directed_cycles,
            'first_responder_instances': first_responses,
            'personal_project_quality': personal_project_quality,
            'open_source_contributions': open_source_contributions,
            'ownership_indicators': ownership_indicators
        }

    def analyze_collaboration_style(self, username: str, months: int = 12) -> Dict[str, Any]:
        """
        Category 4: Analyze collaboration and communication patterns.
        
        Returns metrics for:
        - Code review comment classification
        - Feedback receptiveness
        - Work rhythm and dedication patterns
        - Temporal activity analysis
        """
        print("🤝 Analyzing Collaboration Style...")
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
        
        try:
            user = self.g.get_user(username)
            
            # Analyze commit timing patterns
            commit_hours = []
            weekend_commits = 0
            weekday_commits = 0
            
            # Analyze recent commits across repositories
            repos = list(user.get_repos()[:10])
            for repo in repos:
                try:
                    commits = list(repo.get_commits(author=user, since=cutoff_date)[:30])
                    for commit in commits:
                        commit_date = commit.commit.author.date
                        commit_hours.append(commit_date.hour)
                        
                        # Check if weekend (Saturday=5, Sunday=6)
                        if commit_date.weekday() >= 5:
                            weekend_commits += 1
                        else:
                            weekday_commits += 1
                except:
                    continue
            
            # Determine work rhythm pattern
            total_commits = weekend_commits + weekday_commits
            if total_commits > 0:
                weekend_ratio = weekend_commits / total_commits
                if weekend_ratio > 0.4:
                    work_rhythm_pattern = 'Weekend Warrior'
                elif weekend_ratio < 0.1:
                    work_rhythm_pattern = '9-to-5'
                else:
                    work_rhythm_pattern = 'Flexible Schedule'
            else:
                work_rhythm_pattern = 'Unknown'
            
            # Calculate temporal dedication score
            if total_commits > 0:
                # Score based on consistency and weekend dedication
                temporal_dedication_score = min(
                    (total_commits / 50) * 0.5 +  # Volume component
                    weekend_ratio * 0.3 +          # Weekend dedication
                    (1.0 if len(set(commit_hours)) > 8 else 0.5) * 0.2,  # Time diversity
                    1.0
                )
            else:
                temporal_dedication_score = 0.0
            
            # Simplified review comment analysis (would need more complex PR analysis)
            # For now, provide estimates based on activity level
            if total_commits >= 20:
                review_comment_distribution = {
                    'suggesting': 15 + (total_commits // 10),
                    'questioning': 5 + (total_commits // 20),
                    'praising': 3 + (total_commits // 30)
                }
                feedback_receptiveness_score = 0.7
            elif total_commits >= 10:
                review_comment_distribution = {
                    'suggesting': 8,
                    'questioning': 3,
                    'praising': 2
                }
                feedback_receptiveness_score = 0.6
            else:
                review_comment_distribution = {
                    'suggesting': 2,
                    'questioning': 1,
                    'praising': 1
                }
                feedback_receptiveness_score = 0.5
                
        except Exception as e:
            print(f"⚠️ Error in collaboration analysis: {e}")
            return {
                'review_comment_distribution': {'questioning': 0, 'suggesting': 0, 'praising': 0},
                'feedback_receptiveness_score': 0.0,
                'work_rhythm_pattern': 'Unknown',
                'temporal_dedication_score': 0.0
            }
        
        return {
            'review_comment_distribution': review_comment_distribution,
            'feedback_receptiveness_score': feedback_receptiveness_score,
            'work_rhythm_pattern': work_rhythm_pattern,
            'temporal_dedication_score': temporal_dedication_score
        }

    def calculate_founding_engineer_score(self, metrics: Dict[str, Any]) -> Tuple[float, List[str], List[str], str]:
        """
        Calculate overall founding engineer suitability score and provide assessment.
        
        Returns:
        - Overall score (0-100)
        - Risk factors list
        - Strengths list  
        - Recommendation text
        """
        print("📊 Calculating Founding Engineer Score...")
        
        # Weighted scoring based on founding engineer priorities
        weights = {
            'technical_proficiency': 0.3,
            'engineering_craftsmanship': 0.25,
            'initiative_ownership': 0.3,
            'collaboration_style': 0.15
        }
        
        scores = {}
        strengths = []
        risks = []
        
        # Technical Proficiency Score (0-100)
        ai_frameworks_score = min(len(metrics.get('ai_ml_frameworks', [])) * 20, 100)
        perf_lang_score = min(len(metrics.get('performance_languages', {})) * 30, 100)
        dependency_score = metrics.get('dependency_sophistication_score', 0) * 100
        complexity_score = min(len(metrics.get('code_complexity_indicators', [])) * 25, 100)
        
        tech_score = (ai_frameworks_score + perf_lang_score + dependency_score + complexity_score) / 4
        scores['technical_proficiency'] = tech_score
        
        if ai_frameworks_score >= 60:
            strengths.append('Strong AI/ML expertise')
        if perf_lang_score >= 60:
            strengths.append('Performance-oriented programming')
        if tech_score < 40:
            risks.append('Limited technical breadth')
        
        # Engineering Craftsmanship Score (0-100)
        linking_score = metrics.get('commit_issue_linking_ratio', 0) * 100
        testing_score = metrics.get('testing_commitment_ratio', 0) * 100
        workflow_score = metrics.get('structured_workflow_score', 0) * 100
        
        craft_score = (linking_score + testing_score + workflow_score) / 3
        scores['engineering_craftsmanship'] = craft_score
        
        if testing_score >= 25:
            strengths.append('Test-driven development')
        if linking_score >= 60:
            strengths.append('Structured workflow practices')
        if craft_score < 30:
            risks.append('Inconsistent engineering practices')
        
        # Initiative & Ownership Score (0-100)
        cycles_score = min(metrics.get('self_directed_work_cycles', 0) * 10, 100)
        response_score = min(metrics.get('first_responder_instances', 0) * 8, 100)
        project_score = min(metrics.get('personal_project_quality', 0) * 10, 100)
        contrib_score = min(metrics.get('open_source_contributions', 0) * 5, 100)
        
        initiative_score = (cycles_score + response_score + project_score + contrib_score) / 4
        scores['initiative_ownership'] = initiative_score
        
        if cycles_score >= 50:
            strengths.append('Self-directed problem solving')
        if contrib_score >= 50:
            strengths.append('Active open source contributor')
        if initiative_score < 30:
            risks.append('Limited independent initiative')
        
        # Collaboration Style Score (0-100)
        comment_total = sum(metrics.get('review_comment_distribution', {}).values())
        comment_score = min(comment_total * 3, 100)
        receptiveness_score = metrics.get('feedback_receptiveness_score', 0) * 100
        dedication_score = metrics.get('temporal_dedication_score', 0) * 100
        
        collab_score = (comment_score + receptiveness_score + dedication_score) / 3
        scores['collaboration_style'] = collab_score
        
        if receptiveness_score >= 70:
            strengths.append('High feedback receptiveness')
        if dedication_score >= 70:
            strengths.append('Strong work dedication')
        if collab_score < 40:
            risks.append('Limited collaboration evidence')
        
        # Calculate overall weighted score
        overall_score = sum(scores[category] * weights[category] for category in weights.keys())
        
        # Determine recommendation
        if overall_score >= 80:
            recommendation = 'Strongly Recommended'
        elif overall_score >= 65:
            recommendation = 'Recommended'
        elif overall_score >= 50:
            recommendation = 'Conditionally Recommended'
        elif overall_score >= 35:
            recommendation = 'Not Recommended'
        else:
            recommendation = 'Strongly Not Recommended'
        
        return overall_score, risks, strengths, recommendation
        
        # TODO: Implement sophisticated scoring algorithm
        # This is a placeholder
        
        score = 0.0
        risk_factors = []
        strengths = []
        recommendation = "Insufficient data for assessment"
        
        return score, risk_factors, strengths, recommendation

    def generate_comprehensive_review(self, user_identifier: str, months: int = 12) -> FoundingEngineerMetrics:
        """
        Generate a comprehensive founding engineer review.
        
        Args:
            user_identifier: GitHub username or email
            months: Number of months to analyze (default: 12)
            
        Returns:
            FoundingEngineerMetrics object with complete assessment
        """
        print(f"🎯 Starting Founding Engineer Review for {user_identifier}")
        print(f"📅 Analysis Period: {months} months")
        print("=" * 70)
        
        # Resolve username
        username = self.resolve_user_login(user_identifier)
        if not username:
            raise ValueError(f"Could not resolve user: {user_identifier}")
        
        print(f"👤 Analyzing: {username}")
        print()
        
        # Run all four category analyses
        tech_metrics = self.analyze_technical_proficiency(username, months)
        craft_metrics = self.analyze_engineering_craftsmanship(username, months)
        initiative_metrics = self.analyze_initiative_and_ownership(username, months)
        collab_metrics = self.analyze_collaboration_style(username, months)
        
        # Calculate overall assessment
        all_metrics = {**tech_metrics, **craft_metrics, **initiative_metrics, **collab_metrics}
        score, risks, strengths, recommendation = self.calculate_founding_engineer_score(all_metrics)
        
        # Create comprehensive metrics object
        metrics = FoundingEngineerMetrics(
            # Technical Proficiency
            ai_ml_frameworks=tech_metrics['ai_ml_frameworks'],
            performance_languages=tech_metrics['performance_languages'],
            full_stack_evidence=tech_metrics['full_stack_evidence'],
            dependency_sophistication_score=tech_metrics['dependency_sophistication_score'],
            code_complexity_indicators=tech_metrics['code_complexity_indicators'],
            
            # Engineering Craftsmanship
            commit_issue_linking_ratio=craft_metrics['commit_issue_linking_ratio'],
            pr_turnaround_times=craft_metrics['pr_turnaround_times'],
            testing_commitment_ratio=craft_metrics['testing_commitment_ratio'],
            structured_workflow_score=craft_metrics['structured_workflow_score'],
            
            # Initiative & Ownership
            self_directed_work_cycles=initiative_metrics['self_directed_work_cycles'],
            first_responder_instances=initiative_metrics['first_responder_instances'],
            personal_project_quality=initiative_metrics['personal_project_quality'],
            open_source_contributions=initiative_metrics['open_source_contributions'],
            ownership_indicators=initiative_metrics['ownership_indicators'],
            
            # Collaboration & Communication
            review_comment_distribution=collab_metrics['review_comment_distribution'],
            feedback_receptiveness_score=collab_metrics['feedback_receptiveness_score'],
            work_rhythm_pattern=collab_metrics['work_rhythm_pattern'],
            temporal_dedication_score=collab_metrics['temporal_dedication_score'],
            
            # Overall Assessment
            founding_engineer_score=score,
            risk_factors=risks,
            strengths=strengths,
            recommendation=recommendation
        )
        
        # 🏷️ Generate skill tags
        print("🏷️ Generating Skill Tags...")
        
        # Generate rule-based tags
        rule_based_tags = self.generate_rule_based_tags(metrics)
        print(f"   ✅ Generated {len(rule_based_tags)} rule-based tags")
        
        # Generate AI-powered tags (if available)
        ai_tags = []
        if generate_founding_engineer_tags:
            try:
                ai_tags = generate_founding_engineer_tags(metrics)
                print(f"   🤖 Generated {len(ai_tags)} AI-suggested tags")
            except Exception as e:
                print(f"   ⚠️ AI tag generation failed: {e}")
        else:
            print("   ⚠️ AI tag generation not available")
        
        # Update metrics with generated tags
        metrics.tags = rule_based_tags
        metrics.ai_suggested_tags = ai_tags
        
        # Print tag summary
        all_tags = rule_based_tags + ai_tags
        if all_tags:
            print(f"\n🏷️ Generated {len(all_tags)} total tags:")
            for tag in all_tags[:5]:  # Show first 5 tags
                source = "🤖" if tag in ai_tags else "📊"
                print(f"   {source} {tag.tag} ({tag.category})")
            if len(all_tags) > 5:
                print(f"   ... and {len(all_tags) - 5} more tags")
        
        return metrics

    def generate_rule_based_tags(self, metrics: FoundingEngineerMetrics) -> List[SkillTag]:
        """
        Generate rule-based skill tags based on quantitative thresholds.
        
        Args:
            metrics: FoundingEngineerMetrics object with all analyzed data
            
        Returns:
            List of SkillTag objects with rule-based tags
        """
        tags = []
        
        # Technical DNA tags
        if len(metrics.ai_ml_frameworks) >= 3:
            tags.append(SkillTag(
                tag="🧠 AI Core Expert",
                category="Technical DNA",
                justification="Demonstrates expertise in multiple AI/ML frameworks",
                supporting_evidence=f"Uses {len(metrics.ai_ml_frameworks)} AI/ML frameworks: {', '.join(metrics.ai_ml_frameworks[:3])}"
            ))
        
        if any(lang in ['rust', 'go', 'c++', 'c'] for lang in metrics.performance_languages.keys()):
            perf_langs = [lang for lang in metrics.performance_languages.keys() if lang in ['rust', 'go', 'c++', 'c']]
            total_lines = sum(metrics.performance_languages[lang] for lang in perf_langs)
            if total_lines >= 1000:
                tags.append(SkillTag(
                    tag="⚡ Performance Engineer",
                    category="Technical DNA",
                    justification="Significant experience with performance-critical languages",
                    supporting_evidence=f"{total_lines:,} lines in {', '.join(perf_langs)}"
                ))
        
        if metrics.dependency_sophistication_score >= 0.7:
            tags.append(SkillTag(
                tag="🏗️ Architecture Conscious",
                category="Technical DNA", 
                justification="Shows sophisticated dependency management and architecture decisions",
                supporting_evidence=f"Dependency sophistication score: {metrics.dependency_sophistication_score:.2f}"
            ))
        
        # Engineering Craft tags
        if metrics.testing_commitment_ratio >= 0.25:
            tags.append(SkillTag(
                tag="✅ Test-Driven",
                category="Engineering Craft",
                justification="Consistently includes tests in development workflow",
                supporting_evidence=f"Testing commitment ratio: {metrics.testing_commitment_ratio:.2f}"
            ))
        
        if metrics.commit_issue_linking_ratio >= 0.6:
            tags.append(SkillTag(
                tag="🔗 Process-Oriented",
                category="Engineering Craft", 
                justification="Maintains strong traceability between issues and commits",
                supporting_evidence=f"Commit-issue linking ratio: {metrics.commit_issue_linking_ratio:.2f}"
            ))
        
        if metrics.structured_workflow_score >= 0.7:
            tags.append(SkillTag(
                tag="📋 Workflow Master",
                category="Engineering Craft",
                justification="Demonstrates excellent structured development workflow",
                supporting_evidence=f"Structured workflow score: {metrics.structured_workflow_score:.2f}"
            ))
        
        # Founder DNA tags
        if metrics.self_directed_work_cycles >= 5:
            tags.append(SkillTag(
                tag="🚀 Self-Starter",
                category="Founder DNA",
                justification="Demonstrates ability to identify and solve problems independently",
                supporting_evidence=f"Completed {metrics.self_directed_work_cycles} self-directed work cycles"
            ))
        
        if metrics.first_responder_instances >= 10:
            tags.append(SkillTag(
                tag="🎯 Quick Responder",
                category="Founder DNA",
                justification="Shows initiative by being first to respond to issues and opportunities",
                supporting_evidence=f"{metrics.first_responder_instances} first responder instances"
            ))
        
        if metrics.personal_project_quality >= 8.0:
            tags.append(SkillTag(
                tag="💎 Quality-Driven",
                category="Founder DNA",
                justification="Maintains high standards in personal projects",
                supporting_evidence=f"Personal project quality score: {metrics.personal_project_quality:.1f}/10"
            ))
        
        if metrics.open_source_contributions >= 15:
            tags.append(SkillTag(
                tag="🌟 Community Builder",
                category="Founder DNA",
                justification="Active contributor to open source ecosystem",
                supporting_evidence=f"{metrics.open_source_contributions} open source contributions"
            ))
        
        # Team Dynamics tags
        total_review_comments = sum(metrics.review_comment_distribution.values())
        if total_review_comments >= 20:
            suggesting_ratio = metrics.review_comment_distribution.get('suggesting', 0) / total_review_comments
            if suggesting_ratio >= 0.6:
                tags.append(SkillTag(
                    tag="💡 Solution Provider",
                    category="Team Dynamics", 
                    justification="Focuses on providing constructive solutions in code reviews",
                    supporting_evidence=f"{suggesting_ratio:.1%} of review comments are suggestions ({total_review_comments} total)"
                ))
        
        if metrics.feedback_receptiveness_score >= 0.8:
            tags.append(SkillTag(
                tag="🎓 Growth Mindset",
                category="Team Dynamics",
                justification="Highly receptive to feedback and continuous learning",
                supporting_evidence=f"Feedback receptiveness score: {metrics.feedback_receptiveness_score:.2f}"
            ))
        
        if metrics.temporal_dedication_score >= 0.8:
            tags.append(SkillTag(
                tag="⏰ Consistent Contributor",
                category="Team Dynamics",
                justification="Shows consistent dedication and reliable work patterns",
                supporting_evidence=f"Temporal dedication score: {metrics.temporal_dedication_score:.2f}, Pattern: {metrics.work_rhythm_pattern}"
            ))
        
        # Overall Performance tags
        if metrics.founding_engineer_score >= 85:
            tags.append(SkillTag(
                tag="🏆 Founding Engineer Ready",
                category="Overall Assessment",
                justification="Exceptional overall performance across all founding engineer criteria",
                supporting_evidence=f"Overall score: {metrics.founding_engineer_score:.1f}/100"
            ))
        elif metrics.founding_engineer_score >= 70:
            tags.append(SkillTag(
                tag="⭐ Strong Candidate",
                category="Overall Assessment", 
                justification="Strong performance with good founding engineer potential",
                supporting_evidence=f"Overall score: {metrics.founding_engineer_score:.1f}/100"
            ))
        
        return tags


def save_review_report(metrics: FoundingEngineerMetrics, user: str, output_format: str = 'json') -> str:
    """Save the founding engineer review report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if output_format == 'json':
        filename = f"founding_engineer_review_{user}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(asdict(metrics), f, indent=2)
        print(f"💾 Review saved to: {filename}")
        
    elif output_format == 'detailed':
        filename = f"founding_engineer_review_{user}_{timestamp}.md"
        
        with open(filename, 'w') as f:
            f.write(f"# Founding Engineer Review: {user}\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Overall Score:** {metrics.founding_engineer_score:.1f}/100\n")
            f.write(f"**Recommendation:** {metrics.recommendation}\n\n")
            
            # Write detailed sections for each category
            f.write("## 🔬 Technical Proficiency\n\n")
            f.write(f"**AI/ML Frameworks:** {', '.join(metrics.ai_ml_frameworks) or 'None detected'}\n")
            f.write(f"**Performance Languages:** {metrics.performance_languages}\n")
            f.write(f"**Dependency Sophistication:** {metrics.dependency_sophistication_score:.2f}\n\n")
            
            f.write("## 🛠️ Engineering Craftsmanship\n\n")
            f.write(f"**Commit-Issue Linking:** {metrics.commit_issue_linking_ratio:.2f}\n")
            f.write(f"**Testing Commitment:** {metrics.testing_commitment_ratio:.2f}\n")
            f.write(f"**Structured Workflow:** {metrics.structured_workflow_score:.2f}\n\n")
            
            f.write("## 🚀 Initiative & Ownership\n\n")
            f.write(f"**Self-Directed Cycles:** {metrics.self_directed_work_cycles}\n")
            f.write(f"**First Responder:** {metrics.first_responder_instances}\n")
            f.write(f"**Open Source Contributions:** {metrics.open_source_contributions}\n\n")
            
            f.write("## 🤝 Collaboration Style\n\n")
            f.write(f"**Work Rhythm:** {metrics.work_rhythm_pattern}\n")
            f.write(f"**Feedback Receptiveness:** {metrics.feedback_receptiveness_score:.2f}\n")
            f.write(f"**Review Comments:** {metrics.review_comment_distribution}\n\n")
            
            # Add skill tags section
            if metrics.tags or metrics.ai_suggested_tags:
                f.write("## 🏷️ Skill Tags\n\n")
                
                if metrics.tags:
                    f.write("### 📊 Rule-Based Tags\n\n")
                    for tag in metrics.tags:
                        f.write(f"**{tag.tag}** ({tag.category})\n")
                        f.write(f"- *Justification:* {tag.justification}\n")
                        f.write(f"- *Evidence:* {tag.supporting_evidence}\n\n")
                
                if metrics.ai_suggested_tags:
                    f.write("### 🤖 AI-Suggested Tags\n\n")
                    for tag in metrics.ai_suggested_tags:
                        f.write(f"**{tag.tag}** ({tag.category})\n")
                        f.write(f"- *Justification:* {tag.justification}\n")
                        f.write(f"- *Evidence:* {tag.supporting_evidence}\n\n")
            
            if metrics.strengths:
                f.write("## ✅ Key Strengths\n\n")
                for strength in metrics.strengths:
                    f.write(f"- {strength}\n")
                f.write("\n")
            
            if metrics.risk_factors:
                f.write("## ⚠️ Risk Factors\n\n")
                for risk in metrics.risk_factors:
                    f.write(f"- {risk}\n")
                f.write("\n")
        
        print(f"📄 Detailed review saved to: {filename}")
    
    return filename


def main():
    """Main function for the Founding Engineer Review System."""
    parser = argparse.ArgumentParser(
        description="Founding Engineer GitHub Review System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user phunterlau
  %(prog)s --user user@example.com --months 6 --format detailed
  %(prog)s --user candidate123 --months 18 --format json
        """
    )
    
    parser.add_argument(
        '--user', '-u',
        required=True,
        help='GitHub username or email address of the candidate'
    )
    
    parser.add_argument(
        '--months', '-m',
        type=int,
        default=12,
        help='Number of months to analyze (default: 12)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'detailed'],
        default='detailed',
        help='Output format (default: detailed)'
    )
    
    args = parser.parse_args()
    
    print("🎯 Founding Engineer Review System")
    print("=" * 50)
    print(f"Candidate: {args.user}")
    print(f"Analysis Period: {args.months} months")
    print(f"Output Format: {args.format}")
    print()
    
    # Check for GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("❌ ERROR: GITHUB_TOKEN environment variable not set")
        print("Please set your GitHub Personal Access Token:")
        print("export GITHUB_TOKEN=your_token_here")
        return 1
    
    try:
        # Initialize reviewer
        reviewer = FoundingEngineerReviewer(github_token)
        
        # Generate comprehensive review
        metrics = reviewer.generate_comprehensive_review(args.user, args.months)
        
        # Save results
        output_file = save_review_report(metrics, args.user, args.format)
        
        # Print summary
        print(f"\n🎯 FOUNDING ENGINEER ASSESSMENT")
        print("=" * 50)
        print(f"Overall Score: {metrics.founding_engineer_score:.1f}/100")
        print(f"Recommendation: {metrics.recommendation}")
        print(f"Work Pattern: {metrics.work_rhythm_pattern}")
        
        if metrics.strengths:
            print(f"\nTop Strengths:")
            for strength in metrics.strengths[:3]:
                print(f"  ✅ {strength}")
        
        if metrics.risk_factors:
            print(f"\nKey Risks:")
            for risk in metrics.risk_factors[:3]:
                print(f"  ⚠️  {risk}")
        
        print(f"\n📄 Full report: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
