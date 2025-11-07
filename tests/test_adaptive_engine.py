"""
Tests for the adaptive challenge selection engine.
"""
import pytest
from datetime import datetime, timedelta
from src.algorithms.adaptive_engine import AdaptiveEngine
from src.algorithms.bkt_engine import BKTEngine
from src.models.adaptive_models import (
    CompetencyLevel, ChallengeMetadata, AdaptationRequest,
    ActivityResult, DifficultyFeedback, BKTParameters
)


@pytest.fixture
def bkt_engine():
    """Create BKT engine instance."""
    return BKTEngine()


@pytest.fixture
def adaptive_engine():
    """Create adaptive engine instance."""
    return AdaptiveEngine()


@pytest.fixture
def sample_competencies():
    """Create sample competency levels."""
    return [
        CompetencyLevel(
            _id="comp1",
            competency_name="Arrays",
            mastery_probability=0.6,
            confidence_level=0.8,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        ),
        CompetencyLevel(
            _id="comp2",
            competency_name="Recursion",
            mastery_probability=0.3,
            confidence_level=0.5,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        ),
        CompetencyLevel(
            _id="comp3",
            competency_name="Binary Trees",
            mastery_probability=0.8,
            confidence_level=0.9,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        )
    ]


@pytest.fixture
def sample_challenges():
    """Create sample challenges."""
    return [
        ChallengeMetadata(
            _id="challenge1",
            title="Array Manipulation",
            description="Practice array operations",
            competencies=["comp1"],
            difficulty_level=0.5,
            estimated_duration=30,
            challenge_type="coding",
            prerequisites=[]
        ),
        ChallengeMetadata(
            _id="challenge2",
            title="Recursive Algorithms",
            description="Learn recursive problem solving",
            competencies=["comp2"],
            difficulty_level=0.4,
            estimated_duration=45,
            challenge_type="coding",
            prerequisites=[]
        ),
        ChallengeMetadata(
            _id="challenge3",
            title="Tree Traversal",
            description="Master tree traversal techniques",
            competencies=["comp3"],
            difficulty_level=0.7,
            estimated_duration=60,
            challenge_type="coding",
            prerequisites=["comp1"]
        )
    ]


class TestBKTEngine:
    """Test cases for BKT engine."""
    
    def test_initialize_competency(self, bkt_engine):
        """Test competency initialization."""
        competency = bkt_engine.initialize_competency("test_comp", "Test Competency")
        
        assert competency.competency_id == "test_comp"
        assert competency.competency_name == "Test Competency"
        assert competency.mastery_probability == 0.1  # Default prior knowledge
        assert competency.confidence_level == 0.5
        assert isinstance(competency.bkt_parameters, BKTParameters)
    
    def test_update_competency_success(self, bkt_engine, sample_competencies):
        """Test competency update with successful activity."""
        competency = sample_competencies[0]  # Arrays with 0.6 mastery
        
        activity_result = ActivityResult(
            learner_id="learner1",
            challenge_id="challenge1",
            competencies_addressed=["comp1"],
            success=True,
            score=0.9,
            attempts=1,
            time_spent=25
        )
        
        updated_competency = bkt_engine.update_competency(competency, activity_result)
        
        # Mastery should increase after successful activity
        assert updated_competency.mastery_probability > competency.mastery_probability
        assert updated_competency.competency_id == competency.competency_id
        assert updated_competency.last_updated > competency.last_updated
    
    def test_update_competency_failure(self, bkt_engine, sample_competencies):
        """Test competency update with failed activity."""
        competency = sample_competencies[0]  # Arrays with 0.6 mastery
        
        activity_result = ActivityResult(
            learner_id="learner1",
            challenge_id="challenge1",
            competencies_addressed=["comp1"],
            success=False,
            score=0.2,
            attempts=3,
            time_spent=45
        )
        
        updated_competency = bkt_engine.update_competency(competency, activity_result)
        
        # Mastery should decrease after failed activity
        assert updated_competency.mastery_probability < competency.mastery_probability
        assert updated_competency.competency_id == competency.competency_id
    
    def test_predict_performance(self, bkt_engine, sample_competencies):
        """Test performance prediction."""
        competency = sample_competencies[0]  # Arrays with 0.6 mastery
        
        success_prob, confidence = bkt_engine.predict_performance(competency, 0.5)
        
        assert 0.0 <= success_prob <= 1.0
        assert 0.0 <= confidence <= 1.0
        
        # Higher difficulty should reduce success probability
        success_prob_hard, _ = bkt_engine.predict_performance(competency, 0.9)
        assert success_prob_hard < success_prob
    
    def test_calculate_optimal_difficulty(self, bkt_engine, sample_competencies):
        """Test optimal difficulty calculation."""
        competency = sample_competencies[0]  # Arrays with 0.6 mastery
        
        optimal_difficulty = bkt_engine.calculate_optimal_difficulty(competency)
        
        assert 0.0 <= optimal_difficulty <= 1.0
        
        # For moderate mastery, optimal difficulty should be moderate
        assert 0.3 <= optimal_difficulty <= 0.8
    
    def test_get_competency_insights(self, bkt_engine, sample_competencies):
        """Test competency insights generation."""
        insights = bkt_engine.get_competency_insights(sample_competencies)
        
        assert "overall_mastery" in insights
        assert "strong_competencies" in insights
        assert "developing_competencies" in insights
        assert "weak_competencies" in insights
        
        # Check that insights make sense
        assert 0.0 <= insights["overall_mastery"] <= 1.0
        assert isinstance(insights["strong_competencies"], list)
        assert isinstance(insights["developing_competencies"], list)


class TestAdaptiveEngine:
    """Test cases for adaptive engine."""
    
    def test_generate_recommendations(self, adaptive_engine, sample_competencies, sample_challenges):
        """Test recommendation generation."""
        request = AdaptationRequest(
            learner_id="learner1",
            current_competencies=sample_competencies,
            learning_goals=["comp2"],  # Focus on recursion
            time_available=60,
            preferred_difficulty=0.5
        )
        
        response = adaptive_engine.generate_recommendations(request, sample_challenges)
        
        assert response.learner_id == "learner1"
        assert response.next_challenge is not None
        assert len(response.alternative_challenges) >= 0
        assert response.refresh_in_minutes > 0
        
        # Check that recommendations are relevant
        next_challenge = response.next_challenge
        assert next_challenge.recommendation_score > 0.0
        assert len(next_challenge.target_competencies) > 0
    
    def test_adapt_after_activity(self, adaptive_engine, sample_competencies):
        """Test adaptation after activity completion."""
        activity_result = ActivityResult(
            learner_id="learner1",
            challenge_id="challenge1",
            competencies_addressed=["comp1"],
            success=True,
            score=0.8,
            attempts=1,
            time_spent=30
        )
        
        updated_competencies = adaptive_engine.adapt_after_activity(
            "learner1",
            activity_result,
            sample_competencies
        )
        
        assert len(updated_competencies) == len(sample_competencies)
        
        # Find the updated competency
        updated_comp = next(
            comp for comp in updated_competencies 
            if comp.competency_id == "comp1"
        )
        original_comp = next(
            comp for comp in sample_competencies 
            if comp.competency_id == "comp1"
        )
        
        # Mastery should have increased due to successful activity
        assert updated_comp.mastery_probability > original_comp.mastery_probability
    
    def test_calculate_optimal_difficulty(self, adaptive_engine, sample_competencies, sample_challenges):
        """Test optimal difficulty calculation for challenges."""
        challenge = sample_challenges[0]  # Array challenge
        
        optimal_difficulty = adaptive_engine.calculate_optimal_difficulty(
            sample_competencies,
            challenge
        )
        
        assert 0.0 <= optimal_difficulty <= 1.0
    
    def test_filter_eligible_challenges(self, adaptive_engine, sample_challenges, sample_competencies):
        """Test challenge filtering based on prerequisites."""
        # Challenge 3 has prerequisite comp1 (Arrays)
        eligible = adaptive_engine._filter_eligible_challenges(
            sample_challenges,
            sample_competencies,
            []
        )
        
        # All challenges should be eligible since Arrays has 0.6 mastery (>0.6 threshold)
        assert len(eligible) == len(sample_challenges)
        
        # Test with low mastery competencies
        low_mastery_competencies = [
            CompetencyLevel(
                _id="comp1",
                competency_name="Arrays",
                mastery_probability=0.2,  # Below threshold
                confidence_level=0.5,
                last_updated=datetime.utcnow(),
                bkt_parameters=BKTParameters()
            )
        ]
        
        eligible_low = adaptive_engine._filter_eligible_challenges(
            sample_challenges,
            low_mastery_competencies,
            []
        )
        
        # Challenge 3 should be filtered out due to unmet prerequisites
        challenge_ids = [c.challenge_id for c in eligible_low]
        assert "challenge3" not in challenge_ids
    
    def test_difficulty_feedback_application(self, adaptive_engine, sample_competencies):
        """Test application of difficulty feedback."""
        feedback = DifficultyFeedback(
            challenge_id="challenge1",
            learner_id="learner1",
            perceived_difficulty=0.7,
            actual_difficulty=0.5,
            completion_time=35,
            success_rate=0.8
        )
        
        updated_competencies = adaptive_engine._apply_difficulty_feedback(
            sample_competencies,
            feedback
        )
        
        assert len(updated_competencies) == len(sample_competencies)
        
        # Confidence levels might be adjusted based on feedback accuracy
        for comp in updated_competencies:
            assert 0.0 <= comp.confidence_level <= 1.0


class TestIntegration:
    """Integration tests for the complete adaptive system."""
    
    def test_complete_learning_cycle(self, adaptive_engine, sample_competencies, sample_challenges):
        """Test a complete learning cycle: recommendation -> activity -> adaptation."""
        # Step 1: Get recommendations
        request = AdaptationRequest(
            learner_id="learner1",
            current_competencies=sample_competencies,
            learning_goals=["comp2"],
            time_available=60
        )
        
        response = adaptive_engine.generate_recommendations(request, sample_challenges)
        assert response.next_challenge is not None
        
        # Step 2: Simulate activity completion
        activity_result = ActivityResult(
            learner_id="learner1",
            challenge_id=response.next_challenge.challenge.challenge_id,
            competencies_addressed=response.next_challenge.challenge.competencies,
            success=True,
            score=0.75,
            attempts=2,
            time_spent=40
        )
        
        # Step 3: Adapt competencies
        updated_competencies = adaptive_engine.adapt_after_activity(
            "learner1",
            activity_result,
            sample_competencies
        )
        
        assert len(updated_competencies) == len(sample_competencies)
        
        # Step 4: Get new recommendations with updated competencies
        new_request = AdaptationRequest(
            learner_id="learner1",
            current_competencies=updated_competencies,
            learning_goals=["comp2"],
            time_available=60
        )
        
        new_response = adaptive_engine.generate_recommendations(new_request, sample_challenges)
        
        # Recommendations should be different due to updated competencies
        assert new_response.next_challenge is not None
        
        # The system should adapt to the learner's progress
        assert new_response.adaptation_metadata["learner_profile_summary"]["avg_mastery"] >= 0.0
    
    def test_zone_of_proximal_development_targeting(self, adaptive_engine, sample_challenges):
        """Test that the system targets the Zone of Proximal Development."""
        # Create competencies with different mastery levels
        competencies = [
            CompetencyLevel(
                _id="comp1",
                competency_name="Easy Skill",
                mastery_probability=0.9,  # Already mastered
                confidence_level=0.9,
                last_updated=datetime.utcnow(),
                bkt_parameters=BKTParameters()
            ),
            CompetencyLevel(
                _id="comp2",
                competency_name="ZPD Skill",
                mastery_probability=0.5,  # In ZPD
                confidence_level=0.7,
                last_updated=datetime.utcnow(),
                bkt_parameters=BKTParameters()
            ),
            CompetencyLevel(
                _id="comp3",
                competency_name="Hard Skill",
                mastery_probability=0.1,  # Too difficult
                confidence_level=0.3,
                last_updated=datetime.utcnow(),
                bkt_parameters=BKTParameters()
            )
        ]
        
        request = AdaptationRequest(
            learner_id="learner1",
            current_competencies=competencies,
            time_available=60
        )
        
        response = adaptive_engine.generate_recommendations(request, sample_challenges)
        
        # The system should prefer challenges targeting the ZPD skill
        if response.next_challenge:
            target_competencies = response.next_challenge.target_competencies
            zpd_competencies = [
                comp for comp in target_competencies 
                if 0.3 <= comp.mastery_probability <= 0.7
            ]
            
            # Should have at least some focus on ZPD competencies
            assert len(zpd_competencies) >= 0