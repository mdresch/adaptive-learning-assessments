"""
Bayesian Knowledge Tracing (BKT) algorithm implementation for competency evaluation.
"""
import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import numpy as np
from src.models.adaptive_models import BKTParameters, CompetencyLevel, ActivityResult


class BKTEngine:
    """
    Bayesian Knowledge Tracing engine for tracking learner competency.
    
    This implementation uses the standard 4-parameter BKT model:
    - P(L0): Prior probability of knowing the skill
    - P(T): Probability of learning the skill (transition)
    - P(S): Probability of slip (making mistake when knowing)
    - P(G): Probability of guess (correct answer when not knowing)
    """
    
    def __init__(self):
        self.default_parameters = BKTParameters()
    
    def initialize_competency(
        self, 
        competency_id: str, 
        competency_name: str,
        custom_parameters: Optional[BKTParameters] = None
    ) -> CompetencyLevel:
        """
        Initialize a new competency for a learner.
        
        Args:
            competency_id: Unique identifier for the competency
            competency_name: Human-readable name of the competency
            custom_parameters: Custom BKT parameters, uses defaults if None
            
        Returns:
            CompetencyLevel: Initial competency level
        """
        parameters = custom_parameters or self.default_parameters
        
        return CompetencyLevel(
            _id=competency_id,
            competency_name=competency_name,
            mastery_probability=parameters.prior_knowledge,
            confidence_level=0.5,  # Medium confidence initially
            last_updated=datetime.utcnow(),
            bkt_parameters=parameters
        )
    
    def update_competency(
        self, 
        current_competency: CompetencyLevel, 
        activity_result: ActivityResult
    ) -> CompetencyLevel:
        """
        Update competency level based on activity result using BKT.
        
        Args:
            current_competency: Current competency state
            activity_result: Result of the completed activity
            
        Returns:
            CompetencyLevel: Updated competency level
        """
        params = current_competency.bkt_parameters
        current_mastery = current_competency.mastery_probability
        
        # Calculate probability of correct response given current mastery
        p_correct_given_mastery = (
            current_mastery * (1 - params.slip_probability) + 
            (1 - current_mastery) * params.guess_probability
        )
        
        # Update mastery probability based on observed performance
        if activity_result.success:
            # Correct response - update using Bayes' rule
            numerator = current_mastery * (1 - params.slip_probability)
            new_mastery = numerator / p_correct_given_mastery if p_correct_given_mastery > 0 else current_mastery
        else:
            # Incorrect response - update using Bayes' rule
            numerator = current_mastery * params.slip_probability
            denominator = 1 - p_correct_given_mastery
            new_mastery = numerator / denominator if denominator > 0 else current_mastery
        
        # Apply learning transition
        final_mastery = new_mastery + (1 - new_mastery) * params.learning_rate
        
        # Ensure mastery probability stays within bounds
        final_mastery = max(0.0, min(1.0, final_mastery))
        
        # Calculate confidence based on number of observations and consistency
        confidence = self._calculate_confidence(current_competency, activity_result)
        
        return CompetencyLevel(
            _id=current_competency.competency_id,
            competency_name=current_competency.competency_name,
            mastery_probability=final_mastery,
            confidence_level=confidence,
            last_updated=datetime.utcnow(),
            bkt_parameters=params
        )
    
    def update_multiple_competencies(
        self, 
        competencies: List[CompetencyLevel], 
        activity_result: ActivityResult
    ) -> List[CompetencyLevel]:
        """
        Update multiple competencies based on a single activity result.
        
        Args:
            competencies: List of competencies to update
            activity_result: Result of the completed activity
            
        Returns:
            List[CompetencyLevel]: Updated competencies
        """
        updated_competencies = []
        
        for competency in competencies:
            if competency.competency_id in activity_result.competencies_addressed:
                # Apply full update for directly addressed competencies
                updated_competency = self.update_competency(competency, activity_result)
            else:
                # Apply partial update for related competencies
                updated_competency = self._apply_transfer_learning(competency, activity_result)
            
            updated_competencies.append(updated_competency)
        
        return updated_competencies
    
    def predict_performance(
        self, 
        competency: CompetencyLevel, 
        challenge_difficulty: float
    ) -> Tuple[float, float]:
        """
        Predict learner performance on a challenge given current competency.
        
        Args:
            competency: Current competency level
            challenge_difficulty: Difficulty level of the challenge (0-1)
            
        Returns:
            Tuple[float, float]: (predicted_success_probability, confidence)
        """
        mastery = competency.mastery_probability
        params = competency.bkt_parameters
        
        # Adjust for challenge difficulty
        difficulty_factor = 1.0 - challenge_difficulty
        adjusted_slip = params.slip_probability + (challenge_difficulty * 0.3)
        adjusted_slip = min(0.5, adjusted_slip)  # Cap slip probability
        
        # Calculate predicted success probability
        success_prob = (
            mastery * (1 - adjusted_slip) + 
            (1 - mastery) * params.guess_probability * difficulty_factor
        )
        
        # Confidence decreases with higher difficulty and lower mastery
        confidence = competency.confidence_level * (1 - challenge_difficulty * 0.5)
        
        return success_prob, confidence
    
    def calculate_optimal_difficulty(
        self, 
        competency: CompetencyLevel, 
        target_success_rate: float = 0.7
    ) -> float:
        """
        Calculate optimal challenge difficulty for a given competency level.
        
        Args:
            competency: Current competency level
            target_success_rate: Desired success rate (default 0.7 for optimal learning)
            
        Returns:
            float: Optimal difficulty level (0-1)
        """
        mastery = competency.mastery_probability
        params = competency.bkt_parameters
        
        # Use binary search to find difficulty that yields target success rate
        low, high = 0.0, 1.0
        tolerance = 0.01
        max_iterations = 50
        
        for _ in range(max_iterations):
            mid = (low + high) / 2
            predicted_success, _ = self.predict_performance(competency, mid)
            
            if abs(predicted_success - target_success_rate) < tolerance:
                return mid
            elif predicted_success > target_success_rate:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def _calculate_confidence(
        self, 
        current_competency: CompetencyLevel, 
        activity_result: ActivityResult
    ) -> float:
        """
        Calculate confidence level based on observation history and consistency.
        
        Args:
            current_competency: Current competency state
            activity_result: Latest activity result
            
        Returns:
            float: Updated confidence level
        """
        # Base confidence increases with more observations
        base_confidence = min(0.9, current_competency.confidence_level + 0.05)
        
        # Adjust based on consistency with prediction
        mastery = current_competency.mastery_probability
        expected_success = mastery > 0.5
        actual_success = activity_result.success
        
        if expected_success == actual_success:
            # Consistent with prediction - increase confidence
            confidence_adjustment = 0.1
        else:
            # Inconsistent with prediction - decrease confidence
            confidence_adjustment = -0.15
        
        final_confidence = base_confidence + confidence_adjustment
        return max(0.1, min(0.95, final_confidence))
    
    def _apply_transfer_learning(
        self, 
        competency: CompetencyLevel, 
        activity_result: ActivityResult
    ) -> CompetencyLevel:
        """
        Apply transfer learning effects to related competencies.
        
        Args:
            competency: Competency to update via transfer
            activity_result: Activity result from related competency
            
        Returns:
            CompetencyLevel: Updated competency with transfer effects
        """
        # Apply small positive transfer for successful activities
        transfer_rate = 0.05 if activity_result.success else -0.02
        
        current_mastery = competency.mastery_probability
        new_mastery = current_mastery + (transfer_rate * (1 - current_mastery))
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        return CompetencyLevel(
            _id=competency.competency_id,
            competency_name=competency.competency_name,
            mastery_probability=new_mastery,
            confidence_level=competency.confidence_level,
            last_updated=datetime.utcnow(),
            bkt_parameters=competency.bkt_parameters
        )
    
    def get_competency_insights(
        self, 
        competencies: List[CompetencyLevel]
    ) -> Dict[str, any]:
        """
        Generate insights about learner's overall competency profile.
        
        Args:
            competencies: List of learner's competencies
            
        Returns:
            Dict: Insights about competency profile
        """
        if not competencies:
            return {"error": "No competencies provided"}
        
        masteries = [c.mastery_probability for c in competencies]
        confidences = [c.confidence_level for c in competencies]
        
        insights = {
            "overall_mastery": np.mean(masteries),
            "mastery_variance": np.var(masteries),
            "average_confidence": np.mean(confidences),
            "strong_competencies": [
                c.competency_name for c in competencies 
                if c.mastery_probability > 0.8 and c.confidence_level > 0.7
            ],
            "developing_competencies": [
                c.competency_name for c in competencies 
                if 0.3 <= c.mastery_probability <= 0.7
            ],
            "weak_competencies": [
                c.competency_name for c in competencies 
                if c.mastery_probability < 0.3
            ],
            "uncertain_competencies": [
                c.competency_name for c in competencies 
                if c.confidence_level < 0.5
            ]
        }
        
        return insights