"""
Report Generation System

This module provides various report formats for presenting founding engineer assessments
in different contexts (executive summary, detailed analysis, JSON export, etc.).
"""

import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from ..models.assessment import AssessmentResult, RiskLevel, StrengthCategory


class ReportGenerator:
    """Generates various report formats for founding engineer assessments."""
    
    def __init__(self):
        """Initialize report generator."""
        self.templates = self._init_templates()
    
    def _init_templates(self):
        """Initialize report templates and formatting."""
        return {
            'risk_emoji': {
                RiskLevel.CRITICAL: '🚨',
                RiskLevel.HIGH: '⚠️',
                RiskLevel.MEDIUM: '🔶',
                RiskLevel.LOW: '💡'
            },
            'strength_emoji': {
                StrengthCategory.TECHNICAL_EXCELLENCE: '🔬',
                StrengthCategory.LEADERSHIP_POTENTIAL: '👑',
                StrengthCategory.PRODUCT_MINDSET: '🚀',
                StrengthCategory.COLLABORATION_SKILLS: '🤝',
                StrengthCategory.LEARNING_AGILITY: '📚',
                StrengthCategory.EXECUTION_FOCUS: '⚡'
            }
        }
    
    def generate_executive_summary(self, assessment: AssessmentResult) -> str:
        """
        Generate a concise executive summary for leadership.
        
        Args:
            assessment: Complete assessment result
            
        Returns:
            Executive summary as markdown string
        """
        lines = []
        
        # Header
        lines.append(f"# Executive Summary: {assessment.candidate_username}")
        lines.append(f"**Generated:** {assessment.analysis_timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Analysis Period:** {assessment.analysis_period_months} months")
        lines.append("")
        
        # Key metrics box
        lines.append("## 📊 Key Metrics")
        lines.append("```")
        lines.append(f"Overall Score:     {assessment.overall_score:.1f}/100")
        lines.append(f"Recommendation:    {assessment.recommendation.value}")
        lines.append(f"Confidence Level:  {assessment.confidence_level:.0%}")
        lines.append("```")
        lines.append("")
        
        # Executive summary
        lines.append("## 🎯 Assessment Summary")
        lines.append(assessment.executive_summary)
        lines.append("")
        
        # Top strengths (max 3)
        if assessment.top_strengths:
            lines.append("## ✅ Key Strengths")
            for i, strength in enumerate(assessment.top_strengths[:3], 1):
                emoji = self.templates['strength_emoji'].get(strength.category, '✅')
                lines.append(f"{i}. {emoji} **{strength.description}**")
                lines.append(f"   *{strength.impact_potential}*")
            lines.append("")
        
        # Critical risks
        if assessment.critical_risks:
            lines.append("## ⚠️ Key Risks")
            for i, risk in enumerate(assessment.critical_risks[:3], 1):
                emoji = self.templates['risk_emoji'].get(risk.severity, '⚠️')
                lines.append(f"{i}. {emoji} **{risk.description}**")
                lines.append(f"   *{risk.impact_description}*")
            lines.append("")
        
        # Hiring recommendation
        lines.append("## 💼 Hiring Recommendation")
        lines.append(assessment.hiring_recommendation)
        
        if assessment.next_steps:
            lines.append("")
            lines.append("**Next Steps:**")
            for step in assessment.next_steps:
                lines.append(f"- {step}")
        
        return "\n".join(lines)
    
    def generate_detailed_report(self, assessment: AssessmentResult) -> str:
        """
        Generate a comprehensive detailed report.
        
        Args:
            assessment: Complete assessment result
            
        Returns:
            Detailed report as markdown string
        """
        lines = []
        
        # Header
        lines.append(f"# Founding Engineer Assessment: {assessment.candidate_username}")
        lines.append(f"**Generated:** {assessment.analysis_timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Analysis Period:** {assessment.analysis_period_months} months")
        lines.append(f"**Data Sources:** {', '.join(assessment.data_sources_used)}")
        lines.append(f"**Analysis Completeness:** {assessment.analysis_completeness:.0%}")
        lines.append("")
        
        # Overall assessment
        lines.append("## 🎯 Overall Assessment")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| **Overall Score** | {assessment.overall_score:.1f}/100 |")
        lines.append(f"| **Recommendation** | {assessment.recommendation.value} |")
        lines.append(f"| **Confidence Level** | {assessment.confidence_level:.0%} |")
        lines.append("")
        lines.append(assessment.executive_summary)
        lines.append("")
        
        # Category breakdown
        lines.append("## 📈 Category Analysis")
        lines.append("")
        
        for category_name, category_assessment in assessment.category_assessments.items():
            lines.append(f"### {category_name}")
            lines.append(f"**Score:** {category_assessment.score:.1f}/100")
            lines.append("")
            
            # Strengths for this category
            if category_assessment.strengths:
                lines.append("**Strengths:**")
                for strength in category_assessment.strengths:
                    emoji = self.templates['strength_emoji'].get(strength.category, '✅')
                    lines.append(f"- {emoji} {strength.description}")
                    if strength.supporting_evidence:
                        lines.append(f"  - Evidence: {', '.join(strength.supporting_evidence[:3])}")
                lines.append("")
            
            # Risk factors for this category
            if category_assessment.risk_factors:
                lines.append("**Risk Factors:**")
                for risk in category_assessment.risk_factors:
                    emoji = self.templates['risk_emoji'].get(risk.severity, '⚠️')
                    lines.append(f"- {emoji} {risk.description}")
                    if risk.mitigation_suggestions:
                        lines.append(f"  - Mitigation: {risk.mitigation_suggestions[0]}")
                lines.append("")
            
            # Key insights
            if category_assessment.key_insights:
                lines.append("**Key Insights:**")
                for insight in category_assessment.key_insights:
                    lines.append(f"- {insight}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # All strengths
        if assessment.top_strengths:
            lines.append("## ✅ Complete Strengths Analysis")
            lines.append("")
            for i, strength in enumerate(assessment.top_strengths, 1):
                emoji = self.templates['strength_emoji'].get(strength.category, '✅')
                lines.append(f"### {i}. {emoji} {strength.description}")
                lines.append(f"**Category:** {strength.category.value}")
                lines.append(f"**Impact:** {strength.impact_potential}")
                lines.append(f"**Confidence:** {strength.confidence:.0%}")
                
                if strength.supporting_evidence:
                    lines.append("**Evidence:**")
                    for evidence in strength.supporting_evidence:
                        lines.append(f"- {evidence}")
                lines.append("")
        
        # All risks
        if assessment.critical_risks:
            lines.append("## ⚠️ Risk Analysis")
            lines.append("")
            for i, risk in enumerate(assessment.critical_risks, 1):
                emoji = self.templates['risk_emoji'].get(risk.severity, '⚠️')
                lines.append(f"### {i}. {emoji} {risk.description}")
                lines.append(f"**Severity:** {risk.severity.value}")
                lines.append(f"**Impact:** {risk.impact_description}")
                lines.append(f"**Confidence:** {risk.confidence:.0%}")
                
                if risk.mitigation_suggestions:
                    lines.append("**Mitigation Strategies:**")
                    for suggestion in risk.mitigation_suggestions:
                        lines.append(f"- {suggestion}")
                lines.append("")
        
        # Detailed metrics (if available)
        if assessment.detailed_metrics:
            lines.append("## 📊 Detailed Metrics")
            lines.append("")
            
            # Technical proficiency details
            tech = assessment.detailed_metrics.technical_proficiency
            lines.append("### 🔬 Technical Proficiency")
            lines.append(f"**AI/ML Frameworks:** {', '.join(tech.ai_ml_frameworks) if tech.ai_ml_frameworks else 'None detected'}")
            lines.append(f"**Performance Languages:** {dict(tech.performance_languages) if tech.performance_languages else 'None'}")
            lines.append(f"**Dependency Sophistication:** {tech.dependency_sophistication_score:.2f}")
            lines.append("")
            
            # Engineering craftsmanship details
            craft = assessment.detailed_metrics.engineering_craftsmanship
            lines.append("### 🛠️ Engineering Craftsmanship")
            lines.append(f"**Commit-Issue Linking:** {craft.commit_issue_linking_ratio:.1%}")
            lines.append(f"**Testing Commitment:** {craft.testing_commitment_ratio:.1%}")
            lines.append(f"**Structured Workflow:** {craft.structured_workflow_score:.2f}")
            lines.append("")
            
            # Initiative & ownership details
            initiative = assessment.detailed_metrics.initiative_ownership
            lines.append("### 🚀 Initiative & Ownership")
            lines.append(f"**Self-Directed Cycles:** {initiative.self_directed_work_cycles}")
            lines.append(f"**First Responder Instances:** {initiative.first_responder_instances}")
            lines.append(f"**Personal Project Quality:** {initiative.personal_project_quality:.2f}")
            lines.append(f"**OSS Contributions:** {initiative.open_source_contributions}")
            lines.append("")
            
            # Collaboration style details
            collab = assessment.detailed_metrics.collaboration_style
            lines.append("### 🤝 Collaboration Style")
            lines.append(f"**Work Rhythm:** {collab.work_rhythm_pattern.value}")
            lines.append(f"**Feedback Receptiveness:** {collab.feedback_receptiveness_score:.2f}")
            lines.append(f"**Temporal Dedication:** {collab.temporal_dedication_score:.2f}")
            lines.append("")
        
        # Final recommendation
        lines.append("## 💼 Final Recommendation")
        lines.append("")
        lines.append(f"**{assessment.recommendation.value}**")
        lines.append("")
        lines.append(assessment.hiring_recommendation)
        
        return "\n".join(lines)
    
    def generate_json_export(self, assessment: AssessmentResult) -> str:
        """
        Generate JSON export of the complete assessment.
        
        Args:
            assessment: Complete assessment result
            
        Returns:
            JSON string of the assessment
        """
        # Create a safe dictionary representation
        def safe_serialize(obj):
            """Safely serialize objects, avoiding recursion."""
            if obj is None:
                return None
            elif isinstance(obj, (str, int, float, bool)):
                return obj
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            elif isinstance(obj, list):
                return [safe_serialize(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: safe_serialize(v) for k, v in obj.items()}
            else:
                # For dataclass objects, manually extract key fields
                return str(obj)
        
        assessment_dict = {
            'candidate_username': assessment.candidate_username,
            'overall_score': assessment.overall_score,
            'recommendation': safe_serialize(assessment.recommendation),
            'confidence_level': assessment.confidence_level,
            'executive_summary': assessment.executive_summary,
            'hiring_recommendation': assessment.hiring_recommendation,
            'analysis_timestamp': safe_serialize(assessment.analysis_timestamp),
            'analysis_period_months': assessment.analysis_period_months,
            'category_scores': safe_serialize(getattr(assessment, 'category_scores', {})),
            'data_sources_used': assessment.data_sources_used,
            'analysis_completeness': assessment.analysis_completeness
        }
        
        # Add category assessments if they exist
        if hasattr(assessment, 'category_assessments') and assessment.category_assessments:
            assessment_dict['category_assessments'] = {}
            for name, cat in assessment.category_assessments.items():
                assessment_dict['category_assessments'][name] = {
                    'score': cat.score,
                    'strengths': [
                        {
                            'description': s.description,
                            'confidence': s.confidence,
                            'category': safe_serialize(getattr(s, 'category', None))
                        } for s in cat.strengths
                    ],
                    'risks': [
                        {
                            'description': r.description,
                            'severity': safe_serialize(getattr(r, 'severity', None)),
                            'confidence': getattr(r, 'confidence', 0.0)
                        } for r in cat.risks
                    ],
                    'key_findings': cat.key_findings if hasattr(cat, 'key_findings') else []
                }
        
        # Add top strengths if they exist
        if hasattr(assessment, 'top_strengths') and assessment.top_strengths:
            assessment_dict['top_strengths'] = [
                {
                    'category': safe_serialize(getattr(s, 'category', None)),
                    'description': s.description,
                    'supporting_evidence': getattr(s, 'supporting_evidence', []),
                    'impact_potential': getattr(s, 'impact_potential', ''),
                    'confidence': s.confidence
                }
                for s in assessment.top_strengths
            ]
        
        # Add critical risks if they exist
        if hasattr(assessment, 'critical_risks') and assessment.critical_risks:
            assessment_dict['critical_risks'] = [
                {
                    'category': getattr(r, 'category', 'Unknown'),
                    'description': r.description,
                    'severity': safe_serialize(getattr(r, 'severity', None)),
                    'impact_description': getattr(r, 'impact_description', ''),
                    'confidence': getattr(r, 'confidence', 0.0)
                }
                for r in assessment.critical_risks
            ]
        
        return json.dumps(assessment_dict, indent=2, ensure_ascii=False)
    
    def save_report(self, assessment: AssessmentResult, output_format: str = 'detailed', 
                   output_dir: str = '.') -> str:
        """
        Save assessment report to file.
        
        Args:
            assessment: Complete assessment result
            output_format: Format type ('executive', 'detailed', 'json')
            output_dir: Output directory
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        username = assessment.candidate_username
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        if output_format == 'executive':
            content = self.generate_executive_summary(assessment)
            filename = f"founding_engineer_executive_{username}_{timestamp}.md"
            
        elif output_format == 'detailed':
            content = self.generate_detailed_report(assessment)
            filename = f"founding_engineer_detailed_{username}_{timestamp}.md"
            
        elif output_format == 'json':
            content = self.generate_json_export(assessment)
            filename = f"founding_engineer_data_{username}_{timestamp}.json"
            
        else:
            raise ValueError(f"Unknown output format: {output_format}")
        
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Report saved: {file_path}")
        
        return str(file_path)
    
    def generate_comparison_report(self, assessments: List[AssessmentResult]) -> str:
        """
        Generate a comparison report for multiple candidates.
        
        Args:
            assessments: List of assessment results to compare
            
        Returns:
            Comparison report as markdown string
        """
        if not assessments:
            return "No assessments provided for comparison."
        
        lines = []
        
        # Header
        lines.append("# Founding Engineer Candidate Comparison")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"**Candidates:** {len(assessments)}")
        lines.append("")
        
        # Summary table
        lines.append("## 📊 Candidate Summary")
        lines.append("")
        lines.append("| Candidate | Overall Score | Recommendation | Confidence |")
        lines.append("|-----------|---------------|----------------|------------|")
        
        for assessment in sorted(assessments, key=lambda a: a.overall_score, reverse=True):
            lines.append(
                f"| {assessment.candidate_username} | "
                f"{assessment.overall_score:.1f}/100 | "
                f"{assessment.recommendation.value} | "
                f"{assessment.confidence_level:.0%} |"
            )
        lines.append("")
        
        # Category comparison
        lines.append("## 📈 Category Comparison")
        lines.append("")
        
        categories = ["Technical Proficiency", "Engineering Craftsmanship", "Initiative & Ownership", "Collaboration Style"]
        
        for category in categories:
            lines.append(f"### {category}")
            lines.append("")
            lines.append("| Candidate | Score | Key Strength |")
            lines.append("|-----------|-------|--------------|")
            
            for assessment in sorted(assessments, key=lambda a: a.category_assessments.get(category, type('obj', (object,), {'score': 0})).score, reverse=True):
                cat_assessment = assessment.category_assessments.get(category)
                if cat_assessment:
                    key_strength = cat_assessment.strengths[0].description if cat_assessment.strengths else "None identified"
                    if len(key_strength) > 50:
                        key_strength = key_strength[:47] + "..."
                    lines.append(f"| {assessment.candidate_username} | {cat_assessment.score:.1f} | {key_strength} |")
            lines.append("")
        
        # Top performers by category
        lines.append("## 🏆 Top Performers by Category")
        lines.append("")
        
        for category in categories:
            top_candidate = max(assessments, 
                              key=lambda a: a.category_assessments.get(category, type('obj', (object,), {'score': 0})).score)
            top_score = top_candidate.category_assessments.get(category).score
            
            lines.append(f"**{category}:** {top_candidate.candidate_username} ({top_score:.1f}/100)")
        
        lines.append("")
        
        # Overall recommendations
        lines.append("## 💼 Overall Recommendations")
        lines.append("")
        
        strongly_recommended = [a for a in assessments if a.recommendation.value == "Strongly Recommended"]
        recommended = [a for a in assessments if a.recommendation.value == "Recommended"]
        conditional = [a for a in assessments if a.recommendation.value == "Conditional"]
        
        if strongly_recommended:
            lines.append("### 🌟 Strongly Recommended")
            for assessment in strongly_recommended:
                lines.append(f"- **{assessment.candidate_username}** ({assessment.overall_score:.1f}/100)")
            lines.append("")
        
        if recommended:
            lines.append("### ✅ Recommended")
            for assessment in recommended:
                lines.append(f"- **{assessment.candidate_username}** ({assessment.overall_score:.1f}/100)")
            lines.append("")
        
        if conditional:
            lines.append("### 🔶 Conditional")
            for assessment in conditional:
                lines.append(f"- **{assessment.candidate_username}** ({assessment.overall_score:.1f}/100)")
            lines.append("")
        
        return "\n".join(lines)
