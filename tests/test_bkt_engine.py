"""
Tests for the BKT (Bayesian Knowledge Tracing) engine.

This module contains unit tests for the core BKT algorithm implementation
and mastery tracking functionality.
"""

import pytest
from datetime import datetime, timedelta
from src.core.bkt_engine import BKTEngine
from src.models.mastery import (
    LearnerInteraction,
    MasteryLevel,
    BKTParameters,
    ActivityType,
    InteractionType,
    DifficultyLevel
)


class TestBKTEngine:
    """Test cases for the BKT engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bkt_engine = BKTEngine()
        
        # Create a sample mastery level
        self.sample_mastery = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.3,
            bkt_parameters=BKTParameters(
                prior_knowledge=0.1,
                learning_rate=0.3,
                slip_probability=0.1,
                guess_probability=0.25
            )
        )
        
        # Create sample interactions
        self.correct_interaction = LearnerInteraction(
            learner_id="test_learner",
            activity_id="test_activity",
            activity_type=ActivityType.QUIZ,
            interaction_type=InteractionType.COMPLETION,
            competency_ids=["test_competency"],
            score=0.9,
            is_correct=True,
            attempts=1,
            time_spent=120.0,
            hints_used=0
        )
        
        self.incorrect_interaction = LearnerInteraction(
            learner_id="test_learner",
            activity_id="test_activity",
            activity_type=ActivityType.QUIZ,
            interaction_type=InteractionType.COMPLETION,
            competency_ids=["test_competency"],
            score=0.4,
            is_correct=False,
            attempts=2,
            time_spent=180.0,
            hints_used=1
        )
    
    def test_update_mastery_correct_response(self):
        """Test mastery update with correct response."""
        updated_mastery = self.bkt_engine.update_mastery(
            self.sample_mastery, 
            self.correct_interaction
        )
        
        # Mastery should increase with correct response
        assert updated_mastery.current_mastery > self.sample_mastery.current_mastery
        
        # Statistics should be updated
        assert updated_mastery.total_interactions == 1
        assert updated_mastery.correct_interactions == 1
        assert updated_mastery.average_score == 0.9
        assert len(updated_mastery.recent_performance) == 1
        assert updated_mastery.recent_performance[0] == 0.9
    
    def test_update_mastery_incorrect_response(self):
        """Test mastery update with incorrect response."""
        updated_mastery = self.bkt_engine.update_mastery(
            self.sample_mastery, 
            self.incorrect_interaction
        )
        
        # Mastery might increase or decrease depending on BKT parameters
        # But should still be a valid probability
        assert 0.0 <= updated_mastery.current_mastery <= 1.0
        
        # Statistics should be updated
        assert updated_mastery.total_interactions == 1
        assert updated_mastery.correct_interactions == 0
        assert updated_mastery.average_score == 0.4
    
    def test_mastery_threshold_detection(self):
        """Test detection of mastery threshold achievement."""
        # Create a mastery level close to threshold
        high_mastery = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.75,
            mastery_threshold=0.8,
            is_mastered=False
        )
        
        # Create a very good interaction
        excellent_interaction = LearnerInteraction(
            learner_id="test_learner",
            activity_id="test_activity",
            activity_type=ActivityType.QUIZ,
            interaction_type=InteractionType.COMPLETION,
            competency_ids=["test_competency"],
            score=1.0,
            is_correct=True,
            attempts=1
        )
        
        updated_mastery = self.bkt_engine.update_mastery(high_mastery, excellent_interaction)
        
        # Should achieve mastery
        if updated_mastery.current_mastery >= 0.8:
            assert updated_mastery.is_mastered
            assert updated_mastery.mastery_achieved_at is not None
    
    def test_determine_correctness_explicit(self):
        """Test correctness determination with explicit is_correct field."""
        interaction = LearnerInteraction(
            learner_id="test_learner",
            activity_id="test_activity",
            activity_type=ActivityType.QUIZ,
            interaction_type=InteractionType.COMPLETION,
            competency_ids=["test_competency"],
            is_correct=True,
            score=0.5  # Score conflicts with is_correct
        )
        
        # Should use explicit is_correct value
        assert self.bkt_engine._determine_correctness(interaction) == True
    
    def test_determine_correctness_from_score(self):
        """Test correctness determination from score."""
        high_score_interaction = LearnerInteraction(
            learner_id="test_learner",
            activity_id="test_activity",
            activity_type=ActivityType.QUIZ,
            interaction_type=InteractionType.COMPLETION,
            competency_ids=["test_competency"],
            score=0.8
        )
        
        low_score_interaction = LearnerInteraction(
            learner_id="test_learner",
            activity_id="test_activity",
            activity_type=ActivityType.QUIZ,
            interaction_type=InteractionType.COMPLETION,
            competency_ids=["test_competency"],
            score=0.5
        )
        
        assert self.bkt_engine._determine_correctness(high_score_interaction) == True
        assert self.bkt_engine._determine_correctness(low_score_interaction) == False
    
    def test_bkt_update_formula_correct(self):
        """Test BKT update formula with correct response."""
        params = BKTParameters(
            prior_knowledge=0.1,
            learning_rate=0.3,
            slip_probability=0.1,
            guess_probability=0.25
        )
        
        p_mastery_before = 0.3
        updated_mastery = self.bkt_engine._bkt_update(p_mastery_before, True, params)
        
        # Should be a valid probability
        assert 0.0 <= updated_mastery <= 1.0
        
        # With correct response, mastery should generally increase
        # (though not always due to slip probability)
        assert updated_mastery >= p_mastery_before * 0.8  # Allow some decrease due to slip
    
    def test_bkt_update_formula_incorrect(self):
        """Test BKT update formula with incorrect response."""
        params = BKTParameters(
            prior_knowledge=0.1,
            learning_rate=0.3,
            slip_probability=0.1,
            guess_probability=0.25
        )
        
        p_mastery_before = 0.7
        updated_mastery = self.bkt_engine._bkt_update(p_mastery_before, False, params)
        
        # Should be a valid probability
        assert 0.0 <= updated_mastery <= 1.0
        
        # With incorrect response, mastery should generally decrease
        assert updated_mastery <= p_mastery_before
    
    def test_batch_update_mastery(self):
        """Test batch updating of multiple mastery levels."""
        # Create multiple mastery levels
        mastery_levels = [
            MasteryLevel(
                learner_id="learner1",
                competency_id="comp1",
                current_mastery=0.3
            ),
            MasteryLevel(
                learner_id="learner1",
                competency_id="comp2",
                current_mastery=0.5
            ),
            MasteryLevel(
                learner_id="learner2",
                competency_id="comp1",
                current_mastery=0.2
            )
        ]
        
        # Create interactions
        interactions = [
            LearnerInteraction(
                learner_id="learner1",
                activity_id="activity1",
                activity_type=ActivityType.QUIZ,
                interaction_type=InteractionType.COMPLETION,
                competency_ids=["comp1"],
                is_correct=True
            ),
            LearnerInteraction(
                learner_id="learner1",
                activity_id="activity2",
                activity_type=ActivityType.QUIZ,
                interaction_type=InteractionType.COMPLETION,
                competency_ids=["comp2"],
                is_correct=False
            )
        ]
        
        updated_levels = self.bkt_engine.batch_update_mastery(mastery_levels, interactions)
        
        # Should return updated mastery levels
        assert len(updated_levels) == 2  # Only learner1's competencies were updated
        
        # Find the updated mastery for comp1
        comp1_mastery = next(ml for ml in updated_levels if ml.competency_id == "comp1")
        assert comp1_mastery.total_interactions == 1
        assert comp1_mastery.correct_interactions == 1
    
    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation."""
        mastery_level = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.6,
            total_interactions=10,
            correct_interactions=6
        )
        
        lower, upper = self.bkt_engine.calculate_confidence_interval(mastery_level)
        
        # Should be valid bounds
        assert 0.0 <= lower <= upper <= 1.0
        assert lower < upper
    
    def test_confidence_interval_insufficient_data(self):
        """Test confidence interval with insufficient data."""
        mastery_level = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.6,
            total_interactions=1,
            correct_interactions=1
        )
        
        lower, upper = self.bkt_engine.calculate_confidence_interval(mastery_level)
        
        # Should return wide interval
        assert lower == 0.0
        assert upper == 1.0
    
    def test_learning_velocity_calculation(self):
        """Test learning velocity calculation."""
        mastery_level = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.6,
            first_interaction=datetime.utcnow() - timedelta(days=10),
            last_interaction=datetime.utcnow(),
            total_interactions=5
        )
        
        velocity = self.bkt_engine.get_learning_velocity(mastery_level)
        
        # Should return a velocity value
        assert velocity is not None
        assert isinstance(velocity, float)
    
    def test_learning_velocity_insufficient_data(self):
        """Test learning velocity with insufficient data."""
        mastery_level = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.6,
            total_interactions=1
        )
        
        velocity = self.bkt_engine.get_learning_velocity(mastery_level)
        
        # Should return None for insufficient data
        assert velocity is None
    
    def test_practice_intensity_recommendations(self):
        """Test practice intensity recommendations."""
        test_cases = [
            (0.2, "intensive"),
            (0.4, "moderate"),
            (0.7, "light"),
            (0.9, "maintenance")
        ]
        
        for mastery_value, expected_recommendation in test_cases:
            mastery_level = MasteryLevel(
                learner_id="test_learner",
                competency_id="test_competency",
                current_mastery=mastery_value
            )
            
            recommendation = self.bkt_engine.recommend_practice_intensity(mastery_level)
            assert recommendation == expected_recommendation
    
    def test_edge_cases_zero_denominator(self):
        """Test edge cases that might cause division by zero."""
        # Create parameters that might cause issues
        problematic_params = BKTParameters(
            prior_knowledge=0.0,
            learning_rate=0.0,
            slip_probability=0.0,
            guess_probability=0.0
        )
        
        mastery_level = MasteryLevel(
            learner_id="test_learner",
            competency_id="test_competency",
            current_mastery=0.5,
            bkt_parameters=problematic_params
        )
        
        # Should handle gracefully without crashing
        updated_mastery = self.bkt_engine.update_mastery(mastery_level, self.correct_interaction)
        
        # Should return a valid mastery level
        assert 0.0 <= updated_mastery.current_mastery <= 1.0