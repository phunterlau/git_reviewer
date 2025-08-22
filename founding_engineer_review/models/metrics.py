"""
Data models for the Founding Engineer Review System.

This module contains all the core data structures used throughout the system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class WorkRhythmPattern(Enum):
    """Enumeration of work rhythm patterns."""
    WEEKEND_WARRIOR = "Weekend Warrior"
    NIGHT_OWL = "Night Owl"
    NINE_TO_FIVE = "9-to-5"
    EARLY_BIRD = "Early Bird"
    IRREGULAR = "Irregular"
    UNKNOWN = "Unknown"


class RecommendationLevel(Enum):
    """Enumeration of recommendation levels."""
    STRONGLY_RECOMMENDED = "Strongly Recommended"
    RECOMMENDED = "Recommended"
    CONDITIONAL = "Conditional"
    NOT_RECOMMENDED = "Not Recommended"
    INSUFFICIENT_DATA = "Insufficient Data"


@dataclass
class TechnicalProficiencyMetrics:
    """Metrics for Category 1: Core AI/ML Technical Proficiency."""
    
    ai_ml_frameworks: List[str] = field(default_factory=list)
    performance_languages: Dict[str, int] = field(default_factory=dict)  # language -> line count
    full_stack_evidence: List[str] = field(default_factory=list)
    dependency_sophistication_score: float = 0.0
    code_complexity_indicators: List[str] = field(default_factory=list)
    
    # Advanced metrics
    advanced_library_usage: Dict[str, int] = field(default_factory=dict)  # library -> usage count
    infrastructure_as_code_evidence: List[str] = field(default_factory=list)
    production_readiness_signals: List[str] = field(default_factory=list)


@dataclass
class EngineeringCraftsmanshipMetrics:
    """Metrics for Category 2: Problem-Solving & Engineering Craftsmanship."""
    
    commit_issue_linking_ratio: float = 0.0
    pr_turnaround_times: Dict[str, float] = field(default_factory=dict)  # size -> avg hours
    testing_commitment_ratio: float = 0.0
    structured_workflow_score: float = 0.0
    
    # Additional metrics
    code_review_thoroughness: float = 0.0
    documentation_quality_score: float = 0.0
    error_handling_patterns: List[str] = field(default_factory=list)
    performance_optimization_evidence: List[str] = field(default_factory=list)


@dataclass 
class InitiativeOwnershipMetrics:
    """Metrics for Category 3: Initiative, Curiosity & Product Sense."""
    
    self_directed_work_cycles: int = 0
    first_responder_instances: int = 0
    personal_project_quality: float = 0.0
    open_source_contributions: int = 0
    ownership_indicators: List[str] = field(default_factory=list)
    
    # Enhanced metrics
    problem_identification_score: float = 0.0
    solution_creativity_indicators: List[str] = field(default_factory=list)
    project_leadership_evidence: List[str] = field(default_factory=list)
    learning_trajectory_indicators: List[str] = field(default_factory=list)


@dataclass
class CollaborationStyleMetrics:
    """Metrics for Category 4: Collaboration & Communication Style."""
    
    review_comment_distribution: Dict[str, int] = field(default_factory=dict)  # type -> count
    feedback_receptiveness_score: float = 0.0
    work_rhythm_pattern: WorkRhythmPattern = WorkRhythmPattern.UNKNOWN
    temporal_dedication_score: float = 0.0
    
    # Enhanced metrics  
    mentorship_indicators: List[str] = field(default_factory=list)
    conflict_resolution_evidence: List[str] = field(default_factory=list)
    team_contribution_quality: float = 0.0
    communication_clarity_score: float = 0.0


@dataclass
class FoundingEngineerMetrics:
    """Comprehensive metrics for evaluating a founding engineer candidate."""
    
    # Core category metrics
    technical_proficiency: TechnicalProficiencyMetrics = field(default_factory=TechnicalProficiencyMetrics)
    engineering_craftsmanship: EngineeringCraftsmanshipMetrics = field(default_factory=EngineeringCraftsmanshipMetrics)
    initiative_ownership: InitiativeOwnershipMetrics = field(default_factory=InitiativeOwnershipMetrics)
    collaboration_style: CollaborationStyleMetrics = field(default_factory=CollaborationStyleMetrics)
    
    # Overall assessment
    founding_engineer_score: float = 0.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    risk_factors: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    recommendation: RecommendationLevel = RecommendationLevel.INSUFFICIENT_DATA
    confidence_level: float = 0.0
    
    # Metadata
    user_analyzed: str = ""
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analysis_period_months: int = 12
    data_completeness_score: float = 0.0


@dataclass
class ActivityData:
    """Raw activity data from GitHub API."""
    
    commits: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    pull_requests: List[Dict[str, Any]] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    reviews: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Processed data
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    repository_involvement: Dict[str, int] = field(default_factory=dict)
    
    # Metadata
    collection_timestamp: datetime = field(default_factory=datetime.now)
    total_activities: int = 0
