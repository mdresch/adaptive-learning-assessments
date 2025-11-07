"""
Bayesian Knowledge Tracing (BKT) Engine.

This module implements the core BKT algorithm for tracking learner mastery
of micro-competencies based on their interactions with learning activities.
"""

import math
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging

from ..models.mastery import (
    LearnerInteraction, 
    MasteryLevel, 
    BKTParameters,
    MicroCompetency
)

logger = logging.getLogger(__name__)


class BKTEngine:
    """
    Bayesian Knowledge Tracing engine for updating learner mastery probabilities.
    
    The BKT model tracks the probability that a learner has mastered a skill
    based on their performance on activities that require that skill.
    """
    
    def __init__(self):
        """Initialize the BKT engine."""
        self.default_parameters = BKTParameters()
    
    def update_mastery(
        self, 
        current_mastery: MasteryLevel, 
        interaction: LearnerInteraction
    ) -> MasteryLevel:
        """
        Update mastery level based on a new learner interaction.
        
        Args:
            current_mastery: Current mastery level for the competency
            interaction: New learner interaction data
            
        Returns:
            Updated mastery level
        """
        try:
            # Extract BKT parameters
            params = current_mastery.bkt_parameters
            
            # Get the current probability of mastery
            p_mastery_before = current_mastery.current_mastery
            
            # Determine if the interaction was correct
            is_correct = self._determine_correctness(interaction)
            
            # Update mastery probability using BKT
            p_mastery_after = self._bkt_update(
                p_mastery_before, 
                is_correct, 
                params
            )
            
            # Update performance statistics
            updated_mastery = self._update_performance_stats(
                current_mastery, 
                interaction, 
                p_mastery_after
            )
            
            # Check if mastery threshold is reached
            self._check_mastery_threshold(updated_mastery)
            
            logger.info(
                f"Updated mastery for learner {current_mastery.learner_id}, "
                f"competency {current_mastery.competency_id}: "
                f"{p_mastery_before:.3f} -> {p_mastery_after:.3f}"
            )
            
            return updated_mastery
            
        except Exception as e:
            logger.error(f"Error updating mastery: {str(e)}")
            raise
    
    def _determine_correctness(self, interaction: LearnerInteraction) -> bool:
        """
        Determine if an interaction represents correct performance.
        
        Args:
            interaction: Learner interaction data
            
        Returns:
            Boolean indicating correctness
        """
        # If is_correct is explicitly set, use it
        if interaction.is_correct is not None:
            return interaction.is_correct
        
        # If score is available, use a threshold
        if interaction.score is not None:
            # Consider score >= 0.7 as correct
            return interaction.score >= 0.7
        
        # Default to False if no clear indication
        logger.warning(
            f"Could not determine correctness for interaction {interaction.id}, "
            f"defaulting to False"
        )
        return False
    
    def _bkt_update(
        self, 
        p_mastery_before: float, 
        is_correct: bool, 
        params: BKTParameters
    ) -> float:
        """
        Apply the BKT update formula.
        
        Args:
            p_mastery_before: Probability of mastery before this interaction
            is_correct: Whether the interaction was correct
            params: BKT parameters
            
        Returns:
            Updated probability of mastery
        """
        # BKT update formulas
        if is_correct:
            # P(L_n+1 = 1 | correct) = 
            # [P(L_n = 1) * (1 - P(S))] / [P(L_n = 1) * (1 - P(S)) + (1 - P(L_n = 1)) * P(G)]
            numerator = p_mastery_before * (1 - params.slip_probability)
            denominator = (
                p_mastery_before * (1 - params.slip_probability) + 
                (1 - p_mastery_before) * params.guess_probability
            )
        else:
            # P(L_n+1 = 1 | incorrect) = 
            # [P(L_n = 1) * P(S)] / [P(L_n = 1) * P(S) + (1 - P(L_n = 1)) * (1 - P(G))]
            numerator = p_mastery_before * params.slip_probability
            denominator = (
                p_mastery_before * params.slip_probability + 
                (1 - p_mastery_before) * (1 - params.guess_probability)
            )
        
        # Avoid division by zero
        if denominator == 0:
            logger.warning("Division by zero in BKT update, returning previous mastery")
            return p_mastery_before
        
        p_mastery_given_evidence = numerator / denominator
        
        # Apply learning rate (probability of transitioning from not-mastered to mastered)
        p_mastery_after = (
            p_mastery_given_evidence + 
            (1 - p_mastery_given_evidence) * params.learning_rate
        )
        
        # Ensure probability stays within [0, 1]
        return max(0.0, min(1.0, p_mastery_after))
    
    def _update_performance_stats(
        self, 
        current_mastery: MasteryLevel, 
        interaction: LearnerInteraction, 
        new_mastery_prob: float
    ) -> MasteryLevel:
        """
        Update performance statistics in the mastery level.
        
        Args:
            current_mastery: Current mastery level
            interaction: New interaction
            new_mastery_prob: Updated mastery probability
            
        Returns:
            Updated mastery level with new statistics
        """
        # Create a copy to avoid modifying the original
        updated = current_mastery.copy(deep=True)
        
        # Update mastery probability
        updated.current_mastery = new_mastery_prob
        
        # Update interaction counts
        updated.total_interactions += 1
        if self._determine_correctness(interaction):
            updated.correct_interactions += 1
        
        # Update average score if score is available
        if interaction.score is not None:
            if updated.average_score is None:
                updated.average_score = interaction.score
            else:
                # Weighted average with more weight on recent interactions
                weight = 0.1  # Weight for new score
                updated.average_score = (
                    (1 - weight) * updated.average_score + 
                    weight * interaction.score
                )
        
        # Update recent performance (keep last 10 scores)
        if interaction.score is not None:
            updated.recent_performance.append(interaction.score)
            if len(updated.recent_performance) > 10:
                updated.recent_performance = updated.recent_performance[-10:]
        
        # Update timestamps
        if updated.first_interaction is None:
            updated.first_interaction = interaction.completed_at
        updated.last_interaction = interaction.completed_at
        updated.updated_at = datetime.utcnow()
        
        return updated
    
    def _check_mastery_threshold(self, mastery_level: MasteryLevel) -> None:
        """
        Check if mastery threshold has been reached and update accordingly.
        
        Args:
            mastery_level: Mastery level to check
        """
        if (mastery_level.current_mastery >= mastery_level.mastery_threshold and 
            not mastery_level.is_mastered):
            mastery_level.is_mastered = True
            mastery_level.mastery_achieved_at = datetime.utcnow()
            logger.info(
                f"Mastery achieved for learner {mastery_level.learner_id}, "
                f"competency {mastery_level.competency_id}"
            )
    
    def batch_update_mastery(
        self, 
        mastery_levels: List[MasteryLevel], 
        interactions: List[LearnerInteraction]
    ) -> List[MasteryLevel]:
        """
        Update multiple mastery levels based on multiple interactions.
        
        Args:
            mastery_levels: List of current mastery levels
            interactions: List of new interactions
            
        Returns:
            List of updated mastery levels
        """
        # Group interactions by learner and competency
        interaction_groups = self._group_interactions(interactions)
        
        # Create a lookup for mastery levels
        mastery_lookup = {
            (ml.learner_id, ml.competency_id): ml 
            for ml in mastery_levels
        }
        
        updated_mastery_levels = []
        
        for (learner_id, competency_id), interaction_list in interaction_groups.items():
            current_mastery = mastery_lookup.get((learner_id, competency_id))
            
            if current_mastery is None:
                logger.warning(
                    f"No mastery level found for learner {learner_id}, "
                    f"competency {competency_id}"
                )
                continue
            
            # Apply interactions sequentially
            updated_mastery = current_mastery
            for interaction in sorted(interaction_list, key=lambda x: x.completed_at):
                updated_mastery = self.update_mastery(updated_mastery, interaction)
            
            updated_mastery_levels.append(updated_mastery)
        
        return updated_mastery_levels
    
    def _group_interactions(
        self, 
        interactions: List[LearnerInteraction]
    ) -> Dict[Tuple[str, str], List[LearnerInteraction]]:
        """
        Group interactions by learner and competency.
        
        Args:
            interactions: List of interactions to group
            
        Returns:
            Dictionary mapping (learner_id, competency_id) to list of interactions
        """
        groups = {}
        
        for interaction in interactions:
            for competency_id in interaction.competency_ids:
                key = (interaction.learner_id, competency_id)
                if key not in groups:
                    groups[key] = []
                groups[key].append(interaction)
        
        return groups
    
    def calculate_confidence_interval(
        self, 
        mastery_level: MasteryLevel, 
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for mastery probability.
        
        Args:
            mastery_level: Mastery level to analyze
            confidence: Confidence level (default 0.95 for 95% CI)
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if mastery_level.total_interactions < 3:
            # Not enough data for meaningful confidence interval
            return (0.0, 1.0)
        
        # Use Wilson score interval for binomial proportion
        n = mastery_level.total_interactions
        p = mastery_level.correct_interactions / n
        z = 1.96 if confidence == 0.95 else 2.576  # Z-score for confidence level
        
        denominator = 1 + (z**2 / n)
        center = (p + (z**2 / (2 * n))) / denominator
        margin = (z / denominator) * math.sqrt((p * (1 - p) / n) + (z**2 / (4 * n**2)))
        
        lower_bound = max(0.0, center - margin)
        upper_bound = min(1.0, center + margin)
        
        return (lower_bound, upper_bound)
    
    def get_learning_velocity(
        self, 
        mastery_level: MasteryLevel, 
        time_window_days: int = 7
    ) -> Optional[float]:
        """
        Calculate learning velocity (rate of mastery improvement).
        
        Args:
            mastery_level: Mastery level to analyze
            time_window_days: Time window for velocity calculation
            
        Returns:
            Learning velocity (mastery change per day) or None if insufficient data
        """
        if (mastery_level.first_interaction is None or 
            mastery_level.last_interaction is None or
            mastery_level.total_interactions < 2):
            return None
        
        time_diff = mastery_level.last_interaction - mastery_level.first_interaction
        days_elapsed = time_diff.total_seconds() / (24 * 3600)
        
        if days_elapsed < 1:
            return None
        
        # Estimate initial mastery (could be improved with historical data)
        initial_mastery = mastery_level.bkt_parameters.prior_knowledge
        current_mastery = mastery_level.current_mastery
        
        velocity = (current_mastery - initial_mastery) / days_elapsed
        return velocity
    
    def recommend_practice_intensity(
        self, 
        mastery_level: MasteryLevel
    ) -> str:
        """
        Recommend practice intensity based on current mastery state.
        
        Args:
            mastery_level: Mastery level to analyze
            
        Returns:
            Recommendation string
        """
        mastery = mastery_level.current_mastery
        
        if mastery < 0.3:
            return "intensive"  # Need lots of practice
        elif mastery < 0.6:
            return "moderate"   # Regular practice needed
        elif mastery < 0.8:
            return "light"      # Light practice to maintain
        else:
            return "maintenance"  # Just occasional review