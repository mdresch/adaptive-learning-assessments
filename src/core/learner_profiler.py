"""
Learner Profile Management for the Adaptive Learning System.

This module handles learner profile creation, updates, and analysis
to support personalized learning experiences.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from ..models.learner_profile import (
    LearnerProfile, LearnerProfileUpdate, LearnerPreferences, 
    LearnerDemographics, LearningStyle, ExperienceLevel
)
from ..models.competency import LearnerCompetency, CompetencyLevel
from ..models.performance import PerformanceRecord, ActivityResult


logger = logging.getLogger(__name__)


class LearnerProfiler:
    """
    Manages learner profiles and provides insights for adaptive learning.
    
    Handles profile creation, updates, learning style analysis,
    and personalization recommendations.
    """
    
    def __init__(self, db_client=None):
        """
        Initialize the learner profiler.
        
        Args:
            db_client: Database client for persistence (optional)
        """
        self.db_client = db_client
        self.logger = logger
        
        # Learning style detection thresholds
        self.learning_style_thresholds = {
            "visual": {"video_engagement": 0.7, "diagram_preference": 0.6},
            "auditory": {"audio_engagement": 0.7, "discussion_participation": 0.6},
            "kinesthetic": {"interactive_preference": 0.8, "hands_on_completion": 0.7},
            "reading_writing": {"text_engagement": 0.7, "note_taking": 0.6}
        }
    
    async def create_profile(
        self,
        learner_id: str,
        username: str,
        email: str,
        demographics: Optional[LearnerDemographics] = None,
        preferences: Optional[LearnerPreferences] = None,
        programming_experience: ExperienceLevel = ExperienceLevel.BEGINNER,
        learning_goals: Optional[List[str]] = None
    ) -> LearnerProfile:
        """
        Create a new learner profile.
        
        Args:
            learner_id: Unique learner identifier
            username: Username
            email: Email address
            demographics: Demographic information
            preferences: Learning preferences
            programming_experience: Programming experience level
            learning_goals: Learning objectives
            
        Returns:
            Created LearnerProfile
        """
        try:
            # Create profile with defaults
            profile = LearnerProfile(
                learner_id=learner_id,
                username=username,
                email=email,
                demographics=demographics or LearnerDemographics(),
                preferences=preferences or LearnerPreferences(),
                programming_experience=programming_experience,
                learning_goals=learning_goals or []
            )
            
            # Save to database if available
            if self.db_client:
                try:
                    # This would be implemented with actual database save
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to save profile to database: {e}")
            
            self.logger.info(f"Created profile for learner {learner_id}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to create profile for {learner_id}: {e}")
            raise
    
    async def get_profile(self, learner_id: str) -> Optional[LearnerProfile]:
        """
        Retrieve a learner profile.
        
        Args:
            learner_id: Learner identifier
            
        Returns:
            LearnerProfile or None if not found
        """
        if self.db_client:
            try:
                # This would be implemented with actual database query
                pass
            except Exception as e:
                self.logger.warning(f"Failed to load profile for {learner_id}: {e}")
        
        return None
    
    async def update_profile(
        self,
        learner_id: str,
        updates: LearnerProfileUpdate
    ) -> Optional[LearnerProfile]:
        """
        Update a learner profile.
        
        Args:
            learner_id: Learner identifier
            updates: Profile updates
            
        Returns:
            Updated LearnerProfile or None if not found
        """
        try:
            profile = await self.get_profile(learner_id)
            if not profile:
                self.logger.warning(f"Profile not found for learner {learner_id}")
                return None
            
            # Apply updates
            if updates.demographics:
                profile.demographics = updates.demographics
            if updates.preferences:
                profile.preferences = updates.preferences
            if updates.programming_experience:
                profile.programming_experience = updates.programming_experience
            if updates.learning_goals is not None:
                profile.learning_goals = updates.learning_goals
            if updates.data_consent is not None:
                profile.data_consent = updates.data_consent
            if updates.analytics_consent is not None:
                profile.analytics_consent = updates.analytics_consent
            
            # Update timestamp
            profile.updated_at = datetime.utcnow()
            
            # Save to database if available
            if self.db_client:
                try:
                    # This would be implemented with actual database save
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to save updated profile: {e}")
            
            self.logger.info(f"Updated profile for learner {learner_id}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to update profile for {learner_id}: {e}")
            raise
    
    async def analyze_learning_patterns(
        self,
        learner_id: str,
        performance_history: List[PerformanceRecord],
        activity_results: List[ActivityResult]
    ) -> Dict[str, Any]:
        """
        Analyze learner patterns to provide insights.
        
        Args:
            learner_id: Learner identifier
            performance_history: Historical performance records
            activity_results: Activity completion results
            
        Returns:
            Dictionary with learning pattern analysis
        """
        try:
            analysis = {
                "learner_id": learner_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "learning_style_indicators": {},
                "performance_trends": {},
                "engagement_patterns": {},
                "difficulty_preferences": {},
                "time_patterns": {},
                "recommendations": []
            }
            
            # Analyze learning style indicators
            analysis["learning_style_indicators"] = self._analyze_learning_style(
                performance_history, activity_results
            )
            
            # Analyze performance trends
            analysis["performance_trends"] = self._analyze_performance_trends(
                activity_results
            )
            
            # Analyze engagement patterns
            analysis["engagement_patterns"] = self._analyze_engagement_patterns(
                performance_history, activity_results
            )
            
            # Analyze difficulty preferences
            analysis["difficulty_preferences"] = self._analyze_difficulty_preferences(
                activity_results
            )
            
            # Analyze time patterns
            analysis["time_patterns"] = self._analyze_time_patterns(
                performance_history, activity_results
            )
            
            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze learning patterns for {learner_id}: {e}")
            raise
    
    def _analyze_learning_style(
        self,
        performance_history: List[PerformanceRecord],
        activity_results: List[ActivityResult]
    ) -> Dict[str, float]:
        """
        Analyze learning style indicators from behavior data.
        
        Args:
            performance_history: Performance records
            activity_results: Activity results
            
        Returns:
            Dictionary with learning style scores
        """
        style_indicators = {
            "visual": 0.0,
            "auditory": 0.0,
            "kinesthetic": 0.0,
            "reading_writing": 0.0
        }
        
        if not activity_results:
            return style_indicators
        
        # Analyze activity type preferences and performance
        activity_type_performance = {}
        activity_type_engagement = {}
        
        for result in activity_results:
            # This would analyze actual activity types and performance
            # For now, provide placeholder logic
            pass
        
        # Calculate style scores based on performance and engagement
        # Visual learners: better with diagrams, videos, visual content
        # Auditory learners: better with audio content, discussions
        # Kinesthetic learners: better with interactive, hands-on activities
        # Reading/Writing learners: better with text-based content
        
        return style_indicators
    
    def _analyze_performance_trends(
        self,
        activity_results: List[ActivityResult]
    ) -> Dict[str, Any]:
        """
        Analyze performance trends over time.
        
        Args:
            activity_results: Activity results
            
        Returns:
            Dictionary with performance trend analysis
        """
        if not activity_results:
            return {"trend": "insufficient_data"}
        
        # Sort by completion time
        sorted_results = sorted(activity_results, key=lambda x: x.start_time)
        
        # Calculate moving averages
        window_size = min(5, len(sorted_results))
        recent_scores = [r.percentage_score for r in sorted_results[-window_size:]]
        early_scores = [r.percentage_score for r in sorted_results[:window_size]]
        
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        early_avg = sum(early_scores) / len(early_scores) if early_scores else 0
        
        # Determine trend
        if recent_avg > early_avg + 5:
            trend = "improving"
        elif recent_avg < early_avg - 5:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "recent_average": recent_avg,
            "early_average": early_avg,
            "improvement": recent_avg - early_avg,
            "total_activities": len(activity_results),
            "analysis_window": window_size
        }
    
    def _analyze_engagement_patterns(
        self,
        performance_history: List[PerformanceRecord],
        activity_results: List[ActivityResult]
    ) -> Dict[str, Any]:
        """
        Analyze learner engagement patterns.
        
        Args:
            performance_history: Performance records
            activity_results: Activity results
            
        Returns:
            Dictionary with engagement analysis
        """
        if not activity_results:
            return {"engagement_level": "unknown"}
        
        # Calculate engagement metrics
        total_time = sum(r.duration_minutes or 0 for r in activity_results)
        completed_activities = len([r for r in activity_results if r.status == "completed"])
        total_activities = len(activity_results)
        
        completion_rate = completed_activities / total_activities if total_activities > 0 else 0
        avg_session_time = total_time / total_activities if total_activities > 0 else 0
        
        # Determine engagement level
        if completion_rate > 0.8 and avg_session_time > 20:
            engagement_level = "high"
        elif completion_rate > 0.6 and avg_session_time > 10:
            engagement_level = "medium"
        else:
            engagement_level = "low"
        
        return {
            "engagement_level": engagement_level,
            "completion_rate": completion_rate,
            "average_session_time": avg_session_time,
            "total_time_spent": total_time,
            "completed_activities": completed_activities,
            "total_activities": total_activities
        }
    
    def _analyze_difficulty_preferences(
        self,
        activity_results: List[ActivityResult]
    ) -> Dict[str, Any]:
        """
        Analyze learner's difficulty preferences and performance.
        
        Args:
            activity_results: Activity results
            
        Returns:
            Dictionary with difficulty preference analysis
        """
        if not activity_results:
            return {"preferred_difficulty": "unknown"}
        
        # Group results by difficulty level
        difficulty_performance = {}
        
        for result in activity_results:
            # This would use actual difficulty levels from activities
            # For now, use placeholder logic
            difficulty = getattr(result, 'difficulty_level', 'medium')
            
            if difficulty not in difficulty_performance:
                difficulty_performance[difficulty] = []
            
            difficulty_performance[difficulty].append(result.percentage_score)
        
        # Calculate average performance by difficulty
        difficulty_averages = {}
        for difficulty, scores in difficulty_performance.items():
            difficulty_averages[difficulty] = sum(scores) / len(scores)
        
        # Find preferred difficulty (best performance with reasonable challenge)
        preferred_difficulty = "medium"  # Default
        if difficulty_averages:
            # Simple heuristic: prefer difficulty with good performance (>70%)
            good_performance = {d: avg for d, avg in difficulty_averages.items() if avg > 70}
            if good_performance:
                preferred_difficulty = max(good_performance.keys())
        
        return {
            "preferred_difficulty": preferred_difficulty,
            "difficulty_performance": difficulty_averages,
            "difficulty_distribution": {d: len(scores) for d, scores in difficulty_performance.items()}
        }
    
    def _analyze_time_patterns(
        self,
        performance_history: List[PerformanceRecord],
        activity_results: List[ActivityResult]
    ) -> Dict[str, Any]:
        """
        Analyze learner's time-based patterns.
        
        Args:
            performance_history: Performance records
            activity_results: Activity results
            
        Returns:
            Dictionary with time pattern analysis
        """
        if not activity_results:
            return {"optimal_time": "unknown"}
        
        # Analyze performance by time of day
        hour_performance = {}
        
        for result in activity_results:
            hour = result.start_time.hour
            if hour not in hour_performance:
                hour_performance[hour] = []
            hour_performance[hour].append(result.percentage_score)
        
        # Calculate average performance by hour
        hour_averages = {}
        for hour, scores in hour_performance.items():
            hour_averages[hour] = sum(scores) / len(scores)
        
        # Find optimal time (best performance)
        optimal_hour = max(hour_averages.keys(), key=lambda h: hour_averages[h]) if hour_averages else 12
        
        # Categorize time periods
        if 6 <= optimal_hour < 12:
            optimal_period = "morning"
        elif 12 <= optimal_hour < 18:
            optimal_period = "afternoon"
        else:
            optimal_period = "evening"
        
        return {
            "optimal_time": optimal_period,
            "optimal_hour": optimal_hour,
            "hour_performance": hour_averages,
            "total_sessions": len(activity_results)
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate personalized recommendations based on analysis.
        
        Args:
            analysis: Learning pattern analysis
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Performance trend recommendations
        performance_trends = analysis.get("performance_trends", {})
        if performance_trends.get("trend") == "declining":
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "message": "Consider reviewing fundamental concepts and taking breaks between sessions.",
                "action": "review_fundamentals"
            })
        elif performance_trends.get("trend") == "improving":
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "message": "Great progress! Consider increasing difficulty level for more challenge.",
                "action": "increase_difficulty"
            })
        
        # Engagement recommendations
        engagement = analysis.get("engagement_patterns", {})
        if engagement.get("engagement_level") == "low":
            recommendations.append({
                "type": "engagement",
                "priority": "high",
                "message": "Try shorter, more interactive activities to boost engagement.",
                "action": "shorter_sessions"
            })
        
        # Time pattern recommendations
        time_patterns = analysis.get("time_patterns", {})
        optimal_time = time_patterns.get("optimal_time")
        if optimal_time and optimal_time != "unknown":
            recommendations.append({
                "type": "scheduling",
                "priority": "medium",
                "message": f"You perform best during {optimal_time} hours. Consider scheduling study sessions then.",
                "action": "optimize_schedule"
            })
        
        # Learning style recommendations
        style_indicators = analysis.get("learning_style_indicators", {})
        if style_indicators:
            dominant_style = max(style_indicators.keys(), key=lambda k: style_indicators[k])
            recommendations.append({
                "type": "learning_style",
                "priority": "medium",
                "message": f"Your {dominant_style} learning style is prominent. Focus on {dominant_style} content.",
                "action": f"emphasize_{dominant_style}"
            })
        
        return recommendations
    
    async def get_personalization_settings(self, learner_id: str) -> Dict[str, Any]:
        """
        Get personalization settings for adaptive content delivery.
        
        Args:
            learner_id: Learner identifier
            
        Returns:
            Dictionary with personalization settings
        """
        try:
            profile = await self.get_profile(learner_id)
            if not profile:
                return self._get_default_personalization_settings()
            
            # Get recent performance data for analysis
            # This would be implemented with actual database queries
            performance_history = []
            activity_results = []
            
            # Analyze patterns
            analysis = await self.analyze_learning_patterns(
                learner_id, performance_history, activity_results
            )
            
            # Build personalization settings
            settings = {
                "learner_id": learner_id,
                "difficulty_preference": profile.preferences.difficulty_preference,
                "session_duration": profile.preferences.session_duration_minutes,
                "learning_styles": profile.preferences.learning_styles,
                "accessibility_needs": profile.preferences.accessibility_needs,
                "gamification_enabled": profile.preferences.gamification_enabled,
                "optimal_time": analysis.get("time_patterns", {}).get("optimal_time", "any"),
                "preferred_difficulty": analysis.get("difficulty_preferences", {}).get("preferred_difficulty", "medium"),
                "engagement_level": analysis.get("engagement_patterns", {}).get("engagement_level", "medium"),
                "recommendations": analysis.get("recommendations", [])
            }
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to get personalization settings for {learner_id}: {e}")
            return self._get_default_personalization_settings()
    
    def _get_default_personalization_settings(self) -> Dict[str, Any]:
        """
        Get default personalization settings for new learners.
        
        Returns:
            Dictionary with default settings
        """
        return {
            "difficulty_preference": "adaptive",
            "session_duration": 30,
            "learning_styles": ["visual"],
            "accessibility_needs": [],
            "gamification_enabled": True,
            "optimal_time": "any",
            "preferred_difficulty": "medium",
            "engagement_level": "medium",
            "recommendations": []
        }