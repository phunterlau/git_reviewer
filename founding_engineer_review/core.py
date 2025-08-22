"""
Core Founding Engineer Review System

This module provides the main FoundingEngineerReviewer class that orchestrates
the entire analysis pipeline from data collection to final assessment.
"""

import os
from datetime import datetime
from typing import Optional

from .data_sources import GitHubDataSource
from .analyzers import (
    TechnicalProficiencyAnalyzer,
    EngineeringCraftsmanshipAnalyzer,
    InitiativeOwnershipAnalyzer,
    CollaborationStyleAnalyzer
)
from .scoring import FoundingEngineerScorer
from .models.metrics import FoundingEngineerMetrics
from .models.assessment import AssessmentResult


class FoundingEngineerReviewer:
    """
    Main class that orchestrates the complete founding engineer review process.
    
    This class provides a clean interface for evaluating GitHub profiles and
    generating comprehensive founding engineer assessments.
    """
    
    def __init__(self, github_token: str):
        """
        Initialize the reviewer with GitHub API access.
        
        Args:
            github_token: GitHub Personal Access Token
            
        Raises:
            ValueError: If github_token is not provided
        """
        if not github_token:
            raise ValueError("GitHub token is required")
        
        # Initialize components
        self.data_source = GitHubDataSource(github_token)
        self.tech_analyzer = TechnicalProficiencyAnalyzer()
        self.craft_analyzer = EngineeringCraftsmanshipAnalyzer()
        self.initiative_analyzer = InitiativeOwnershipAnalyzer()
        self.collab_analyzer = CollaborationStyleAnalyzer()
        self.scorer = FoundingEngineerScorer()
        
        print("✅ Founding Engineer Reviewer initialized")
    
    def resolve_user_login(self, user_identifier: str) -> Optional[str]:
        """
        Resolve email or username to GitHub login.
        
        Args:
            user_identifier: GitHub username or email
            
        Returns:
            GitHub username or None if not found
        """
        return self.data_source.resolve_user_login(user_identifier)
    
    def collect_activity_data(self, user_identifier: str, months: int = 12, include_patches: bool = False):
        """
        Collect comprehensive GitHub activity data for analysis.
        
        Args:
            user_identifier: GitHub username or email
            months: Number of months to analyze
            include_patches: Whether to include code patches (increases data size)
            
        Returns:
            ActivityData object with all collected information
        """
        print(f"📊 Collecting activity data for {user_identifier}")
        
        activity_data = self.data_source.collect_comprehensive_activity(
            user_identifier, months, include_patches
        )
        
        return activity_data
    
    def analyze_technical_proficiency(self, activity_data):
        """Analyze Category 1: Technical Proficiency."""
        return self.tech_analyzer.analyze(activity_data)
    
    def analyze_engineering_craftsmanship(self, activity_data):
        """Analyze Category 2: Engineering Craftsmanship."""
        return self.craft_analyzer.analyze(activity_data)
    
    def analyze_initiative_ownership(self, activity_data):
        """Analyze Category 3: Initiative & Ownership."""
        return self.initiative_analyzer.analyze(activity_data)
    
    def analyze_collaboration_style(self, activity_data):
        """Analyze Category 4: Collaboration Style."""
        return self.collab_analyzer.analyze(activity_data)
    
    def generate_comprehensive_review(self, user_identifier: str, months: int = 12, 
                                    include_patches: bool = False) -> AssessmentResult:
        """
        Generate a comprehensive founding engineer review.
        
        Args:
            user_identifier: GitHub username or email
            months: Number of months to analyze (default: 12)
            include_patches: Whether to include code patches for detailed analysis
            
        Returns:
            Complete AssessmentResult with all analysis and scoring
            
        Raises:
            ValueError: If user cannot be resolved or no data found
        """
        print(f"🎯 Starting Comprehensive Founding Engineer Review")
        print(f"🔍 Candidate: {user_identifier}")
        print(f"📅 Analysis Period: {months} months")
        print(f"🔧 Include Patches: {include_patches}")
        print("=" * 70)
        
        # Step 1: Collect activity data
        activity_data = self.collect_activity_data(user_identifier, months, include_patches)
        
        if activity_data.total_activities == 0:
            raise ValueError(f"No GitHub activity found for {user_identifier} in the last {months} months")
        
        username = self.resolve_user_login(user_identifier)
        if not username:
            raise ValueError(f"Could not resolve user: {user_identifier}")
        
        print(f"\n🔬 Running Four-Category Analysis...")
        print("=" * 50)
        
        # Step 2: Run all four category analyses
        tech_metrics = self.analyze_technical_proficiency(activity_data)
        craft_metrics = self.analyze_engineering_craftsmanship(activity_data)
        initiative_metrics = self.analyze_initiative_ownership(activity_data)
        collab_metrics = self.analyze_collaboration_style(activity_data)
        
        # Step 3: Create comprehensive metrics object
        comprehensive_metrics = FoundingEngineerMetrics(
            technical_proficiency=tech_metrics,
            engineering_craftsmanship=craft_metrics,
            initiative_ownership=initiative_metrics,
            collaboration_style=collab_metrics,
            user_analyzed=username,
            analysis_timestamp=datetime.now(),
            analysis_period_months=months,
            data_completeness_score=self._calculate_data_completeness(activity_data)
        )
        
        print(f"\n📊 Generating Assessment & Scoring...")
        print("=" * 50)
        
        # Step 4: Generate comprehensive assessment with scoring
        assessment_result = self.scorer.score_comprehensive_assessment(
            comprehensive_metrics, activity_data.total_activities
        )
        
        # Step 5: Add data source information
        assessment_result.data_sources_used = ["GitHub API"]
        assessment_result.analysis_completeness = comprehensive_metrics.data_completeness_score
        
        print(f"\n🎯 Review Complete!")
        print("=" * 30)
        
        return assessment_result
    
    def _calculate_data_completeness(self, activity_data) -> float:
        """
        Calculate data completeness score based on available activity types.
        
        Args:
            activity_data: ActivityData object
            
        Returns:
            Data completeness score (0-1)
        """
        completeness_factors = []
        
        # Check availability of different data types
        if activity_data.commits:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        if activity_data.issues:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.5)  # Issues are less critical
        
        if activity_data.pull_requests:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.3)
        
        if activity_data.reviews:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.3)
        
        if activity_data.comments:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.2)
        
        # Volume factor - more activities = higher completeness confidence
        if activity_data.total_activities >= 50:
            volume_factor = 1.0
        elif activity_data.total_activities >= 20:
            volume_factor = 0.8
        elif activity_data.total_activities >= 10:
            volume_factor = 0.6
        else:
            volume_factor = 0.4
        
        # Calculate weighted completeness
        data_type_completeness = sum(completeness_factors) / len(completeness_factors)
        overall_completeness = (data_type_completeness * 0.7) + (volume_factor * 0.3)
        
        return overall_completeness
    
    @staticmethod
    def create_from_env() -> 'FoundingEngineerReviewer':
        """
        Create reviewer instance using GITHUB_TOKEN environment variable.
        
        Returns:
            FoundingEngineerReviewer instance
            
        Raises:
            ValueError: If GITHUB_TOKEN environment variable is not set
        """
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError(
                "GITHUB_TOKEN environment variable not set. "
                "Please set your GitHub Personal Access Token: "
                "export GITHUB_TOKEN=your_token_here"
            )
        
        return FoundingEngineerReviewer(github_token)
