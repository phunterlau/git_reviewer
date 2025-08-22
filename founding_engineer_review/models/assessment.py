"""
Assessment models for the Founding Engineer Review System.

This module contains assessment-specific data structures and results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .metrics import RecommendationLevel, FoundingEngineerMetrics


class RiskLevel(Enum):
    """Enumeration of risk levels."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class StrengthCategory(Enum):
    """Enumeration of strength categories."""
    TECHNICAL_EXCELLENCE = "Technical Excellence"
    LEADERSHIP_POTENTIAL = "Leadership Potential"  
    PRODUCT_MINDSET = "Product Mindset"
    COLLABORATION_SKILLS = "Collaboration Skills"
    LEARNING_AGILITY = "Learning Agility"
    EXECUTION_FOCUS = "Execution Focus"


@dataclass
class RiskFactor:
    """Individual risk factor with severity and mitigation suggestions."""
    
    category: str
    description: str
    severity: RiskLevel
    impact_description: str
    mitigation_suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Strength:
    """Individual strength with supporting evidence."""
    
    category: StrengthCategory
    description: str
    supporting_evidence: List[str] = field(default_factory=list)
    impact_potential: str = ""
    confidence: float = 0.0


@dataclass
class CategoryAssessment:
    """Assessment for a specific category."""
    
    category_name: str
    score: float
    max_score: float
    strengths: List[Strength] = field(default_factory=list)
    risk_factors: List[RiskFactor] = field(default_factory=list)
    key_insights: List[str] = field(default_factory=list)
    data_quality: float = 0.0
    confidence: float = 0.0


@dataclass
class AssessmentResult:
    """Complete assessment result for a founding engineer candidate."""
    
    # Core information
    candidate_username: str
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    analysis_period_months: int = 12
    
    # Assessment results
    overall_score: float = 0.0
    recommendation: RecommendationLevel = RecommendationLevel.INSUFFICIENT_DATA
    confidence_level: float = 0.0
    
    # Category assessments
    category_assessments: Dict[str, CategoryAssessment] = field(default_factory=dict)
    
    # Aggregated results
    top_strengths: List[Strength] = field(default_factory=list)
    critical_risks: List[RiskFactor] = field(default_factory=list)
    
    # Detailed metrics
    detailed_metrics: Optional[FoundingEngineerMetrics] = None
    
    # Executive summary
    executive_summary: str = ""
    hiring_recommendation: str = ""
    next_steps: List[str] = field(default_factory=list)
    
    # Metadata
    data_sources_used: List[str] = field(default_factory=list)
    analysis_completeness: float = 0.0
