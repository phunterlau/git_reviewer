"""
Collaboration Style Analyzer

Implements Category 4 analysis: Collaboration & Communication Style
Analyzes review comments, feedback receptiveness, and work rhythm patterns.
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from collections import defaultdict, Counter

from ..models.metrics import CollaborationStyleMetrics, ActivityData, WorkRhythmPattern


class CollaborationStyleAnalyzer:
    """Analyzer for Category 4: Collaboration & Communication Style."""
    
    def __init__(self):
        """Initialize analyzer with communication patterns."""
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize patterns for communication analysis."""
        
        # Comment type classification patterns
        self.comment_patterns = {
            'questioning': [
                r'\?', r'why ', r'how ', r'what ', r'when ', r'where ',
                r'could you', r'can you', r'would you', r'do you',
                r'is this', r'are we', r'should we'
            ],
            'suggesting': [
                r'suggest', r'consider', r'maybe', r'perhaps', r'might',
                r'could be', r'what about', r'how about', r'alternatively',
                r'instead', r'better to', r'prefer'
            ],
            'praising': [
                r'great', r'good', r'nice', r'excellent', r'awesome',
                r'well done', r'perfect', r'love', r'like', r'impressive',
                r'thanks', r'thank you', r'appreciate'
            ],
            'instructing': [
                r'should', r'must', r'need to', r'have to', r'required',
                r'please', r'fix', r'change', r'update', r'remove'
            ]
        }
        
        # Receptiveness indicators
        self.receptiveness_patterns = {
            'positive': [
                r'thanks', r'thank you', r'good point', r'you\'re right',
                r'makes sense', r'agree', r'will do', r'updated',
                r'fixed', r'addressed', r'done'
            ],
            'collaborative': [
                r'what do you think', r'thoughts', r'feedback',
                r'suggestions', r'let me know', r'discuss'
            ],
            'defensive': [
                r'but', r'however', r'actually', r'no,', r'wrong',
                r'disagree', r'not true', r'don\'t think'
            ]
        }
        
        # Mentorship indicators
        self.mentorship_patterns = [
            r'here\'s how', r'try this', r'you can', r'way to',
            r'tip:', r'hint:', r'fyi', r'for future', r'best practice',
            r'recommend', r'experience', r'learned'
        ]
    
    def classify_review_comments(self, reviews: List[Dict], comments: List[Dict]) -> Dict[str, int]:
        """
        Classify code review comments by type.
        
        Args:
            reviews: List of review data
            comments: List of comment data
            
        Returns:
            Dict mapping comment type to count
        """
        comment_distribution = defaultdict(int)
        
        # Analyze review comments
        for review in reviews:
            body = review.get('body', '').lower()
            if not body:
                continue
            
            # Classify this comment
            classified = False
            for comment_type, patterns in self.comment_patterns.items():
                if any(re.search(pattern, body, re.IGNORECASE) for pattern in patterns):
                    comment_distribution[comment_type] += 1
                    classified = True
                    break
            
            # If not classified, it's informational
            if not classified:
                comment_distribution['informational'] += 1
        
        # Analyze general comments (issue/PR comments)
        for comment in comments:
            body = comment.get('comment_body', '').lower()
            if not body:
                continue
            
            # Classify this comment
            classified = False
            for comment_type, patterns in self.comment_patterns.items():
                if any(re.search(pattern, body, re.IGNORECASE) for pattern in patterns):
                    comment_distribution[comment_type] += 1
                    classified = True
                    break
            
            if not classified:
                comment_distribution['informational'] += 1
        
        return dict(comment_distribution)
    
    def analyze_feedback_receptiveness(self, pull_requests: List[Dict], comments: List[Dict]) -> float:
        """
        Analyze receptiveness to feedback in PR discussions.
        
        Args:
            pull_requests: List of PR data (where user received feedback)
            comments: List of comment data (user's responses)
            
        Returns:
            Feedback receptiveness score (0-1)
        """
        receptiveness_scores = []
        
        # This is a simplified analysis - in reality we'd need to match
        # comments to specific PRs and conversation threads
        
        user_responses = []
        for comment in comments:
            body = comment.get('comment_body', '').lower()
            if body:
                user_responses.append(body)
        
        if not user_responses:
            return 0.5  # Neutral score if no data
        
        total_score = 0
        for response in user_responses:
            response_score = 0.5  # Start neutral
            
            # Positive receptiveness indicators
            positive_count = sum(1 for pattern in self.receptiveness_patterns['positive'] 
                               if re.search(pattern, response, re.IGNORECASE))
            
            collaborative_count = sum(1 for pattern in self.receptiveness_patterns['collaborative'] 
                                    if re.search(pattern, response, re.IGNORECASE))
            
            # Negative receptiveness indicators
            defensive_count = sum(1 for pattern in self.receptiveness_patterns['defensive'] 
                                if re.search(pattern, response, re.IGNORECASE))
            
            # Calculate score for this response
            if positive_count > 0 or collaborative_count > 0:
                response_score += 0.3
            if defensive_count > 0:
                response_score -= 0.2
            
            # Bonus for length (shows engagement)
            if len(response) > 50:
                response_score += 0.1
            
            total_score += max(0, min(1, response_score))
        
        return total_score / len(user_responses)
    
    def analyze_work_rhythm_pattern(self, activity_data: ActivityData) -> Tuple[WorkRhythmPattern, float]:
        """
        Analyze temporal work patterns to determine rhythm.
        
        Args:
            activity_data: Full activity data with timestamps
            
        Returns:
            Tuple of (work_rhythm_pattern, dedication_score)
        """
        # Collect all activity timestamps
        timestamps = []
        
        for activity in activity_data.timeline:
            timestamp_str = activity.get('timestamp', '')
            if timestamp_str:
                try:
                    # Parse ISO format timestamp
                    if timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str[:-1] + '+00:00'
                    
                    dt = datetime.fromisoformat(timestamp_str)
                    timestamps.append(dt)
                except:
                    continue
        
        if not timestamps:
            return WorkRhythmPattern.UNKNOWN, 0.0
        
        # Analyze hour-of-day distribution
        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)
        
        for timestamp in timestamps:
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
            
            hour_distribution[hour] += 1
            day_distribution[day_of_week] += 1
        
        # Determine work pattern
        total_activities = len(timestamps)
        
        # Weekend activity (Saturday=5, Sunday=6)
        weekend_activities = day_distribution[5] + day_distribution[6]
        weekend_ratio = weekend_activities / total_activities
        
        # Night activity (10PM - 6AM)
        night_hours = list(range(22, 24)) + list(range(0, 6))
        night_activities = sum(hour_distribution[hour] for hour in night_hours)
        night_ratio = night_activities / total_activities
        
        # Early morning activity (5AM - 9AM)
        early_hours = list(range(5, 9))
        early_activities = sum(hour_distribution[hour] for hour in early_hours)
        early_ratio = early_activities / total_activities
        
        # Business hours activity (9AM - 5PM)
        business_hours = list(range(9, 17))
        business_activities = sum(hour_distribution[hour] for hour in business_hours)
        business_ratio = business_activities / total_activities
        
        # Determine pattern
        if weekend_ratio > 0.3:
            pattern = WorkRhythmPattern.WEEKEND_WARRIOR
        elif night_ratio > 0.4:
            pattern = WorkRhythmPattern.NIGHT_OWL
        elif early_ratio > 0.3:
            pattern = WorkRhythmPattern.EARLY_BIRD
        elif business_ratio > 0.6:
            pattern = WorkRhythmPattern.NINE_TO_FIVE
        else:
            pattern = WorkRhythmPattern.IRREGULAR
        
        # Calculate dedication score based on activity spread and consistency
        # Higher score for more consistent activity across time periods
        activity_spread = len([h for h in hour_distribution.keys() if hour_distribution[h] > 0])
        spread_score = min(activity_spread / 16, 1.0)  # Max score if active 16+ hours
        
        # Consistency score based on activity distribution
        if total_activities > 0:
            variance = sum((count - total_activities/24)**2 for count in hour_distribution.values()) / 24
            consistency_score = max(0, 1 - (variance / (total_activities**2)))
        else:
            consistency_score = 0
        
        dedication_score = (spread_score + consistency_score) / 2
        
        return pattern, dedication_score
    
    def analyze_mentorship_indicators(self, reviews: List[Dict], comments: List[Dict]) -> List[str]:
        """
        Analyze indicators of mentorship and knowledge sharing.
        
        Args:
            reviews: List of review data
            comments: List of comment data
            
        Returns:
            List of mentorship indicators
        """
        mentorship_indicators = []
        mentorship_count = 0
        
        # Check review comments for mentorship
        for review in reviews:
            body = review.get('body', '').lower()
            
            if any(re.search(pattern, body, re.IGNORECASE) for pattern in self.mentorship_patterns):
                mentorship_count += 1
        
        # Check general comments for mentorship
        for comment in comments:
            body = comment.get('comment_body', '').lower()
            
            if any(re.search(pattern, body, re.IGNORECASE) for pattern in self.mentorship_patterns):
                mentorship_count += 1
        
        total_comments = len(reviews) + len(comments)
        
        if total_comments > 0:
            mentorship_ratio = mentorship_count / total_comments
            
            if mentorship_ratio > 0.2:
                mentorship_indicators.append(f"High mentorship activity: {mentorship_count}/{total_comments} helpful comments")
            elif mentorship_ratio > 0.1:
                mentorship_indicators.append(f"Moderate mentorship: {mentorship_count}/{total_comments} guiding comments")
        
        return mentorship_indicators
    
    def analyze_communication_clarity(self, pull_requests: List[Dict], issues: List[Dict]) -> float:
        """
        Analyze clarity and quality of written communication.
        
        Args:
            pull_requests: List of PR data
            issues: List of issue data
            
        Returns:
            Communication clarity score (0-1)
        """
        clarity_scores = []
        
        # Analyze PR descriptions
        for pr in pull_requests:
            title = pr.get('title', '')
            body = pr.get('body', '')
            
            score = 0.0
            
            # Title clarity (descriptive, not too short/long)
            if 10 < len(title) < 80:
                score += 0.3
            
            # Body length and structure
            if len(body) > 50:
                score += 0.3
                
                # Look for structure indicators
                if any(marker in body.lower() for marker in ['##', '**', '- ', '1.', 'summary', 'changes']):
                    score += 0.2
            
            # Grammar and professionalism (basic heuristics)
            combined_text = (title + ' ' + body).lower()
            if not any(word in combined_text for word in ['lol', 'wtf', 'omg', 'idk']):
                score += 0.2
            
            clarity_scores.append(min(score, 1.0))
        
        # Analyze issue descriptions
        for issue in issues:
            title = issue.get('title', '')
            body = issue.get('body', '')
            
            score = 0.0
            
            # Title clarity
            if 10 < len(title) < 80:
                score += 0.3
            
            # Detailed problem description
            if len(body) > 100:
                score += 0.4
                
                # Look for structured problem reporting
                if any(marker in body.lower() for marker in ['steps', 'expected', 'actual', 'reproduce']):
                    score += 0.3
            
            clarity_scores.append(min(score, 1.0))
        
        if clarity_scores:
            return sum(clarity_scores) / len(clarity_scores)
        else:
            return 0.5  # Neutral if no data
    
    def analyze_team_contribution_quality(self, activity_data: ActivityData) -> float:
        """
        Analyze overall quality of team contributions.
        
        Args:
            activity_data: Full activity data
            
        Returns:
            Team contribution quality score (0-1)
        """
        quality_indicators = []
        
        # Review activity (shows engagement in team processes)
        if activity_data.reviews:
            review_ratio = len(activity_data.reviews) / max(len(activity_data.pull_requests), 1)
            quality_indicators.append(min(review_ratio, 1.0))
        
        # Comment engagement
        if activity_data.comments:
            comment_ratio = len(activity_data.comments) / max(len(activity_data.commits), 1)
            quality_indicators.append(min(comment_ratio * 2, 1.0))  # Scale up since comments are valuable
        
        # Cross-repository collaboration
        unique_repos = len(activity_data.repository_involvement)
        if unique_repos > 1:
            collaboration_score = min(unique_repos / 5, 1.0)  # Max score for 5+ repos
            quality_indicators.append(collaboration_score)
        
        if quality_indicators:
            return sum(quality_indicators) / len(quality_indicators)
        else:
            return 0.0
    
    def analyze(self, activity_data: ActivityData) -> CollaborationStyleMetrics:
        """
        Perform comprehensive collaboration style analysis.
        
        Args:
            activity_data: Raw GitHub activity data
            
        Returns:
            CollaborationStyleMetrics with analysis results
        """
        print("🤝 Analyzing Collaboration Style...")
        
        reviews = activity_data.reviews
        comments = activity_data.comments
        pull_requests = activity_data.pull_requests
        issues = activity_data.issues
        
        # Perform all analyses
        review_comment_distribution = self.classify_review_comments(reviews, comments)
        
        feedback_receptiveness_score = self.analyze_feedback_receptiveness(pull_requests, comments)
        
        work_rhythm_pattern, temporal_dedication_score = self.analyze_work_rhythm_pattern(activity_data)
        
        mentorship_indicators = self.analyze_mentorship_indicators(reviews, comments)
        
        communication_clarity_score = self.analyze_communication_clarity(pull_requests, issues)
        
        team_contribution_quality = self.analyze_team_contribution_quality(activity_data)
        
        # Create metrics object
        metrics = CollaborationStyleMetrics(
            review_comment_distribution=review_comment_distribution,
            feedback_receptiveness_score=feedback_receptiveness_score,
            work_rhythm_pattern=work_rhythm_pattern,
            temporal_dedication_score=temporal_dedication_score,
            mentorship_indicators=mentorship_indicators,
            communication_clarity_score=communication_clarity_score,
            team_contribution_quality=team_contribution_quality
        )
        
        print(f"✅ Collaboration Analysis Complete:")
        print(f"  - Work Rhythm: {work_rhythm_pattern.value}")
        print(f"  - Feedback Receptiveness: {feedback_receptiveness_score:.2f}")
        print(f"  - Temporal Dedication: {temporal_dedication_score:.2f}")
        print(f"  - Communication Clarity: {communication_clarity_score:.2f}")
        
        return metrics
