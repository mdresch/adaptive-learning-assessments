"""
Adaptive challenge selection engine for personalized learning.
"""
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from src.models.adaptive_models import (
    CompetencyLevel, ChallengeMetadata, AdaptiveRecommendation,
    ChallengeSequence, AdaptationRequest, AdaptationResponse,
    ActivityResult, DifficultyFeedback
)
from src.algorithms.bkt_engine import BKTEngine


class AdaptiveEngine:
    """
    Adaptive engine for selecting optimal learning challenges based on learner competency.
    
    This engine uses multiple algorithms to recommend challenges:
    - Zone of Proximal Development (ZPD) targeting
    - Competency gap analysis
    - Learning path optimization
    - Difficulty calibration
    """
    
    def __init__(self):
        self.bkt_engine = BKTEngine()
        self.recommendation_cache = {}
        self.adaptation_history = {}
    
    def generate_recommendations(
        self, 
        request: AdaptationRequest,
        available_challenges: List[ChallengeMetadata]
    ) -> AdaptationResponse:
        """
        Generate adaptive challenge recommendations for a learner.
        
        Args:
            request: Adaptation request with learner context
            available_challenges: Pool of available challenges
            
        Returns:
            AdaptationResponse: Personalized recommendations
        """
        # Filter challenges based on prerequisites and exclusions
        eligible_challenges = self._filter_eligible_challenges(
            available_challenges, 
            request.current_competencies,
            request.exclude_challenges
        )
        
        # Score and rank challenges
        scored_challenges = self._score_challenges(
            eligible_challenges,
            request.current_competencies,
            request.learning_goals,
            request.preferred_difficulty,
            request.time_available
        )
        
        # Generate recommendations
        recommendations = self._create_recommendations(
            scored_challenges,
            request.current_competencies,
            request.challenge_types
        )
        
        # Create challenge sequence
        sequence = self._create_challenge_sequence(
            request.learner_id,
            recommendations,
            request
        )
        
        # Determine refresh interval
        refresh_minutes = self._calculate_refresh_interval(request.current_competencies)
        
        return AdaptationResponse(
            learner_id=request.learner_id,
            challenge_sequence=sequence,
            next_challenge=recommendations[0] if recommendations else None,
            alternative_challenges=recommendations[1:4] if len(recommendations) > 1 else [],
            adaptation_metadata=self._generate_adaptation_metadata(request, scored_challenges),
            refresh_in_minutes=refresh_minutes
        )
    
    def adapt_after_activity(
        self,
        learner_id: str,
        activity_result: ActivityResult,
        current_competencies: List[CompetencyLevel],
        difficulty_feedback: Optional[DifficultyFeedback] = None
    ) -> List[CompetencyLevel]:
        """
        Adapt learner model after completing an activity.
        
        Args:
            learner_id: Learner identifier
            activity_result: Result of completed activity
            current_competencies: Current competency levels
            difficulty_feedback: Optional difficulty feedback
            
        Returns:
            List[CompetencyLevel]: Updated competency levels
        """
        # Update competencies using BKT
        updated_competencies = self.bkt_engine.update_multiple_competencies(
            current_competencies,
            activity_result
        )
        
        # Apply difficulty feedback adjustments
        if difficulty_feedback:
            updated_competencies = self._apply_difficulty_feedback(
                updated_competencies,
                difficulty_feedback
            )
        
        # Store adaptation history
        self._store_adaptation_history(learner_id, activity_result, difficulty_feedback)
        
        # Clear recommendation cache for this learner
        self._clear_learner_cache(learner_id)
        
        return updated_competencies
    
    def calculate_optimal_difficulty(
        self,
        competencies: List[CompetencyLevel],
        challenge: ChallengeMetadata
    ) -> float:
        """
        Calculate optimal difficulty for a challenge given learner competencies.
        
        Args:
            competencies: Learner's current competencies
            challenge: Challenge to evaluate
            
        Returns:
            float: Optimal difficulty level (0-1)
        """
        relevant_competencies = [
            comp for comp in competencies 
            if comp.competency_id in challenge.competencies
        ]
        
        if not relevant_competencies:
            return 0.5  # Default difficulty if no relevant competencies
        
        # Calculate weighted average of optimal difficulties
        total_weight = 0
        weighted_difficulty = 0
        
        for competency in relevant_competencies:
            optimal_diff = self.bkt_engine.calculate_optimal_difficulty(competency)
            weight = competency.confidence_level
            
            weighted_difficulty += optimal_diff * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return weighted_difficulty / total_weight
    
    def _filter_eligible_challenges(
        self,
        challenges: List[ChallengeMetadata],
        competencies: List[CompetencyLevel],
        exclude_challenges: List[str]
    ) -> List[ChallengeMetadata]:
        """Filter challenges based on prerequisites and exclusions."""
        competency_ids = {comp.competency_id for comp in competencies}
        mastery_map = {comp.competency_id: comp.mastery_probability for comp in competencies}
        
        eligible = []
        for challenge in challenges:
            # Skip excluded challenges
            if challenge.challenge_id in exclude_challenges:
                continue
            
            # Check prerequisites
            prerequisites_met = True
            for prereq in challenge.prerequisites:
                if prereq not in mastery_map or mastery_map[prereq] < 0.6:
                    prerequisites_met = False
                    break
            
            if prerequisites_met:
                eligible.append(challenge)
        
        return eligible
    
    def _score_challenges(
        self,
        challenges: List[ChallengeMetadata],
        competencies: List[CompetencyLevel],
        learning_goals: List[str],
        preferred_difficulty: Optional[float],
        time_available: Optional[int]
    ) -> List[Tuple[ChallengeMetadata, float]]:
        """Score challenges based on multiple criteria."""
        competency_map = {comp.competency_id: comp for comp in competencies}
        scored_challenges = []
        
        for challenge in challenges:
            score = self._calculate_challenge_score(
                challenge,
                competency_map,
                learning_goals,
                preferred_difficulty,
                time_available
            )
            scored_challenges.append((challenge, score))
        
        # Sort by score (descending)
        scored_challenges.sort(key=lambda x: x[1], reverse=True)
        return scored_challenges
    
    def _calculate_challenge_score(
        self,
        challenge: ChallengeMetadata,
        competency_map: Dict[str, CompetencyLevel],
        learning_goals: List[str],
        preferred_difficulty: Optional[float],
        time_available: Optional[int]
    ) -> float:
        """Calculate a comprehensive score for a challenge."""
        score = 0.0
        
        # 1. Competency alignment score (40% weight)
        competency_score = self._calculate_competency_alignment_score(
            challenge, competency_map
        )
        score += competency_score * 0.4
        
        # 2. Learning goals alignment (25% weight)
        goals_score = self._calculate_goals_alignment_score(challenge, learning_goals)
        score += goals_score * 0.25
        
        # 3. Difficulty appropriateness (20% weight)
        difficulty_score = self._calculate_difficulty_score(
            challenge, competency_map, preferred_difficulty
        )
        score += difficulty_score * 0.2
        
        # 4. Time appropriateness (10% weight)
        time_score = self._calculate_time_score(challenge, time_available)
        score += time_score * 0.1
        
        # 5. Variety bonus (5% weight)
        variety_score = self._calculate_variety_score(challenge)
        score += variety_score * 0.05
        
        return score
    
    def _calculate_competency_alignment_score(
        self,
        challenge: ChallengeMetadata,
        competency_map: Dict[str, CompetencyLevel]
    ) -> float:
        """Calculate how well challenge aligns with learner competencies."""
        if not challenge.competencies:
            return 0.0
        
        total_score = 0.0
        for comp_id in challenge.competencies:
            if comp_id in competency_map:
                competency = competency_map[comp_id]
                mastery = competency.mastery_probability
                
                # Optimal learning happens in ZPD (0.3-0.7 mastery range)
                if 0.3 <= mastery <= 0.7:
                    comp_score = 1.0
                elif mastery < 0.3:
                    comp_score = 0.6  # Challenging but possible
                else:  # mastery > 0.7
                    comp_score = 0.4  # Review/reinforcement
                
                # Weight by confidence
                comp_score *= competency.confidence_level
                total_score += comp_score
            else:
                # Unknown competency - moderate score
                total_score += 0.5
        
        return total_score / len(challenge.competencies)
    
    def _calculate_goals_alignment_score(
        self,
        challenge: ChallengeMetadata,
        learning_goals: List[str]
    ) -> float:
        """Calculate alignment with learner's goals."""
        if not learning_goals:
            return 0.5  # Neutral if no specific goals
        
        goal_set = set(learning_goals)
        challenge_comps = set(challenge.competencies)
        
        overlap = len(goal_set.intersection(challenge_comps))
        return overlap / len(goal_set) if goal_set else 0.5
    
    def _calculate_difficulty_score(
        self,
        challenge: ChallengeMetadata,
        competency_map: Dict[str, CompetencyLevel],
        preferred_difficulty: Optional[float]
    ) -> float:
        """Calculate difficulty appropriateness score."""
        optimal_difficulty = self.calculate_optimal_difficulty(
            list(competency_map.values()),
            challenge
        )
        
        actual_difficulty = challenge.difficulty_level
        
        # Score based on how close actual difficulty is to optimal
        difficulty_diff = abs(actual_difficulty - optimal_difficulty)
        difficulty_score = max(0.0, 1.0 - difficulty_diff * 2)
        
        # Adjust for learner preference
        if preferred_difficulty is not None:
            pref_diff = abs(actual_difficulty - preferred_difficulty)
            pref_score = max(0.0, 1.0 - pref_diff * 2)
            difficulty_score = (difficulty_score + pref_score) / 2
        
        return difficulty_score
    
    def _calculate_time_score(
        self,
        challenge: ChallengeMetadata,
        time_available: Optional[int]
    ) -> float:
        """Calculate time appropriateness score."""
        if time_available is None:
            return 1.0  # No time constraint
        
        if challenge.estimated_duration <= time_available:
            return 1.0
        elif challenge.estimated_duration <= time_available * 1.2:
            return 0.7  # Slightly over time
        else:
            return 0.3  # Significantly over time
    
    def _calculate_variety_score(self, challenge: ChallengeMetadata) -> float:
        """Calculate variety bonus to encourage diverse challenge types."""
        # This would be enhanced with actual history tracking
        # For now, return a random small bonus
        return random.uniform(0.0, 0.2)
    
    def _create_recommendations(
        self,
        scored_challenges: List[Tuple[ChallengeMetadata, float]],
        competencies: List[CompetencyLevel],
        preferred_types: List[str]
    ) -> List[AdaptiveRecommendation]:
        """Create recommendation objects from scored challenges."""
        recommendations = []
        
        for challenge, score in scored_challenges[:10]:  # Top 10 challenges
            # Filter by preferred types if specified
            if preferred_types and challenge.challenge_type not in preferred_types:
                continue
            
            # Get relevant competencies
            relevant_comps = [
                comp for comp in competencies 
                if comp.competency_id in challenge.competencies
            ]
            
            # Calculate optimal difficulty
            optimal_difficulty = self.calculate_optimal_difficulty(
                competencies, challenge
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(challenge, relevant_comps, score)
            
            recommendation = AdaptiveRecommendation(
                challenge=challenge,
                recommendation_score=score,
                target_competencies=relevant_comps,
                reasoning=reasoning,
                optimal_difficulty=optimal_difficulty
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_reasoning(
        self,
        challenge: ChallengeMetadata,
        competencies: List[CompetencyLevel],
        score: float
    ) -> str:
        """Generate human-readable reasoning for recommendation."""
        if not competencies:
            return f"This {challenge.challenge_type} challenge will help you learn new skills."
        
        avg_mastery = np.mean([c.mastery_probability for c in competencies])
        
        if avg_mastery < 0.4:
            return f"This challenge will help you build foundational skills in {', '.join([c.competency_name for c in competencies[:2]])}."
        elif avg_mastery < 0.7:
            return f"Perfect for developing your {', '.join([c.competency_name for c in competencies[:2]])} skills further."
        else:
            return f"Great for reinforcing and mastering {', '.join([c.competency_name for c in competencies[:2]])}."
    
    def _create_challenge_sequence(
        self,
        learner_id: str,
        recommendations: List[AdaptiveRecommendation],
        request: AdaptationRequest
    ) -> ChallengeSequence:
        """Create a challenge sequence from recommendations."""
        sequence_id = f"{learner_id}_{datetime.utcnow().isoformat()}"
        expires_at = datetime.utcnow() + timedelta(hours=2)  # Refresh every 2 hours
        
        return ChallengeSequence(
            learner_id=learner_id,
            recommendations=recommendations,
            sequence_id=sequence_id,
            expires_at=expires_at,
            adaptation_context={
                "learning_goals": request.learning_goals,
                "time_available": request.time_available,
                "preferred_difficulty": request.preferred_difficulty,
                "competency_snapshot": [
                    {
                        "id": comp.competency_id,
                        "mastery": comp.mastery_probability,
                        "confidence": comp.confidence_level
                    }
                    for comp in request.current_competencies
                ]
            }
        )
    
    def _calculate_refresh_interval(self, competencies: List[CompetencyLevel]) -> int:
        """Calculate when recommendations should be refreshed."""
        avg_confidence = np.mean([c.confidence_level for c in competencies])
        
        if avg_confidence < 0.5:
            return 30  # Refresh more frequently for uncertain competencies
        elif avg_confidence < 0.8:
            return 60  # Standard refresh interval
        else:
            return 120  # Less frequent refresh for stable competencies
    
    def _generate_adaptation_metadata(
        self,
        request: AdaptationRequest,
        scored_challenges: List[Tuple[ChallengeMetadata, float]]
    ) -> Dict[str, any]:
        """Generate metadata about the adaptation process."""
        return {
            "total_challenges_considered": len(scored_challenges),
            "average_score": np.mean([score for _, score in scored_challenges]) if scored_challenges else 0,
            "adaptation_timestamp": datetime.utcnow().isoformat(),
            "learner_profile_summary": {
                "num_competencies": len(request.current_competencies),
                "avg_mastery": np.mean([c.mastery_probability for c in request.current_competencies]),
                "avg_confidence": np.mean([c.confidence_level for c in request.current_competencies])
            }
        }
    
    def _apply_difficulty_feedback(
        self,
        competencies: List[CompetencyLevel],
        feedback: DifficultyFeedback
    ) -> List[CompetencyLevel]:
        """Apply difficulty feedback to adjust competency estimates."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated feedback integration
        
        updated_competencies = []
        for competency in competencies:
            if competency.competency_id in [feedback.challenge_id]:  # Simplified mapping
                # Adjust confidence based on feedback accuracy
                perceived_diff = feedback.perceived_difficulty
                actual_diff = feedback.actual_difficulty
                
                diff_error = abs(perceived_diff - actual_diff)
                if diff_error < 0.2:
                    # Good calibration - increase confidence
                    new_confidence = min(0.95, competency.confidence_level + 0.05)
                else:
                    # Poor calibration - decrease confidence
                    new_confidence = max(0.1, competency.confidence_level - 0.1)
                
                updated_competency = CompetencyLevel(
                    _id=competency.competency_id,
                    competency_name=competency.competency_name,
                    mastery_probability=competency.mastery_probability,
                    confidence_level=new_confidence,
                    last_updated=datetime.utcnow(),
                    bkt_parameters=competency.bkt_parameters
                )
                updated_competencies.append(updated_competency)
            else:
                updated_competencies.append(competency)
        
        return updated_competencies
    
    def _store_adaptation_history(
        self,
        learner_id: str,
        activity_result: ActivityResult,
        difficulty_feedback: Optional[DifficultyFeedback]
    ):
        """Store adaptation history for analysis."""
        if learner_id not in self.adaptation_history:
            self.adaptation_history[learner_id] = []
        
        history_entry = {
            "timestamp": datetime.utcnow(),
            "activity_result": activity_result,
            "difficulty_feedback": difficulty_feedback
        }
        
        self.adaptation_history[learner_id].append(history_entry)
        
        # Keep only last 100 entries per learner
        if len(self.adaptation_history[learner_id]) > 100:
            self.adaptation_history[learner_id] = self.adaptation_history[learner_id][-100:]
    
    def _clear_learner_cache(self, learner_id: str):
        """Clear cached recommendations for a learner."""
        keys_to_remove = [key for key in self.recommendation_cache.keys() if key.startswith(learner_id)]
        for key in keys_to_remove:
            del self.recommendation_cache[key]