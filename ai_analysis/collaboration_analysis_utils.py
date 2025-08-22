#!/usr/bin/env python3
"""
Collaboration Analysis Utilities for Enhanced Founding Engineer Review

This module provides factual collaboration analysis capabilities that replace
estimations with real data from GitHub's review and collaboration APIs.

Features:
- Real PR review comment analysis
- Factual collaboration style classification
- Review quality assessment
- Mentorship behavior detection
"""

import re
import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from github import Github
from github.GithubException import GithubException


@dataclass
class ReviewComment:
    """Represents a code review comment with analysis."""
    comment_id: int
    body: str
    author: str
    pr_url: str
    created_at: str
    classification: str  # 'suggesting', 'questioning', 'praising', 'nitpicking', 'blocking'
    sentiment_score: float  # -1.0 to 1.0
    value_score: float     # 0.0 to 1.0 (how valuable the comment is)
    evidence: str          # Why it was classified this way


@dataclass
class PRReviewAnalysis:
    """Analysis of a pull request review session."""
    pr_number: int
    pr_title: str
    repo_name: str
    reviewer: str
    review_date: str
    total_comments: int
    comment_classifications: Dict[str, int]
    overall_sentiment: float
    review_quality_score: float
    mentorship_indicators: List[str]
    blocking_issues_raised: int


class CollaborationAnalyzer:
    """Analyzes real collaboration patterns from GitHub review data."""
    
    def __init__(self, github_token: str):
        """Initialize the collaboration analyzer with GitHub API access."""
        self.g = Github(github_token)
        self.token = github_token
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Initialize classification patterns
        self._init_classification_patterns()
    
    def _init_classification_patterns(self):
        """Initialize patterns for classifying review comments."""
        
        # Suggesting (constructive feedback)
        self.suggesting_patterns = [
            r'i suggest',
            r'what if we',
            r'have you considered',
            r'maybe we could',
            r'it might be better to',
            r'consider using',
            r'you could also',
            r'another approach',
            r'alternatively',
            r'improvement:'
        ]
        
        # Questioning (curious, learning-oriented)
        self.questioning_patterns = [
            r'why did you',
            r'can you clarify',
            r'what\'s the reason',
            r'how does this',
            r'could you explain',
            r'what happens if',
            r'is there a reason',
            r'why not use',
            r'what about',
            r'curious:'
        ]
        
        # Praising (supportive, encouraging)
        self.praising_patterns = [
            r'nice work',
            r'great job',
            r'love this',
            r'excellent',
            r'brilliant',
            r'clever',
            r'good catch',
            r'well done',
            r'perfect',
            r'awesome',
            r'solid implementation',
            r'clean code',
            r'nice touch'
        ]
        
        # Nitpicking (low-value style comments)
        self.nitpicking_patterns = [
            r'^add a space',
            r'^remove trailing',
            r'^whitespace',
            r'^formatting:',
            r'^style:',
            r'^nit:',
            r'^minor:',
            r'^\s*,\s*$',  # Just a comma
            r'^\s*\.\s*$',  # Just a period
            r'^typo:',
            r'^missing comma',
            r'^extra space'
        ]
        
        # Blocking (serious issues)
        self.blocking_patterns = [
            r'this will break',
            r'security issue',
            r'performance problem',
            r'this is wrong',
            r'incorrect',
            r'bug:',
            r'critical:',
            r'this won\'t work',
            r'major issue',
            r'blocking:'
        ]
        
        # Mentorship indicators
        self.mentorship_patterns = [
            r'here\'s why',
            r'the reason is',
            r'this helps because',
            r'generally we',
            r'best practice',
            r'in the future',
            r'pro tip',
            r'keep in mind',
            r'good to know',
            r'for reference'
        ]
    
    def classify_review_comment(self, comment_body: str) -> Tuple[str, float, float, str]:
        """
        Classify a review comment into categories and assign scores.
        
        Args:
            comment_body: The text content of the review comment
            
        Returns:
            Tuple of (classification, sentiment_score, value_score, evidence)
        """
        body_lower = comment_body.lower().strip()
        
        # Initialize scores
        sentiment_score = 0.0  # -1 (negative) to 1 (positive)
        value_score = 0.5      # 0 (low value) to 1 (high value)
        evidence = ""
        
        # Check for blocking issues (highest priority)
        for pattern in self.blocking_patterns:
            if re.search(pattern, body_lower):
                return 'blocking', -0.5, 0.9, f"Contains blocking concern: {pattern}"
        
        # Check for praising (positive sentiment)
        praise_matches = []
        for pattern in self.praising_patterns:
            if re.search(pattern, body_lower):
                praise_matches.append(pattern)
        
        if praise_matches:
            sentiment_score = 0.8
            value_score = 0.6  # Praise is nice but not always high-value
            return 'praising', sentiment_score, value_score, f"Positive feedback: {praise_matches[0]}"
        
        # Check for suggesting (constructive)
        suggest_matches = []
        for pattern in self.suggesting_patterns:
            if re.search(pattern, body_lower):
                suggest_matches.append(pattern)
        
        if suggest_matches:
            sentiment_score = 0.3  # Constructive but neutral
            value_score = 0.8     # High value
            return 'suggesting', sentiment_score, value_score, f"Constructive suggestion: {suggest_matches[0]}"
        
        # Check for questioning (curious)
        question_matches = []
        for pattern in self.questioning_patterns:
            if re.search(pattern, body_lower):
                question_matches.append(pattern)
        
        if question_matches:
            sentiment_score = 0.1  # Neutral but engaging
            value_score = 0.7     # Good value for learning
            return 'questioning', sentiment_score, value_score, f"Curious questioning: {question_matches[0]}"
        
        # Check for nitpicking (low value)
        nitpick_matches = []
        for pattern in self.nitpicking_patterns:
            if re.search(pattern, body_lower):
                nitpick_matches.append(pattern)
        
        if nitpick_matches:
            sentiment_score = -0.2  # Slightly negative
            value_score = 0.2      # Low value
            return 'nitpicking', sentiment_score, value_score, f"Style nitpick: {nitpick_matches[0]}"
        
        # Default classification for unmatched comments
        if len(body_lower) < 10:
            return 'nitpicking', -0.1, 0.1, "Very short comment"
        elif len(body_lower) > 200:
            return 'suggesting', 0.2, 0.7, "Detailed explanation"
        else:
            return 'questioning', 0.0, 0.5, "General comment"
    
    def search_user_reviews(self, username: str, max_reviews: int = 20) -> List[str]:
        """
        Search for PRs that a user has reviewed using GitHub Search API.
        
        Args:
            username: GitHub username
            max_reviews: Maximum number of reviewed PRs to return
            
        Returns:
            List of PR URLs that the user has reviewed
        """
        print(f"🔍 Searching for PR reviews by {username}...")
        
        try:
            # Use GitHub Search API to find PRs reviewed by user
            search_query = f"reviewed-by:{username} is:pr"
            
            # Use requests for search API (more flexible than PyGithub for this)
            url = f"https://api.github.com/search/issues"
            params = {
                'q': search_query,
                'sort': 'updated',
                'order': 'desc',
                'per_page': min(max_reviews, 100)
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            search_results = response.json()
            
            pr_urls = []
            for item in search_results.get('items', []):
                pr_url = item.get('html_url', '')
                if pr_url and '/pull/' in pr_url:
                    pr_urls.append(pr_url)
            
            print(f"   ✅ Found {len(pr_urls)} reviewed PRs")
            return pr_urls[:max_reviews]
            
        except Exception as e:
            print(f"⚠️ Error searching for reviews: {e}")
            return []
    
    def analyze_pr_review(self, pr_url: str, reviewer_username: str) -> Optional[PRReviewAnalysis]:
        """
        Analyze a specific PR review by a user.
        
        Args:
            pr_url: URL of the pull request
            reviewer_username: Username of the reviewer
            
        Returns:
            PRReviewAnalysis object or None if analysis fails
        """
        try:
            # Extract repo and PR number from URL
            # URL format: https://github.com/owner/repo/pull/123
            parts = pr_url.replace('https://github.com/', '').split('/')
            if len(parts) >= 4 and parts[2] == 'pull':
                repo_name = f"{parts[0]}/{parts[1]}"
                pr_number = int(parts[3])
            else:
                return None
            
            # Get PR details
            pr_url_api = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
            pr_response = requests.get(pr_url_api, headers=self.headers)
            pr_response.raise_for_status()
            pr_data = pr_response.json()
            
            pr_title = pr_data.get('title', '')
            
            # Get review comments for this PR by this reviewer
            reviews_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/reviews"
            reviews_response = requests.get(reviews_url, headers=self.headers)
            reviews_response.raise_for_status()
            reviews_data = reviews_response.json()
            
            # Filter reviews by the specific reviewer
            reviewer_reviews = [r for r in reviews_data if r.get('user', {}).get('login') == reviewer_username]
            
            if not reviewer_reviews:
                return None
            
            # Get review comments
            comments_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments"
            comments_response = requests.get(comments_url, headers=self.headers)
            comments_response.raise_for_status()
            comments_data = comments_response.json()
            
            # Filter comments by the reviewer
            reviewer_comments = [c for c in comments_data if c.get('user', {}).get('login') == reviewer_username]
            
            # Analyze each comment
            analyzed_comments = []
            comment_classifications = {'suggesting': 0, 'questioning': 0, 'praising': 0, 'nitpicking': 0, 'blocking': 0}
            total_sentiment = 0.0
            total_value = 0.0
            mentorship_indicators = []
            blocking_issues = 0
            
            for comment in reviewer_comments:
                body = comment.get('body', '')
                classification, sentiment, value, evidence = self.classify_review_comment(body)
                
                analyzed_comment = ReviewComment(
                    comment_id=comment.get('id'),
                    body=body,
                    author=reviewer_username,
                    pr_url=pr_url,
                    created_at=comment.get('created_at'),
                    classification=classification,
                    sentiment_score=sentiment,
                    value_score=value,
                    evidence=evidence
                )
                
                analyzed_comments.append(analyzed_comment)
                comment_classifications[classification] += 1
                total_sentiment += sentiment
                total_value += value
                
                if classification == 'blocking':
                    blocking_issues += 1
                
                # Check for mentorship indicators
                body_lower = body.lower()
                for pattern in self.mentorship_patterns:
                    if re.search(pattern, body_lower):
                        mentorship_indicators.append(f"Mentoring: {pattern}")
                        break
            
            # Calculate overall scores
            total_comments = len(analyzed_comments)
            if total_comments > 0:
                overall_sentiment = total_sentiment / total_comments
                review_quality_score = total_value / total_comments
            else:
                overall_sentiment = 0.0
                review_quality_score = 0.0
            
            # Get the latest review date
            if reviewer_reviews:
                latest_review = max(reviewer_reviews, key=lambda r: r.get('submitted_at', ''))
                review_date = latest_review.get('submitted_at', '') if latest_review else ''
            else:
                review_date = ''
            
            return PRReviewAnalysis(
                pr_number=pr_number,
                pr_title=pr_title,
                repo_name=repo_name,
                reviewer=reviewer_username,
                review_date=review_date,
                total_comments=total_comments,
                comment_classifications=comment_classifications,
                overall_sentiment=overall_sentiment,
                review_quality_score=review_quality_score,
                mentorship_indicators=list(set(mentorship_indicators)),  # Remove duplicates
                blocking_issues_raised=blocking_issues
            )
            
        except Exception as e:
            print(f"⚠️ Error analyzing PR review {pr_url}: {e}")
            return None
    
    def analyze_user_collaboration_style(self, username: str, max_reviews: int = 15) -> Dict[str, Any]:
        """
        Analyze a user's collaboration style based on their actual review behavior.
        
        Args:
            username: GitHub username
            max_reviews: Maximum number of reviews to analyze
            
        Returns:
            Dictionary with factual collaboration metrics
        """
        print(f"🤝 Analyzing factual collaboration data for {username}...")
        
        # Find PRs reviewed by the user
        pr_urls = self.search_user_reviews(username, max_reviews)
        
        if not pr_urls:
            print(f"   ⚠️ No reviews found for {username}")
            return {
                'total_reviews_analyzed': 0,
                'factual_comment_distribution': {'suggesting': 0, 'questioning': 0, 'praising': 0, 'nitpicking': 0, 'blocking': 0},
                'avg_sentiment_score': 0.0,
                'avg_review_quality_score': 0.0,
                'mentorship_score': 0.0,
                'collaboration_style': 'Unknown',
                'review_examples': [],
                'golden_collaboration_nuggets': []
            }
        
        # Analyze each review
        analyses = []
        for pr_url in pr_urls[:max_reviews]:
            analysis = self.analyze_pr_review(pr_url, username)
            if analysis and analysis.total_comments > 0:
                analyses.append(analysis)
        
        if not analyses:
            print(f"   ⚠️ No meaningful reviews found for {username}")
            return {
                'total_reviews_analyzed': 0,
                'factual_comment_distribution': {'suggesting': 0, 'questioning': 0, 'praising': 0, 'nitpicking': 0, 'blocking': 0},
                'avg_sentiment_score': 0.0,
                'avg_review_quality_score': 0.0,
                'mentorship_score': 0.0,
                'collaboration_style': 'Unknown',
                'review_examples': [],
                'golden_collaboration_nuggets': []
            }
        
        print(f"   ✅ Analyzed {len(analyses)} meaningful reviews")
        
        # Aggregate metrics
        total_comment_dist = {'suggesting': 0, 'questioning': 0, 'praising': 0, 'nitpicking': 0, 'blocking': 0}
        total_sentiment = 0.0
        total_quality = 0.0
        total_mentorship_indicators = 0
        
        for analysis in analyses:
            for category, count in analysis.comment_classifications.items():
                total_comment_dist[category] += count
            total_sentiment += analysis.overall_sentiment
            total_quality += analysis.review_quality_score
            total_mentorship_indicators += len(analysis.mentorship_indicators)
        
        # Calculate averages
        avg_sentiment = total_sentiment / len(analyses)
        avg_quality = total_quality / len(analyses)
        mentorship_score = min(total_mentorship_indicators / len(analyses), 1.0)
        
        # Determine collaboration style
        total_comments = sum(total_comment_dist.values())
        if total_comments > 0:
            suggesting_ratio = total_comment_dist['suggesting'] / total_comments
            questioning_ratio = total_comment_dist['questioning'] / total_comments
            praising_ratio = total_comment_dist['praising'] / total_comments
            nitpicking_ratio = total_comment_dist['nitpicking'] / total_comments
            
            if suggesting_ratio >= 0.4:
                collaboration_style = 'Constructive Mentor'
            elif questioning_ratio >= 0.4:
                collaboration_style = 'Curious Learner'
            elif praising_ratio >= 0.4:
                collaboration_style = 'Supportive Teammate'
            elif nitpicking_ratio >= 0.5:
                collaboration_style = 'Detail Oriented'
            else:
                collaboration_style = 'Balanced Reviewer'
        else:
            collaboration_style = 'Unknown'
        
        # Extract examples and golden nuggets
        review_examples = []
        golden_nuggets = []
        
        for analysis in analyses[:3]:  # Top 3 examples
            review_examples.append({
                'pr_title': analysis.pr_title,
                'repo': analysis.repo_name,
                'comments': analysis.total_comments,
                'quality_score': analysis.review_quality_score,
                'style': max(analysis.comment_classifications.items(), key=lambda x: x[1])[0]
            })
            
            # High-quality reviews as golden nuggets
            if analysis.review_quality_score >= 0.7 and analysis.total_comments >= 3:
                golden_nuggets.append({
                    'type': 'high_quality_review',
                    'pr_title': analysis.pr_title,
                    'repo': analysis.repo_name,
                    'evidence': f"{analysis.total_comments} thoughtful comments",
                    'question_suggestion': f"Tell me about your review approach in '{analysis.pr_title}'"
                })
        
        return {
            'total_reviews_analyzed': len(analyses),
            'factual_comment_distribution': total_comment_dist,
            'avg_sentiment_score': avg_sentiment,
            'avg_review_quality_score': avg_quality,
            'mentorship_score': mentorship_score,
            'collaboration_style': collaboration_style,
            'review_examples': review_examples,
            'golden_collaboration_nuggets': golden_nuggets
        }


def compare_estimated_vs_factual(estimated_metrics: Dict[str, Any], factual_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare estimated collaboration metrics with factual analysis.
    
    Args:
        estimated_metrics: Original estimated metrics from the founding engineer system
        factual_metrics: Factual metrics from real review analysis
        
    Returns:
        Comparison analysis with accuracy assessment
    """
    comparison = {
        'data_quality_improvement': 'Factual data replaces estimates',
        'estimated_total_comments': sum(estimated_metrics.get('review_comment_distribution', {}).values()),
        'factual_total_comments': sum(factual_metrics.get('factual_comment_distribution', {}).values()),
        'accuracy_assessment': {},
        'key_insights': []
    }
    
    # Compare comment distributions
    estimated_dist = estimated_metrics.get('review_comment_distribution', {})
    factual_dist = factual_metrics.get('factual_comment_distribution', {})
    
    for category in ['suggesting', 'questioning', 'praising']:
        if category in estimated_dist and category in factual_dist:
            estimated_count = estimated_dist[category]
            factual_count = factual_dist[category]
            
            if estimated_count > 0:
                accuracy = 1 - abs(estimated_count - factual_count) / estimated_count
                comparison['accuracy_assessment'][category] = f"{accuracy:.2f}"
    
    # Key insights
    if factual_metrics['total_reviews_analyzed'] > 0:
        comparison['key_insights'].append(f"Found {factual_metrics['total_reviews_analyzed']} actual reviews to analyze")
        comparison['key_insights'].append(f"Collaboration style: {factual_metrics['collaboration_style']}")
        comparison['key_insights'].append(f"Review quality score: {factual_metrics['avg_review_quality_score']:.2f}/1.0")
    else:
        comparison['key_insights'].append("No review data found - candidate may not actively review code")
    
    return comparison
