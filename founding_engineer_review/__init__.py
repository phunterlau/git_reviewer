"""
Founding Engineer Review System

A comprehensive system for evaluating potential founding engineers by analyzing
their GitHub activity patterns, technical proficiency, collaboration style, and ownership mentality.

This package implements the "Founder's Engineering Review Plan" with a modular,
maintainable architecture designed for extensibility and testing.
"""

from .core import FoundingEngineerReviewer
from .models.metrics import FoundingEngineerMetrics
from .models.assessment import AssessmentResult
from .reports import ReportGenerator

__version__ = "0.1.0"
__author__ = "Founding Engineer Review Team"

__all__ = [
    "FoundingEngineerReviewer",
    "FoundingEngineerMetrics", 
    "AssessmentResult",
    "ReportGenerator"
]
