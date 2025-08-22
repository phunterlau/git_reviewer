"""
Founding Engineer Scoring System

Implements sophisticated scoring algorithms to evaluate founding engineer potential
based on the four analysis categories and overall assessment criteria.
"""

from typing import Dict, List, Tuple, Any
from dataclasses import asdict

from ..models.metrics import (
    FoundingEngineerMetrics,
    TechnicalProficiencyMetrics,
    EngineeringCraftsmanshipMetrics,
    InitiativeOwnershipMetrics,
    CollaborationStyleMetrics,
    WorkRhythmPattern,
    RecommendationLevel
)
from ..models.assessment import (
    AssessmentResult,
    CategoryAssessment,
    RiskFactor,
    Strength,
    RiskLevel,
    StrengthCategory
)


class FoundingEngineerScorer:
    """Sophisticated scoring system for founding engineer assessment."""
    
    def __init__(self):
        """Initialize scorer with weights and thresholds."""
        self._init_scoring_parameters()
    
    def _init_scoring_parameters(self):
        """Initialize scoring weights and thresholds."""
        
        # Category weights for overall score
        self.category_weights = {
            'technical_proficiency': 0.30,
            'engineering_craftsmanship': 0.25,
            'initiative_ownership': 0.30,
            'collaboration_style': 0.15
        }
        
        # Scoring thresholds for recommendations
        self.recommendation_thresholds = {
            RecommendationLevel.STRONGLY_RECOMMENDED: 80.0,
            RecommendationLevel.RECOMMENDED: 65.0,
            RecommendationLevel.CONDITIONAL: 45.0,
            RecommendationLevel.NOT_RECOMMENDED: 0.0
        }
        
        # Risk factor thresholds
        self.risk_thresholds = {
            'low_activity': 10,  # Minimum activities for reliable assessment
            'no_ai_experience': 0,  # No AI/ML frameworks
            'poor_testing': 0.2,  # Below 20% testing commitment
            'no_collaboration': 2,  # Fewer than 2 reviews/comments
            'irregular_schedule': 0.3  # Very low temporal dedication
        }
        
        # Strength indicators
        self.strength_indicators = {
            'ai_expertise_threshold': 3,  # 3+ AI frameworks
            'performance_code_threshold': 500,  # 500+ lines performance languages
            'high_ownership_threshold': 5,  # 5+ self-directed cycles
            'mentor_threshold': 0.3,  # 30%+ helpful comments
            'dedication_threshold': 0.7  # High temporal dedication
        }
    
    def score_technical_proficiency(self, metrics: TechnicalProficiencyMetrics) -> Tuple[float, List[Strength], List[RiskFactor]]:
        """
        Score Category 1: Technical Proficiency.
        
        Args:
            metrics: Technical proficiency metrics
            
        Returns:
            Tuple of (score, strengths, risk_factors)
        """
        score = 0.0
        strengths = []
        risk_factors = []
        
        # AI/ML Framework expertise (40% of category score)
        ai_frameworks_count = len(metrics.ai_ml_frameworks)
        if ai_frameworks_count >= 5:
            score += 40
            strengths.append(Strength(
                category=StrengthCategory.TECHNICAL_EXCELLENCE,
                description=f"Extensive AI/ML expertise with {ai_frameworks_count} frameworks",
                supporting_evidence=metrics.ai_ml_frameworks[:5],
                impact_potential="Can architect sophisticated AI systems",
                confidence=0.9
            ))
        elif ai_frameworks_count >= 3:
            score += 30
            strengths.append(Strength(
                category=StrengthCategory.TECHNICAL_EXCELLENCE,
                description=f"Solid AI/ML foundation with {ai_frameworks_count} frameworks",
                supporting_evidence=metrics.ai_ml_frameworks,
                impact_potential="Can build production AI applications",
                confidence=0.8
            ))
        elif ai_frameworks_count >= 1:
            score += 20
        else:
            risk_factors.append(RiskFactor(
                category="Technical Proficiency",
                description="No evidence of AI/ML framework experience",
                severity=RiskLevel.HIGH,
                impact_description="May lack core technical skills for AI startup",
                mitigation_suggestions=["Verify AI experience through interview", "Consider technical assessment"],
                confidence=0.8
            ))
        
        # Performance language proficiency (25% of category score)
        total_perf_lines = sum(metrics.performance_languages.values())
        if total_perf_lines >= 2000:
            score += 25
            strengths.append(Strength(
                category=StrengthCategory.TECHNICAL_EXCELLENCE,
                description="Strong performance programming skills",
                supporting_evidence=[f"{lang}: {lines} lines" for lang, lines in metrics.performance_languages.items()],
                impact_potential="Can optimize critical system components",
                confidence=0.8
            ))
        elif total_perf_lines >= 500:
            score += 15
        elif total_perf_lines >= 100:
            score += 10
        
        # Full-stack capability (20% of category score)
        fullstack_evidence_count = len(metrics.full_stack_evidence)
        if fullstack_evidence_count >= 3:
            score += 20
            strengths.append(Strength(
                category=StrengthCategory.PRODUCT_MINDSET,
                description="Comprehensive full-stack development capabilities",
                supporting_evidence=metrics.full_stack_evidence,
                impact_potential="Can build complete products end-to-end",
                confidence=0.8
            ))
        elif fullstack_evidence_count >= 2:
            score += 15
        elif fullstack_evidence_count >= 1:
            score += 10
        
        # Dependency sophistication (15% of category score)
        sophistication_score = metrics.dependency_sophistication_score
        score += sophistication_score * 15
        
        if sophistication_score >= 0.7:
            strengths.append(Strength(
                category=StrengthCategory.TECHNICAL_EXCELLENCE,
                description="Advanced dependency management and tooling",
                supporting_evidence=[f"Sophistication score: {sophistication_score:.2f}"],
                impact_potential="Can architect complex, production-ready systems",
                confidence=0.7
            ))
        
        return score, strengths, risk_factors
    
    def score_engineering_craftsmanship(self, metrics: EngineeringCraftsmanshipMetrics) -> Tuple[float, List[Strength], List[RiskFactor]]:
        """
        Score Category 2: Engineering Craftsmanship.
        
        Args:
            metrics: Engineering craftsmanship metrics
            
        Returns:
            Tuple of (score, strengths, risk_factors)
        """
        score = 0.0
        strengths = []
        risk_factors = []
        
        # Commit-issue linking (30% of category score)
        linking_ratio = metrics.commit_issue_linking_ratio
        score += linking_ratio * 30
        
        if linking_ratio >= 0.6:
            strengths.append(Strength(
                category=StrengthCategory.EXECUTION_FOCUS,
                description="Excellent workflow discipline and traceability",
                supporting_evidence=[f"Links {linking_ratio:.1%} of commits to issues"],
                impact_potential="Reduces management overhead and ensures accountability",
                confidence=0.9
            ))
        elif linking_ratio < 0.2:
            risk_factors.append(RiskFactor(
                category="Engineering Craftsmanship",
                description="Poor commit-issue linking discipline",
                severity=RiskLevel.MEDIUM,
                impact_description="May require more management oversight",
                mitigation_suggestions=["Establish clear workflow guidelines", "Implement tooling to enforce linking"],
                confidence=0.7
            ))
        
        # Testing commitment (30% of category score)
        testing_ratio = metrics.testing_commitment_ratio
        score += testing_ratio * 30
        
        if testing_ratio >= 0.5:
            strengths.append(Strength(
                category=StrengthCategory.EXECUTION_FOCUS,
                description="Strong commitment to testing and quality",
                supporting_evidence=[f"Tests in {testing_ratio:.1%} of commits"],
                impact_potential="Builds reliable, maintainable products",
                confidence=0.8
            ))
        elif testing_ratio < 0.1:
            risk_factors.append(RiskFactor(
                category="Engineering Craftsmanship",
                description="Minimal testing practices",
                severity=RiskLevel.HIGH,
                impact_description="May create technical debt and reliability issues",
                mitigation_suggestions=["Implement testing requirements", "Provide testing training"],
                confidence=0.8
            ))
        
        # Structured workflow (25% of category score)
        workflow_score = metrics.structured_workflow_score
        score += workflow_score * 25
        
        if workflow_score >= 0.7:
            strengths.append(Strength(
                category=StrengthCategory.EXECUTION_FOCUS,
                description="Highly structured development workflow",
                supporting_evidence=[f"Workflow score: {workflow_score:.2f}"],
                impact_potential="Enables fast, predictable development cycles",
                confidence=0.8
            ))
        
        # Code review thoroughness (15% of category score)
        review_thoroughness = metrics.code_review_thoroughness
        score += review_thoroughness * 15
        
        return score, strengths, risk_factors
    
    def score_initiative_ownership(self, metrics: InitiativeOwnershipMetrics) -> Tuple[float, List[Strength], List[RiskFactor]]:
        """
        Score Category 3: Initiative & Ownership.
        
        Args:
            metrics: Initiative ownership metrics
            
        Returns:
            Tuple of (score, strengths, risk_factors)
        """
        score = 0.0
        strengths = []
        risk_factors = []
        
        # Self-directed work cycles (40% of category score)
        self_directed_cycles = metrics.self_directed_work_cycles
        if self_directed_cycles >= 10:
            score += 40
            strengths.append(Strength(
                category=StrengthCategory.LEADERSHIP_POTENTIAL,
                description="Exceptional self-direction and ownership",
                supporting_evidence=[f"{self_directed_cycles} self-directed work cycles"],
                impact_potential="Natural founding team member - finds and solves problems independently",
                confidence=0.95
            ))
        elif self_directed_cycles >= 5:
            score += 30
            strengths.append(Strength(
                category=StrengthCategory.LEADERSHIP_POTENTIAL,
                description="Strong ownership mentality",
                supporting_evidence=[f"{self_directed_cycles} self-directed work cycles"],
                impact_potential="Takes initiative and drives projects forward",
                confidence=0.8
            ))
        elif self_directed_cycles >= 2:
            score += 20
        elif self_directed_cycles == 0:
            risk_factors.append(RiskFactor(
                category="Initiative & Ownership",
                description="No evidence of self-directed work",
                severity=RiskLevel.HIGH,
                impact_description="May wait for direction rather than driving initiatives",
                mitigation_suggestions=["Test initiative through project assignment", "Assess problem-solving approach"],
                confidence=0.7
            ))
        
        # First responder behavior (20% of category score)
        first_responder_count = metrics.first_responder_instances
        if first_responder_count >= 10:
            score += 20
            strengths.append(Strength(
                category=StrengthCategory.COLLABORATION_SKILLS,
                description="Active community contributor and helper",
                supporting_evidence=[f"{first_responder_count} first responder instances"],
                impact_potential="Will actively support team members and unblock progress",
                confidence=0.8
            ))
        elif first_responder_count >= 5:
            score += 15
        elif first_responder_count >= 2:
            score += 10
        
        # Personal project quality (20% of category score)
        project_quality = metrics.personal_project_quality
        score += project_quality * 20
        
        if project_quality >= 0.7:
            strengths.append(Strength(
                category=StrengthCategory.PRODUCT_MINDSET,
                description="High-quality personal projects demonstrate passion",
                supporting_evidence=[f"Project quality score: {project_quality:.2f}"],
                impact_potential="Intrinsically motivated builder who will drive innovation",
                confidence=0.8
            ))
        
        # Open source contributions (20% of category score)
        oss_contributions = metrics.open_source_contributions
        if oss_contributions >= 5:
            score += 20
            strengths.append(Strength(
                category=StrengthCategory.LEARNING_AGILITY,
                description="Active open source contributor",
                supporting_evidence=[f"{oss_contributions} OSS contributions"],
                impact_potential="Stays current with technology and contributes to ecosystem",
                confidence=0.8
            ))
        elif oss_contributions >= 2:
            score += 15
        elif oss_contributions >= 1:
            score += 10
        
        return score, strengths, risk_factors
    
    def score_collaboration_style(self, metrics: CollaborationStyleMetrics) -> Tuple[float, List[Strength], List[RiskFactor]]:
        """
        Score Category 4: Collaboration Style.
        
        Args:
            metrics: Collaboration style metrics
            
        Returns:
            Tuple of (score, strengths, risk_factors)
        """
        score = 0.0
        strengths = []
        risk_factors = []
        
        # Work rhythm and dedication (40% of category score)
        dedication_score = metrics.temporal_dedication_score
        work_pattern = metrics.work_rhythm_pattern
        
        score += dedication_score * 30
        
        # Bonus for passion-indicating patterns
        if work_pattern == WorkRhythmPattern.WEEKEND_WARRIOR:
            score += 10
            strengths.append(Strength(
                category=StrengthCategory.EXECUTION_FOCUS,
                description="Weekend Warrior pattern shows passion for coding",
                supporting_evidence=[f"Work pattern: {work_pattern.value}"],
                impact_potential="Will put in extra effort when needed for startup success",
                confidence=0.8
            ))
        elif work_pattern == WorkRhythmPattern.NIGHT_OWL:
            score += 5
        elif work_pattern == WorkRhythmPattern.NINE_TO_FIVE:
            # Neutral - not necessarily bad for founders
            pass
        elif work_pattern == WorkRhythmPattern.IRREGULAR:
            risk_factors.append(RiskFactor(
                category="Collaboration Style",
                description="Irregular work schedule may affect team coordination",
                severity=RiskLevel.LOW,
                impact_description="May need schedule alignment for effective collaboration",
                mitigation_suggestions=["Discuss schedule expectations", "Establish core collaboration hours"],
                confidence=0.6
            ))
        
        # Feedback receptiveness (25% of category score)
        receptiveness = metrics.feedback_receptiveness_score
        score += receptiveness * 25
        
        if receptiveness >= 0.7:
            strengths.append(Strength(
                category=StrengthCategory.COLLABORATION_SKILLS,
                description="Highly receptive to feedback",
                supporting_evidence=[f"Receptiveness score: {receptiveness:.2f}"],
                impact_potential="Will adapt quickly and maintain low ego for team success",
                confidence=0.8
            ))
        elif receptiveness < 0.3:
            risk_factors.append(RiskFactor(
                category="Collaboration Style",
                description="May be defensive or unreceptive to feedback",
                severity=RiskLevel.MEDIUM,
                impact_description="Could create team friction and slow iteration",
                mitigation_suggestions=["Assess through behavioral interview", "Test feedback response"],
                confidence=0.6
            ))
        
        # Communication clarity (20% of category score)
        clarity = metrics.communication_clarity_score
        score += clarity * 20
        
        if clarity >= 0.8:
            strengths.append(Strength(
                category=StrengthCategory.COLLABORATION_SKILLS,
                description="Excellent written communication skills",
                supporting_evidence=[f"Communication clarity: {clarity:.2f}"],
                impact_potential="Will effectively communicate vision and technical decisions",
                confidence=0.8
            ))
        
        # Mentorship indicators (15% of category score)
        mentorship_count = len(metrics.mentorship_indicators)
        if mentorship_count > 0:
            score += 15
            strengths.append(Strength(
                category=StrengthCategory.LEADERSHIP_POTENTIAL,
                description="Shows mentorship and knowledge sharing",
                supporting_evidence=metrics.mentorship_indicators,
                impact_potential="Will help build and elevate the engineering team",
                confidence=0.7
            ))
        
        return score, strengths, risk_factors
    
    def calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """
        Calculate overall founding engineer score from category scores.
        
        Args:
            category_scores: Dict mapping category name to score
            
        Returns:
            Overall score (0-100)
        """
        weighted_score = 0.0
        
        for category, weight in self.category_weights.items():
            score = category_scores.get(category, 0.0)
            weighted_score += score * weight
        
        return weighted_score
    
    def determine_recommendation(self, overall_score: float, risk_factors: List[RiskFactor]) -> Tuple[RecommendationLevel, str]:
        """
        Determine recommendation level based on score and risk factors.
        
        Args:
            overall_score: Overall founding engineer score
            risk_factors: List of identified risk factors
            
        Returns:
            Tuple of (recommendation_level, reasoning)
        """
        # Check for critical risks
        critical_risks = [rf for rf in risk_factors if rf.severity == RiskLevel.CRITICAL]
        high_risks = [rf for rf in risk_factors if rf.severity == RiskLevel.HIGH]
        
        if critical_risks:
            return RecommendationLevel.NOT_RECOMMENDED, f"Critical risks identified: {len(critical_risks)} issues"
        
        # Determine base recommendation from score
        if overall_score >= self.recommendation_thresholds[RecommendationLevel.STRONGLY_RECOMMENDED]:
            base_recommendation = RecommendationLevel.STRONGLY_RECOMMENDED
        elif overall_score >= self.recommendation_thresholds[RecommendationLevel.RECOMMENDED]:
            base_recommendation = RecommendationLevel.RECOMMENDED
        elif overall_score >= self.recommendation_thresholds[RecommendationLevel.CONDITIONAL]:
            base_recommendation = RecommendationLevel.CONDITIONAL
        else:
            base_recommendation = RecommendationLevel.NOT_RECOMMENDED
        
        # Adjust for high risks
        if len(high_risks) >= 3:
            # Multiple high risks - downgrade recommendation
            if base_recommendation == RecommendationLevel.STRONGLY_RECOMMENDED:
                final_recommendation = RecommendationLevel.RECOMMENDED
                reasoning = f"Strong technical skills but {len(high_risks)} high-risk areas need attention"
            elif base_recommendation == RecommendationLevel.RECOMMENDED:
                final_recommendation = RecommendationLevel.CONDITIONAL
                reasoning = f"Potential candidate but {len(high_risks)} significant concerns"
            else:
                final_recommendation = base_recommendation
                reasoning = f"Score: {overall_score:.1f}, {len(high_risks)} high risks"
        else:
            final_recommendation = base_recommendation
            if final_recommendation == RecommendationLevel.STRONGLY_RECOMMENDED:
                reasoning = f"Exceptional founding engineer candidate (Score: {overall_score:.1f})"
            elif final_recommendation == RecommendationLevel.RECOMMENDED:
                reasoning = f"Strong founding engineer candidate (Score: {overall_score:.1f})"
            elif final_recommendation == RecommendationLevel.CONDITIONAL:
                reasoning = f"Potential candidate with conditions (Score: {overall_score:.1f})"
            else:
                reasoning = f"Does not meet founding engineer criteria (Score: {overall_score:.1f})"
        
        return final_recommendation, reasoning
    
    def calculate_confidence_level(self, activity_count: int, data_completeness: float) -> float:
        """
        Calculate confidence level in the assessment.
        
        Args:
            activity_count: Total number of activities analyzed
            data_completeness: Data completeness score (0-1)
            
        Returns:
            Confidence level (0-1)
        """
        # Base confidence from activity volume
        if activity_count >= 100:
            activity_confidence = 1.0
        elif activity_count >= 50:
            activity_confidence = 0.8
        elif activity_count >= 20:
            activity_confidence = 0.6
        elif activity_count >= 10:
            activity_confidence = 0.4
        else:
            activity_confidence = 0.2
        
        # Combine with data completeness
        overall_confidence = (activity_confidence + data_completeness) / 2
        
        return overall_confidence
    
    def score_comprehensive_assessment(self, metrics: FoundingEngineerMetrics, activity_count: int = 0) -> AssessmentResult:
        """
        Perform comprehensive scoring and assessment.
        
        Args:
            metrics: Complete founding engineer metrics
            activity_count: Total activity count for confidence calculation
            
        Returns:
            Complete AssessmentResult
        """
        print("📊 Calculating Founding Engineer Score...")
        
        # Score each category
        tech_score, tech_strengths, tech_risks = self.score_technical_proficiency(metrics.technical_proficiency)
        craft_score, craft_strengths, craft_risks = self.score_engineering_craftsmanship(metrics.engineering_craftsmanship)
        initiative_score, initiative_strengths, initiative_risks = self.score_initiative_ownership(metrics.initiative_ownership)
        collab_score, collab_strengths, collab_risks = self.score_collaboration_style(metrics.collaboration_style)
        
        # Aggregate scores
        category_scores = {
            'technical_proficiency': tech_score,
            'engineering_craftsmanship': craft_score,
            'initiative_ownership': initiative_score,
            'collaboration_style': collab_score
        }
        
        overall_score = self.calculate_overall_score(category_scores)
        
        # Aggregate strengths and risks
        all_strengths = tech_strengths + craft_strengths + initiative_strengths + collab_strengths
        all_risks = tech_risks + craft_risks + initiative_risks + collab_risks
        
        # Sort strengths and risks by confidence/severity
        all_strengths.sort(key=lambda s: s.confidence, reverse=True)
        all_risks.sort(key=lambda r: (r.severity.value, r.confidence), reverse=True)
        
        # Determine recommendation
        recommendation, reasoning = self.determine_recommendation(overall_score, all_risks)
        
        # Calculate confidence
        confidence = self.calculate_confidence_level(activity_count, metrics.data_completeness_score)
        
        # Create category assessments
        category_assessments = {
            'Technical Proficiency': CategoryAssessment(
                category_name='Technical Proficiency',
                score=tech_score,
                max_score=100.0,
                strengths=tech_strengths,
                risk_factors=tech_risks,
                confidence=confidence
            ),
            'Engineering Craftsmanship': CategoryAssessment(
                category_name='Engineering Craftsmanship',
                score=craft_score,
                max_score=100.0,
                strengths=craft_strengths,
                risk_factors=craft_risks,
                confidence=confidence
            ),
            'Initiative & Ownership': CategoryAssessment(
                category_name='Initiative & Ownership',
                score=initiative_score,
                max_score=100.0,
                strengths=initiative_strengths,
                risk_factors=initiative_risks,
                confidence=confidence
            ),
            'Collaboration Style': CategoryAssessment(
                category_name='Collaboration Style',
                score=collab_score,
                max_score=100.0,
                strengths=collab_strengths,
                risk_factors=collab_risks,
                confidence=confidence
            )
        }
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(overall_score, recommendation, all_strengths[:3], all_risks[:3])
        
        # Create assessment result
        result = AssessmentResult(
            candidate_username=metrics.user_analyzed,
            analysis_period_months=metrics.analysis_period_months,
            overall_score=overall_score,
            recommendation=recommendation,
            confidence_level=confidence,
            category_assessments=category_assessments,
            top_strengths=all_strengths[:5],
            critical_risks=[r for r in all_risks if r.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]],
            detailed_metrics=metrics,
            executive_summary=executive_summary,
            hiring_recommendation=reasoning
        )
        
        print(f"✅ Assessment Complete:")
        print(f"  - Overall Score: {overall_score:.1f}/100")
        print(f"  - Recommendation: {recommendation.value}")
        print(f"  - Confidence: {confidence:.2f}")
        print(f"  - Top Strengths: {len(all_strengths)}")
        print(f"  - Risk Factors: {len(all_risks)}")
        
        return result
    
    def _generate_executive_summary(self, score: float, recommendation: RecommendationLevel, 
                                  top_strengths: List[Strength], top_risks: List[RiskFactor]) -> str:
        """Generate executive summary of the assessment."""
        
        summary_parts = []
        
        # Overall assessment
        if score >= 80:
            summary_parts.append(f"This candidate demonstrates exceptional founding engineer potential with a score of {score:.1f}/100.")
        elif score >= 65:
            summary_parts.append(f"This candidate shows strong founding engineer potential with a score of {score:.1f}/100.")
        elif score >= 45:
            summary_parts.append(f"This candidate has mixed signals for founding engineer potential with a score of {score:.1f}/100.")
        else:
            summary_parts.append(f"This candidate shows limited founding engineer potential with a score of {score:.1f}/100.")
        
        # Key strengths
        if top_strengths:
            strength_summary = ", ".join([s.description.lower() for s in top_strengths[:2]])
            summary_parts.append(f"Key strengths include {strength_summary}.")
        
        # Key concerns
        if top_risks:
            risk_summary = ", ".join([r.description.lower() for r in top_risks[:2]])
            summary_parts.append(f"Primary concerns are {risk_summary}.")
        
        # Final recommendation
        summary_parts.append(f"Recommendation: {recommendation.value}.")
        
        return " ".join(summary_parts)
