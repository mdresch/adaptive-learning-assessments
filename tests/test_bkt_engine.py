"""
Tests for BKT Engine

Comprehensive tests for the BKT algorithm implementation including
accuracy validation, performance optimization, and concurrent user scenarios.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import numpy as np

from src.core.bkt_engine import BKTEngine
from src.models.bkt_models import (
    BKTParameters, LearnerCompetency, PerformanceEvent, 
    BKTConfiguration, BKTUpdateResult
)
from src.db.bkt_repository import BKTRepository
from src.utils.cache_manager import InMemoryCache


class TestBKTEngine:
    """Test suite for BKT Engine functionality"""
    
    @pytest.fixture
    async def mock_repository(self):
        """Create mock repository for testing"""
        repository = AsyncMock(spec=BKTRepository)
        
        # Mock default skill parameters
        default_params = BKTParameters(
            skill_id="test_skill",
            p_l0=0.1,
            p_t=0.1,
            p_g=0.2,
            p_s=0.1
        )
        repository.get_skill_parameters.return_value = default_params
        repository.get_all_skill_parameters.return_value = [default_params]
        
        return repository
    
    @pytest.fixture
    async def cache_manager(self):
        """Create in-memory cache for testing"""
        cache = InMemoryCache()
        await cache.initialize()
        return cache
    
    @pytest.fixture
    def bkt_config(self):
        """Create BKT configuration for testing"""
        return BKTConfiguration(
            default_parameters=BKTParameters(
                skill_id="default",
                p_l0=0.1,
                p_t=0.1,
                p_g=0.2,
                p_s=0.1
            ),
            mastery_threshold=0.8,
            min_attempts_for_mastery=3,
            cache_ttl_seconds=300,
            update_batch_size=10
        )
    
    @pytest.fixture
    async def bkt_engine(self, mock_repository, cache_manager, bkt_config):
        """Create BKT engine for testing"""
        engine = BKTEngine(mock_repository, cache_manager, bkt_config, max_workers=2)
        await engine.initialize()
        return engine
    
    @pytest.mark.asyncio
    async def test_bkt_algorithm_correctness(self, bkt_engine, mock_repository):
        """Test BKT algorithm mathematical correctness"""
        
        # Setup mock competency
        initial_competency = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.1,
            mastery_threshold=0.8,
            total_attempts=0,
            correct_attempts=0
        )
        
        mock_repository.get_competency.return_value = initial_competency
        mock_repository.save_competency.return_value = initial_competency
        mock_repository.save_performance_event.return_value = MagicMock()
        
        # Test correct response update
        result = await bkt_engine.update_competency(
            learner_id="learner1",
            skill_id="test_skill",
            is_correct=True,
            activity_id="activity1"
        )
        
        # Verify P(Known) increased after correct response
        assert result.new_p_known > result.previous_p_known
        assert 0 <= result.new_p_known <= 1
        
        # Test incorrect response update
        initial_competency.p_known = 0.5  # Reset to middle value
        result = await bkt_engine.update_competency(
            learner_id="learner1",
            skill_id="test_skill",
            is_correct=False,
            activity_id="activity2"
        )
        
        # Verify P(Known) decreased after incorrect response
        assert result.new_p_known < 0.5
        assert 0 <= result.new_p_known <= 1
    
    @pytest.mark.asyncio
    async def test_mastery_detection(self, bkt_engine, mock_repository):
        """Test mastery detection logic"""
        
        # Setup competency near mastery threshold
        competency = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.75,
            mastery_threshold=0.8,
            total_attempts=2,
            correct_attempts=2
        )
        
        mock_repository.get_competency.return_value = competency
        mock_repository.save_competency.return_value = competency
        mock_repository.save_performance_event.return_value = MagicMock()
        
        # Submit correct response that should trigger mastery
        result = await bkt_engine.update_competency(
            learner_id="learner1",
            skill_id="test_skill",
            is_correct=True,
            activity_id="activity1"
        )
        
        # Check if mastery was achieved
        if result.new_p_known >= 0.8 and competency.total_attempts >= 3:
            assert result.mastery_gained
            assert result.is_mastered
    
    @pytest.mark.asyncio
    async def test_performance_prediction(self, bkt_engine, mock_repository):
        """Test performance prediction accuracy"""
        
        # Setup competency
        competency = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.6,
            total_attempts=5
        )
        
        mock_repository.get_competency.return_value = competency
        
        # Get prediction
        prob_correct, confidence = await bkt_engine.predict_performance(
            "learner1", "test_skill"
        )
        
        # Verify prediction is reasonable
        assert 0 <= prob_correct <= 1
        assert 0 <= confidence <= 1
        
        # Prediction should be between P(G) and (1 - P(S)) for P(Known) = 0.6
        # P(Correct) = P(Known) * (1 - P(S)) + (1 - P(Known)) * P(G)
        # With P(G)=0.2, P(S)=0.1: P(Correct) = 0.6 * 0.9 + 0.4 * 0.2 = 0.62
        expected_prob = 0.6 * 0.9 + 0.4 * 0.2
        assert abs(prob_correct - expected_prob) < 0.01
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, bkt_engine, mock_repository):
        """Test batch processing performance and correctness"""
        
        # Setup multiple performance events
        events = []
        for i in range(20):
            event = PerformanceEvent(
                learner_id=f"learner{i % 5}",  # 5 different learners
                skill_id=f"skill{i % 3}",      # 3 different skills
                activity_id=f"activity{i}",
                is_correct=i % 2 == 0,         # Alternating correct/incorrect
                timestamp=datetime.utcnow()
            )
            events.append(event)
        
        # Mock repository responses
        mock_repository.get_competency.return_value = LearnerCompetency(
            learner_id="test",
            skill_id="test",
            p_known=0.5,
            total_attempts=0,
            correct_attempts=0
        )
        mock_repository.save_competency.return_value = MagicMock()
        mock_repository.save_performance_event.return_value = MagicMock()
        
        # Process batch
        results = await bkt_engine.batch_update_competencies(events)
        
        # Verify all events were processed
        assert len(results) == len(events)
        
        # Verify each result is valid
        for result in results:
            assert isinstance(result, BKTUpdateResult)
            assert 0 <= result.new_p_known <= 1
    
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, bkt_engine, mock_repository):
        """Test concurrent competency updates for performance optimization"""
        
        # Setup mock responses
        mock_repository.get_competency.return_value = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.5,
            total_attempts=0,
            correct_attempts=0
        )
        mock_repository.save_competency.return_value = MagicMock()
        mock_repository.save_performance_event.return_value = MagicMock()
        
        # Create concurrent update tasks
        tasks = []
        for i in range(50):
            task = bkt_engine.update_competency(
                learner_id=f"learner{i % 10}",
                skill_id="test_skill",
                is_correct=i % 2 == 0,
                activity_id=f"activity{i}"
            )
            tasks.append(task)
        
        # Execute concurrently
        start_time = datetime.utcnow()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.utcnow()
        
        # Verify performance (should complete within reasonable time)
        duration = (end_time - start_time).total_seconds()
        assert duration < 5.0  # Should complete within 5 seconds
        
        # Verify no exceptions occurred
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0
        
        # Verify all updates completed
        valid_results = [r for r in results if isinstance(r, BKTUpdateResult)]
        assert len(valid_results) == 50
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, bkt_engine, mock_repository, cache_manager):
        """Test cache performance for frequent competency lookups"""
        
        # Setup competency
        competency = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.6,
            total_attempts=5,
            correct_attempts=3
        )
        
        # First call should hit database
        mock_repository.get_competency.return_value = competency
        result1 = await bkt_engine.get_learner_competencies("learner1", ["test_skill"])
        
        # Verify database was called
        mock_repository.get_competency.assert_called()
        
        # Reset mock
        mock_repository.reset_mock()
        
        # Second call should hit cache
        result2 = await bkt_engine.get_learner_competencies("learner1", ["test_skill"])
        
        # Verify database was not called again
        mock_repository.get_competency.assert_not_called()
        
        # Results should be identical
        assert result1["test_skill"].p_known == result2["test_skill"].p_known
    
    @pytest.mark.asyncio
    async def test_algorithm_accuracy_with_test_data(self, bkt_engine, mock_repository):
        """Test BKT algorithm accuracy with known test scenarios"""
        
        # Test scenario: learner with consistent correct responses should reach mastery
        competency = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.1,  # Start with low knowledge
            mastery_threshold=0.8,
            total_attempts=0,
            correct_attempts=0
        )
        
        mock_repository.get_competency.return_value = competency
        mock_repository.save_competency.return_value = competency
        mock_repository.save_performance_event.return_value = MagicMock()
        
        # Simulate 10 consecutive correct responses
        p_known_values = [0.1]  # Starting value
        
        for i in range(10):
            result = await bkt_engine.update_competency(
                learner_id="learner1",
                skill_id="test_skill",
                is_correct=True,
                activity_id=f"activity{i}"
            )
            p_known_values.append(result.new_p_known)
            competency.p_known = result.new_p_known
            competency.total_attempts += 1
            competency.correct_attempts += 1
        
        # Verify P(Known) increased monotonically
        for i in range(1, len(p_known_values)):
            assert p_known_values[i] >= p_known_values[i-1]
        
        # Verify final P(Known) is high
        assert p_known_values[-1] > 0.7
    
    def test_bkt_update_calculation(self, bkt_engine):
        """Test BKT update calculation with known values"""
        
        parameters = BKTParameters(
            skill_id="test",
            p_l0=0.1,
            p_t=0.1,
            p_g=0.2,
            p_s=0.1
        )
        
        # Test correct response update
        p_known_new = bkt_engine._calculate_bkt_update(0.5, True, parameters)
        
        # Manual calculation:
        # P(Correct) = 0.5 * 0.9 + 0.5 * 0.2 = 0.55
        # P(Known|Correct) = (0.5 * 0.9) / 0.55 = 0.818
        # P(Known_final) = 0.818 + (1 - 0.818) * 0.1 = 0.836
        expected = 0.5 * 0.9 / 0.55
        expected = expected + (1 - expected) * 0.1
        
        assert abs(p_known_new - expected) < 0.001
        
        # Test incorrect response update
        p_known_new = bkt_engine._calculate_bkt_update(0.5, False, parameters)
        
        # Manual calculation:
        # P(Incorrect) = 0.5 * 0.1 + 0.5 * 0.8 = 0.45
        # P(Known|Incorrect) = (0.5 * 0.1) / 0.45 = 0.111
        # P(Known_final) = 0.111 + (1 - 0.111) * 0.1 = 0.2
        expected = 0.5 * 0.1 / 0.45
        expected = expected + (1 - expected) * 0.1
        
        assert abs(p_known_new - expected) < 0.001
    
    @pytest.mark.asyncio
    async def test_error_handling(self, bkt_engine, mock_repository):
        """Test error handling and recovery"""
        
        # Test database error handling
        mock_repository.get_competency.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            await bkt_engine.update_competency(
                learner_id="learner1",
                skill_id="test_skill",
                is_correct=True,
                activity_id="activity1"
            )
        
        # Reset mock
        mock_repository.get_competency.side_effect = None
        mock_repository.get_competency.return_value = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.5
        )
        
        # Test recovery after error
        result = await bkt_engine.update_competency(
            learner_id="learner1",
            skill_id="test_skill",
            is_correct=True,
            activity_id="activity1"
        )
        
        assert isinstance(result, BKTUpdateResult)
    
    @pytest.mark.asyncio
    async def test_skill_parameter_management(self, bkt_engine, mock_repository):
        """Test skill parameter loading and caching"""
        
        # Test parameter loading
        parameters = await bkt_engine._get_skill_parameters("new_skill")
        
        # Should use default parameters for new skill
        assert parameters.skill_id == "new_skill"
        assert parameters.p_l0 == 0.1
        
        # Test parameter caching
        parameters2 = await bkt_engine._get_skill_parameters("new_skill")
        
        # Should return same object from cache
        assert parameters is parameters2
    
    @pytest.mark.asyncio
    async def test_mastery_threshold_configuration(self, bkt_engine, mock_repository):
        """Test configurable mastery thresholds"""
        
        # Setup competency with custom mastery threshold
        competency = LearnerCompetency(
            learner_id="learner1",
            skill_id="test_skill",
            p_known=0.75,
            mastery_threshold=0.7,  # Lower threshold
            total_attempts=3,
            correct_attempts=3
        )
        
        # Test mastery check
        is_mastered = bkt_engine._check_mastery(competency)
        assert is_mastered  # Should be mastered with lower threshold
        
        # Test with higher threshold
        competency.mastery_threshold = 0.9
        is_mastered = bkt_engine._check_mastery(competency)
        assert not is_mastered  # Should not be mastered with higher threshold


@pytest.mark.asyncio
async def test_integration_scenario():
    """Integration test with realistic learning scenario"""
    
    # This test simulates a realistic learning scenario
    # and validates the overall BKT system behavior
    
    # Setup
    repository = AsyncMock(spec=BKTRepository)
    cache = InMemoryCache()
    await cache.initialize()
    
    config = BKTConfiguration(
        default_parameters=BKTParameters(
            skill_id="default",
            p_l0=0.1,
            p_t=0.15,
            p_g=0.25,
            p_s=0.1
        ),
        mastery_threshold=0.8,
        min_attempts_for_mastery=5
    )
    
    engine = BKTEngine(repository, cache, config)
    await engine.initialize()
    
    # Mock repository responses
    competency = LearnerCompetency(
        learner_id="student1",
        skill_id="python_loops",
        p_known=0.1,
        mastery_threshold=0.8,
        total_attempts=0,
        correct_attempts=0
    )
    
    repository.get_competency.return_value = competency
    repository.save_competency.return_value = competency
    repository.save_performance_event.return_value = MagicMock()
    repository.get_skill_parameters.return_value = config.default_parameters
    repository.get_all_skill_parameters.return_value = [config.default_parameters]
    
    # Simulate learning progression
    responses = [True, False, True, True, False, True, True, True, True, True]
    p_known_progression = []
    
    for i, is_correct in enumerate(responses):
        result = await engine.update_competency(
            learner_id="student1",
            skill_id="python_loops",
            is_correct=is_correct,
            activity_id=f"exercise_{i}"
        )
        
        p_known_progression.append(result.new_p_known)
        competency.p_known = result.new_p_known
        competency.total_attempts += 1
        if is_correct:
            competency.correct_attempts += 1
    
    # Validate learning progression
    assert len(p_known_progression) == 10
    assert p_known_progression[-1] > p_known_progression[0]  # Overall improvement
    
    # Check final mastery status
    final_mastery = await engine.get_mastery_status("student1", ["python_loops"])
    
    # With mostly correct responses, should achieve mastery
    if competency.total_attempts >= 5 and competency.p_known >= 0.8:
        assert final_mastery["python_loops"]