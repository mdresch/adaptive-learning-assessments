"""
Adaptive Content Selection Engine for the Adaptive Learning System.

This module implements algorithms for selecting optimal learning content
based on learner competency, preferences, and performance patterns.
"""

import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from ..models.competency import LearnerCompetency, CompetencyLevel, Competency
from ..models.performance import LearningActivity, ActivityType
from ..models.learner_profile import LearnerProfile
from ..models.bkt_models import BKTState


logger = logging.getLogger(__name__)


class SelectionStrategy(str, Enum):
    """Content selection strategies."""
    MASTERY_BASED = "mastery_based"
    ZONE_OF_PROXIMAL_DEVELOPMENT = "zpd"
    SPACED_REPETITION = "spaced_repetition"
    DIFFICULTY_PROGRESSION = "difficulty_progression"
    MIXED_PRACTICE = "mixed_practice"


class AdaptiveContentSelector:
    """
    Selects optimal learning content based on adaptive learning principles.
    
    Uses learner competency data, performance history, and learning science
    principles to recommend the most effective next activities.
    """
    
    def __init__(self, db_client=None):
        """
        Initialize the adaptive content selector.
        
        Args:
            db_client: Database client for persistence (optional)
        """
        self.db_client = db_client
        self.logger = logger
        
        # Selection parameters
        self.mastery_threshold = 0.8
        self.learning_threshold = 0.3
        self.zpd_range = (0.3, 0.7)  # Zone of Proximal Development
        self.difficulty_step_size = 0.1
        
        # Spaced repetition intervals (in days)
        self.spaced_intervals = [1, 3, 7, 14, 30, 90]
        
        # Content type weights for different learning styles
        self.learning_style_weights = {
            "visual": {
                "video": 1.5,
                "interactive_exercise": 1.3,
                "reading": 0.8,
                "quiz": 1.0
            },
            "auditory": {
                "video": 1.4,
                "reading": 1.2,
                "interactive_exercise": 1.0,
                "quiz": 0.9
            },
            "kinesthetic": {
                "interactive_exercise": 1.6,
                "coding_challenge": 1.5,
                "project": 1.4,
                "quiz": 0.8
            },
            "reading_writing": {
                "reading": 1.5,
                "quiz": 1.3,
                "project": 1.2,
                "video": 0.9
            }
        }
    
    async def select_next_activities(
        self,
        learner_id: str,
        num_activities: int = 3,
        strategy: SelectionStrategy = SelectionStrategy.MASTERY_BASED,
        session_duration_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Select the next optimal activities for a learner.
        
        Args:
            learner_id: Learner identifier
            num_activities: Number of activities to select
            strategy: Selection strategy to use
            session_duration_minutes: Available session time
            
        Returns:
            List of recommended activity dictionaries
        """
        try:
            # Get learner data
            learner_profile = await self._get_learner_profile(learner_id)
            competency_states = await self._get_learner_competencies(learner_id)
            available_activities = await self._get_available_activities()
            
            if not competency_states or not available_activities:
                return await self._get_default_activities(num_activities)
            
            # Apply selection strategy
            if strategy == SelectionStrategy.MASTERY_BASED:
                recommendations = await self._select_mastery_based(
                    learner_profile, competency_states, available_activities, num_activities
                )
            elif strategy == SelectionStrategy.ZONE_OF_PROXIMAL_DEVELOPMENT:
                recommendations = await self._select_zpd_based(
                    learner_profile, competency_states, available_activities, num_activities
                )
            elif strategy == SelectionStrategy.SPACED_REPETITION:
                recommendations = await self._select_spaced_repetition(
                    learner_profile, competency_states, available_activities, num_activities
                )
            elif strategy == SelectionStrategy.DIFFICULTY_PROGRESSION:
                recommendations = await self._select_difficulty_progression(
                    learner_profile, competency_states, available_activities, num_activities
                )
            else:  # MIXED_PRACTICE
                recommendations = await self._select_mixed_practice(
                    learner_profile, competency_states, available_activities, num_activities
                )
            
            # Apply personalization filters
            recommendations = self._apply_personalization(recommendations, learner_profile)
            
            # Ensure activities fit within session duration
            recommendations = self._fit_to_session_duration(recommendations, session_duration_minutes)
            
            self.logger.info(
                f"Selected {len(recommendations)} activities for learner {learner_id} "
                f"using {strategy} strategy"
            )
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to select activities for {learner_id}: {e}")
            return await self._get_default_activities(num_activities)
    
    async def _select_mastery_based(
        self,
        learner_profile: LearnerProfile,
        competency_states: List[LearnerCompetency],
        available_activities: List[LearningActivity],
        num_activities: int
    ) -> List[Dict[str, Any]]:
        """
        Select activities based on mastery levels.
        
        Prioritizes competencies that are in the learning phase
        and need reinforcement.
        """
        recommendations = []
        
        # Group competencies by mastery level
        learning_competencies = []
        review_competencies = []
        new_competencies = []
        
        for comp in competency_states:
            if comp.mastery_probability < self.learning_threshold:
                new_competencies.append(comp)
            elif comp.mastery_probability < self.mastery_threshold:
                learning_competencies.append(comp)
            else:
                review_competencies.append(comp)
        
        # Prioritize learning competencies
        target_competencies = learning_competencies[:num_activities]
        
        # Fill with new competencies if needed
        if len(target_competencies) < num_activities:
            remaining = num_activities - len(target_competencies)
            target_competencies.extend(new_competencies[:remaining])
        
        # Fill with review competencies if still needed
        if len(target_competencies) < num_activities:
            remaining = num_activities - len(target_competencies)
            target_competencies.extend(review_competencies[:remaining])
        
        # Find activities for target competencies
        for comp in target_competencies:
            activity = self._find_best_activity_for_competency(
                comp, available_activities, learner_profile
            )
            if activity:
                recommendations.append({
                    "activity": activity,
                    "competency": comp,
                    "reason": self._get_selection_reason(comp),
                    "priority": self._calculate_priority(comp),
                    "estimated_difficulty": self._estimate_activity_difficulty(activity, comp)
                })
        
        return recommendations
    
    async def _select_zpd_based(
        self,
        learner_profile: LearnerProfile,
        competency_states: List[LearnerCompetency],
        available_activities: List[LearningActivity],
        num_activities: int
    ) -> List[Dict[str, Any]]:
        """
        Select activities based on Zone of Proximal Development.
        
        Focuses on competencies within the optimal learning zone.
        """
        recommendations = []
        
        # Find competencies in ZPD
        zpd_competencies = [
            comp for comp in competency_states
            if self.zpd_range[0] <= comp.mastery_probability <= self.zpd_range[1]
        ]
        
        # Sort by learning potential (how close to upper ZPD bound)
        zpd_competencies.sort(
            key=lambda c: self.zpd_range[1] - c.mastery_probability
        )
        
        # Select top competencies
        target_competencies = zpd_competencies[:num_activities]
        
        # If not enough ZPD competencies, add some just below ZPD
        if len(target_competencies) < num_activities:
            below_zpd = [
                comp for comp in competency_states
                if comp.mastery_probability < self.zpd_range[0]
            ]
            below_zpd.sort(key=lambda c: c.mastery_probability, reverse=True)
            remaining = num_activities - len(target_competencies)
            target_competencies.extend(below_zpd[:remaining])
        
        # Find activities for target competencies
        for comp in target_competencies:
            activity = self._find_best_activity_for_competency(
                comp, available_activities, learner_profile
            )
            if activity:
                recommendations.append({
                    "activity": activity,
                    "competency": comp,
                    "reason": f"In Zone of Proximal Development (mastery: {comp.mastery_probability:.2f})",
                    "priority": self._calculate_zpd_priority(comp),
                    "estimated_difficulty": self._estimate_activity_difficulty(activity, comp)
                })
        
        return recommendations
    
    async def _select_spaced_repetition(
        self,
        learner_profile: LearnerProfile,
        competency_states: List[LearnerCompetency],
        available_activities: List[LearningActivity],
        num_activities: int
    ) -> List[Dict[str, Any]]:
        """
        Select activities based on spaced repetition principles.
        
        Reviews previously learned competencies at optimal intervals.
        """
        recommendations = []
        current_time = datetime.utcnow()
        
        # Find competencies due for review
        review_due = []
        
        for comp in competency_states:
            if comp.last_attempt and comp.mastery_probability > self.learning_threshold:
                days_since_last = (current_time - comp.last_attempt).days
                
                # Determine optimal interval based on mastery level
                if comp.mastery_probability >= self.mastery_threshold:
                    # Use longer intervals for mastered content
                    optimal_interval = self._get_spaced_interval(comp.successful_attempts, True)
                else:
                    # Use shorter intervals for learning content
                    optimal_interval = self._get_spaced_interval(comp.successful_attempts, False)
                
                if days_since_last >= optimal_interval:
                    review_due.append((comp, days_since_last - optimal_interval))
        
        # Sort by how overdue they are
        review_due.sort(key=lambda x: x[1], reverse=True)
        
        # Select top overdue competencies
        target_competencies = [comp for comp, _ in review_due[:num_activities]]
        
        # Fill with other learning competencies if needed
        if len(target_competencies) < num_activities:
            other_learning = [
                comp for comp in competency_states
                if comp not in target_competencies and 
                self.learning_threshold <= comp.mastery_probability < self.mastery_threshold
            ]
            remaining = num_activities - len(target_competencies)
            target_competencies.extend(other_learning[:remaining])
        
        # Find activities for target competencies
        for comp in target_competencies:
            activity = self._find_best_activity_for_competency(
                comp, available_activities, learner_profile
            )
            if activity:
                recommendations.append({
                    "activity": activity,
                    "competency": comp,
                    "reason": "Due for spaced repetition review",
                    "priority": self._calculate_spaced_priority(comp, current_time),
                    "estimated_difficulty": self._estimate_activity_difficulty(activity, comp)
                })
        
        return recommendations
    
    async def _select_difficulty_progression(
        self,
        learner_profile: LearnerProfile,
        competency_states: List[LearnerCompetency],
        available_activities: List[LearningActivity],
        num_activities: int
    ) -> List[Dict[str, Any]]:
        """
        Select activities with progressive difficulty increase.
        
        Gradually increases challenge level based on performance.
        """
        recommendations = []
        
        # Sort competencies by mastery level
        sorted_competencies = sorted(
            competency_states,
            key=lambda c: c.mastery_probability
        )
        
        # Select competencies for progression
        target_competencies = []
        
        for comp in sorted_competencies:
            if len(target_competencies) >= num_activities:
                break
                
            # Include if in learning phase or ready for next level
            if (self.learning_threshold <= comp.mastery_probability < self.mastery_threshold or
                comp.mastery_probability < self.learning_threshold):
                target_competencies.append(comp)
        
        # Find activities with appropriate difficulty progression
        for i, comp in enumerate(target_competencies):
            # Calculate target difficulty based on position in sequence
            base_difficulty = comp.mastery_probability
            progression_factor = i * self.difficulty_step_size
            target_difficulty = min(1.0, base_difficulty + progression_factor)
            
            activity = self._find_activity_with_difficulty(
                comp, available_activities, target_difficulty, learner_profile
            )
            
            if activity:
                recommendations.append({
                    "activity": activity,
                    "competency": comp,
                    "reason": f"Progressive difficulty step {i+1}",
                    "priority": num_activities - i,  # Earlier in sequence = higher priority
                    "estimated_difficulty": target_difficulty
                })
        
        return recommendations
    
    async def _select_mixed_practice(
        self,
        learner_profile: LearnerProfile,
        competency_states: List[LearnerCompetency],
        available_activities: List[LearningActivity],
        num_activities: int
    ) -> List[Dict[str, Any]]:
        """
        Select activities using mixed practice approach.
        
        Combines different competencies and activity types for variety.
        """
        recommendations = []
        
        # Get competencies from different categories
        categories = {}
        for comp in competency_states:
            # This would use actual competency categories
            category = getattr(comp, 'category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(comp)
        
        # Select from different categories
        selected_competencies = []
        category_names = list(categories.keys())
        
        for i in range(num_activities):
            if not category_names:
                break
                
            # Round-robin through categories
            category = category_names[i % len(category_names)]
            category_comps = categories[category]
            
            if category_comps:
                # Select best competency from this category
                best_comp = max(
                    category_comps,
                    key=lambda c: self._calculate_mixed_practice_score(c)
                )
                selected_competencies.append(best_comp)
                category_comps.remove(best_comp)
                
                # Remove category if empty
                if not category_comps:
                    category_names.remove(category)
        
        # Find diverse activities for selected competencies
        used_activity_types = set()
        
        for comp in selected_competencies:
            activity = self._find_diverse_activity_for_competency(
                comp, available_activities, used_activity_types, learner_profile
            )
            
            if activity:
                used_activity_types.add(activity.activity_type)
                recommendations.append({
                    "activity": activity,
                    "competency": comp,
                    "reason": "Mixed practice variety",
                    "priority": self._calculate_priority(comp),
                    "estimated_difficulty": self._estimate_activity_difficulty(activity, comp)
                })
        
        return recommendations
    
    def _find_best_activity_for_competency(
        self,
        competency: LearnerCompetency,
        available_activities: List[LearningActivity],
        learner_profile: LearnerProfile
    ) -> Optional[LearningActivity]:
        """
        Find the best activity for a specific competency.
        
        Args:
            competency: Target competency
            available_activities: Available activities
            learner_profile: Learner profile for personalization
            
        Returns:
            Best matching activity or None
        """
        # Filter activities that target this competency
        relevant_activities = [
            activity for activity in available_activities
            if competency.competency_id in activity.target_competencies
        ]
        
        if not relevant_activities:
            return None
        
        # Score activities based on suitability
        scored_activities = []
        
        for activity in relevant_activities:
            score = self._score_activity_for_competency(
                activity, competency, learner_profile
            )
            scored_activities.append((activity, score))
        
        # Return highest scoring activity
        scored_activities.sort(key=lambda x: x[1], reverse=True)
        return scored_activities[0][0] if scored_activities else None
    
    def _score_activity_for_competency(
        self,
        activity: LearningActivity,
        competency: LearnerCompetency,
        learner_profile: LearnerProfile
    ) -> float:
        """
        Score an activity's suitability for a competency.
        
        Args:
            activity: Activity to score
            competency: Target competency
            learner_profile: Learner profile
            
        Returns:
            Suitability score (higher is better)
        """
        score = 0.0
        
        # Base score from activity quality (placeholder)
        score += 0.5
        
        # Difficulty match score
        target_difficulty = self._get_target_difficulty(competency)
        activity_difficulty = self._get_activity_difficulty_score(activity)
        difficulty_match = 1.0 - abs(target_difficulty - activity_difficulty)
        score += difficulty_match * 0.3
        
        # Learning style match
        learning_styles = learner_profile.preferences.learning_styles
        if learning_styles:
            style_score = 0.0
            for style in learning_styles:
                if style in self.learning_style_weights:
                    activity_type = activity.activity_type.value
                    weight = self.learning_style_weights[style].get(activity_type, 1.0)
                    style_score += weight
            style_score /= len(learning_styles)
            score += (style_score - 1.0) * 0.2  # Normalize around 1.0
        
        # Duration preference match
        preferred_duration = learner_profile.preferences.session_duration_minutes
        duration_ratio = min(activity.estimated_duration_minutes / preferred_duration, 1.0)
        score += duration_ratio * 0.1
        
        # Avoid recently completed activities (if we had that data)
        # This would check completion history
        
        return score
    
    def _get_target_difficulty(self, competency: LearnerCompetency) -> float:
        """
        Get target difficulty for a competency based on mastery level.
        
        Args:
            competency: Learner competency
            
        Returns:
            Target difficulty (0.0 to 1.0)
        """
        mastery = competency.mastery_probability
        
        if mastery < self.learning_threshold:
            # New learners: start easy
            return 0.3
        elif mastery < self.mastery_threshold:
            # Learning phase: moderate challenge
            return 0.5 + (mastery - self.learning_threshold) * 0.4
        else:
            # Mastered: maintain with appropriate challenge
            return 0.7
    
    def _get_activity_difficulty_score(self, activity: LearningActivity) -> float:
        """
        Get normalized difficulty score for an activity.
        
        Args:
            activity: Learning activity
            
        Returns:
            Difficulty score (0.0 to 1.0)
        """
        # This would use actual difficulty ratings
        # For now, map difficulty levels to scores
        difficulty_map = {
            "beginner": 0.2,
            "easy": 0.3,
            "medium": 0.5,
            "hard": 0.7,
            "advanced": 0.8,
            "expert": 0.9
        }
        
        return difficulty_map.get(activity.difficulty_level, 0.5)
    
    def _calculate_priority(self, competency: LearnerCompetency) -> float:
        """
        Calculate priority score for a competency.
        
        Args:
            competency: Learner competency
            
        Returns:
            Priority score (higher is more important)
        """
        # Base priority on learning potential
        mastery = competency.mastery_probability
        
        if mastery < self.learning_threshold:
            # New competencies: medium priority
            priority = 0.6
        elif mastery < self.mastery_threshold:
            # Learning competencies: high priority
            priority = 0.8 + (self.mastery_threshold - mastery) * 0.2
        else:
            # Mastered competencies: lower priority for review
            priority = 0.4
        
        # Adjust based on recent performance
        if competency.attempts_count > 0:
            success_rate = competency.successful_attempts / competency.attempts_count
            if success_rate < 0.5:
                priority += 0.2  # Struggling competencies get higher priority
        
        return min(1.0, priority)
    
    def _apply_personalization(
        self,
        recommendations: List[Dict[str, Any]],
        learner_profile: LearnerProfile
    ) -> List[Dict[str, Any]]:
        """
        Apply personalization filters to recommendations.
        
        Args:
            recommendations: Activity recommendations
            learner_profile: Learner profile
            
        Returns:
            Personalized recommendations
        """
        # Apply accessibility filters
        accessibility_needs = learner_profile.preferences.accessibility_needs
        if accessibility_needs:
            # This would filter activities based on accessibility requirements
            pass
        
        # Apply gamification preferences
        if not learner_profile.preferences.gamification_enabled:
            # Remove or modify gamified elements
            for rec in recommendations:
                rec["gamification"] = False
        
        # Sort by priority
        recommendations.sort(key=lambda x: x["priority"], reverse=True)
        
        return recommendations
    
    def _fit_to_session_duration(
        self,
        recommendations: List[Dict[str, Any]],
        session_duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Ensure recommendations fit within session duration.
        
        Args:
            recommendations: Activity recommendations
            session_duration_minutes: Available session time
            
        Returns:
            Filtered recommendations that fit in session
        """
        fitted_recommendations = []
        total_duration = 0
        
        for rec in recommendations:
            activity_duration = rec["activity"].estimated_duration_minutes
            if total_duration + activity_duration <= session_duration_minutes:
                fitted_recommendations.append(rec)
                total_duration += activity_duration
            else:
                break
        
        return fitted_recommendations
    
    # Additional helper methods would be implemented here...
    
    async def _get_learner_profile(self, learner_id: str) -> Optional[LearnerProfile]:
        """Get learner profile from database."""
        # This would be implemented with actual database query
        return None
    
    async def _get_learner_competencies(self, learner_id: str) -> List[LearnerCompetency]:
        """Get learner competencies from database."""
        # This would be implemented with actual database query
        return []
    
    async def _get_available_activities(self) -> List[LearningActivity]:
        """Get available activities from database."""
        # This would be implemented with actual database query
        return []
    
    async def _get_default_activities(self, num_activities: int) -> List[Dict[str, Any]]:
        """Get default activities for new learners."""
        # This would return starter activities
        return []