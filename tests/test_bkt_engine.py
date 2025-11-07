"""
Tests for the BKT Engine implementation.
"""

import pytest
import asyncio
from datetime import datetime
from src.core.bkt_engine import BKTEngine
from src.models.bkt_models import BKTParameters


class TestBKTEngine:
    """Test cases for BKT Engine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bkt_engine = BKTEngine()
        self.learner_id = "test_learner_123"
        self.competency_id = "arrays_basic"
    
    @pytest.mark.asyncio
    async def test_get_bkt_parameters(self):
        """Test getting BKT parameters for a competency."""
        parameters = await self.bkt_engine.get_bkt_parameters(self.competency_id)
        
        assert parameters.competency_id == self.competency_id
        assert 0.0 <= parameters.prior_knowledge <= 1.0
        assert 0.0 <= parameters.learning_rate <= 1.0
        assert 0.0 <= parameters.guess_probability <= 1.0
        assert 0.0 <= parameters.slip_probability <= 1.0
    
    @pytest.mark.asyncio
    async def test_get_bkt_state(self):
        """Test getting BKT state for a learner-competency pair."""
        state = await self.bkt_engine.get_bkt_state(self.learner_id, self.competency_id)
        
        assert state.learner_id == self.learner_id
        assert state.competency_id == self.competency_id
        assert 0.0 <= state.mastery_probability <= 1.0
        assert state.evidence_count >= 0
        assert state.total_attempts >= 0
        assert state.correct_attempts >= 0
    
    def test_calculate_mastery_update_correct(self):
        """Test BKT mastery update calculation for correct response."""
        parameters = BKTParameters(
            competency_id=self.competency_id,
            prior_knowledge=0.1,
            learning_rate=0.3,
            guess_probability=0.25,
            slip_probability=0.1
        )
        
        current_mastery = 0.4
        is_correct = True
        
        new_mastery, details = self.bkt_engine.calculate_mastery_update(
            current_mastery, is_correct, parameters
        )
        
        # Correct response should generally increase mastery
        assert new_mastery >= current_mastery
        assert 0.0 <= new_mastery <= 1.0
        assert details["prior_mastery"] == current_mastery
        assert details["is_correct"] == is_correct
        assert details["posterior_mastery"] == new_mastery
    
    def test_calculate_mastery_update_incorrect(self):
        """Test BKT mastery update calculation for incorrect response."""
        parameters = BKTParameters(
            competency_id=self.competency_id,
            prior_knowledge=0.1,
            learning_rate=0.3,
            guess_probability=0.25,
            slip_probability=0.1
        )
        
        current_mastery = 0.6
        is_correct = False
        
        new_mastery, details = self.bkt_engine.calculate_mastery_update(
            current_mastery, is_correct, parameters
        )
        
        # Incorrect response should generally decrease mastery
        assert new_mastery <= current_mastery
        assert 0.0 <= new_mastery <= 1.0
        assert details["prior_mastery"] == current_mastery
        assert details["is_correct"] == is_correct
        assert details["posterior_mastery"] == new_mastery
    
    @pytest.mark.asyncio
    async def test_update_mastery(self):
        """Test complete mastery update process."""
        update = await self.bkt_engine.update_mastery(
            learner_id=self.learner_id,
            competency_id=self.competency_id,
            is_correct=True,
            activity_id="test_activity",
            session_id="test_session"
        )
        
        assert update.learner_id == self.learner_id
        assert update.competency_id == self.competency_id
        assert update.is_correct == True
        assert update.activity_id == "test_activity"
        assert update.session_id == "test_session"
        assert 0.0 <= update.prior_mastery <= 1.0
        assert 0.0 <= update.posterior_mastery <= 1.0
        assert isinstance(update.timestamp, datetime)
    
    def test_predict_performance(self):
        """Test performance prediction."""
        parameters = BKTParameters(
            competency_id=self.competency_id,
            prior_knowledge=0.1,
            learning_rate=0.3,
            guess_probability=0.25,
            slip_probability=0.1
        )
        
        mastery_probability = 0.7
        prediction = self.bkt_engine.predict_performance(
            mastery_probability, parameters
        )
        
        assert 0.0 <= prediction["correct_probability"] <= 1.0
        assert 0.0 <= prediction["incorrect_probability"] <= 1.0
        assert abs(prediction["correct_probability"] + prediction["incorrect_probability"] - 1.0) < 0.001
        assert prediction["mastery_probability"] == mastery_probability
    
    def test_predict_performance_with_difficulty(self):
        """Test performance prediction with difficulty adjustment."""
        parameters = BKTParameters(
            competency_id=self.competency_id,
            prior_knowledge=0.1,
            learning_rate=0.3,
            guess_probability=0.25,
            slip_probability=0.1
        )
        
        mastery_probability = 0.7
        difficulty_adjustment = 1.5  # Harder question
        
        prediction = self.bkt_engine.predict_performance(
            mastery_probability, parameters, difficulty_adjustment
        )
        
        # Harder questions should have lower success probability
        normal_prediction = self.bkt_engine.predict_performance(
            mastery_probability, parameters, 1.0
        )
        
        assert prediction["correct_probability"] <= normal_prediction["correct_probability"]
        assert prediction["adjusted_slip"] >= parameters.slip_probability
        assert prediction["adjusted_guess"] <= parameters.guess_probability


if __name__ == "__main__":
    pytest.main([__file__])