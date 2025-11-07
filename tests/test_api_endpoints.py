"""
Tests for BKT API Endpoints

Tests for the FastAPI endpoints including authentication, validation,
and real-time update functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.bkt_endpoints import router
from src.core.bkt_engine import BKTEngine
from src.models.bkt_models import BKTUpdateResult, LearnerCompetency
from src.utils.dependencies import TestDependencies


@pytest.fixture
def mock_bkt_engine():
    """Create mock BKT engine for testing"""
    engine = AsyncMock(spec=BKTEngine)
    
    # Mock update_competency
    engine.update_competency.return_value = BKTUpdateResult(
        learner_id="test_learner",
        skill_id="test_skill",
        previous_p_known=0.5,
        new_p_known=0.6,
        is_mastered=False,
        mastery_gained=False
    )
    
    # Mock get_learner_competencies
    competency = LearnerCompetency(
        learner_id="test_learner",
        skill_id="test_skill",
        p_known=0.6,
        mastery_threshold=0.8,
        total_attempts=5,
        correct_attempts=3,
        last_updated=datetime.utcnow()
    )
    engine.get_learner_competencies.return_value = {"test_skill": competency}
    
    # Mock predict_performance
    engine.predict_performance.return_value = (0.65, 0.8)
    
    # Mock get_mastery_status
    engine.get_mastery_status.return_value = {"test_skill": False}
    
    return engine


@pytest.fixture
def test_app(mock_bkt_engine):
    """Create test FastAPI app with mocked dependencies"""
    app = FastAPI()
    app.include_router(router)
    
    # Override dependencies
    app.dependency_overrides[get_bkt_engine] = lambda: mock_bkt_engine
    app.dependency_overrides[get_current_user] = TestDependencies.get_test_user()
    
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


class TestBKTEndpoints:
    """Test suite for BKT API endpoints"""
    
    def test_submit_performance_event(self, client, mock_bkt_engine):
        """Test submitting a single performance event"""
        
        event_data = {
            "learner_id": "test_learner",
            "skill_id": "test_skill",
            "activity_id": "test_activity",
            "is_correct": True,
            "response_time": 5.2,
            "confidence_level": 0.8,
            "metadata": {"difficulty": "medium"}
        }
        
        response = client.post(
            "/api/v1/bkt/events",
            json=event_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learner_id"] == "test_learner"
        assert data["skill_id"] == "test_skill"
        assert data["new_p_known"] == 0.6
        assert data["is_mastered"] == False
        
        # Verify engine was called correctly
        mock_bkt_engine.update_competency.assert_called_once()
        call_args = mock_bkt_engine.update_competency.call_args
        assert call_args[1]["learner_id"] == "test_learner"
        assert call_args[1]["skill_id"] == "test_skill"
        assert call_args[1]["is_correct"] == True
    
    def test_submit_batch_performance_events(self, client, mock_bkt_engine):
        """Test submitting batch performance events"""
        
        # Mock batch update response
        mock_bkt_engine.batch_update_competencies.return_value = [
            BKTUpdateResult(
                learner_id="test_learner",
                skill_id="test_skill",
                previous_p_known=0.5,
                new_p_known=0.6,
                is_mastered=False,
                mastery_gained=False
            ),
            BKTUpdateResult(
                learner_id="test_learner",
                skill_id="test_skill2",
                previous_p_known=0.3,
                new_p_known=0.4,
                is_mastered=False,
                mastery_gained=False
            )
        ]
        
        batch_data = {
            "events": [
                {
                    "learner_id": "test_learner",
                    "skill_id": "test_skill",
                    "activity_id": "activity1",
                    "is_correct": True
                },
                {
                    "learner_id": "test_learner",
                    "skill_id": "test_skill2",
                    "activity_id": "activity2",
                    "is_correct": False
                }
            ]
        }
        
        response = client.post(
            "/api/v1/bkt/events/batch",
            json=batch_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["learner_id"] == "test_learner"
        assert data[1]["learner_id"] == "test_learner"
        
        # Verify engine was called
        mock_bkt_engine.batch_update_competencies.assert_called_once()
    
    def test_get_learner_competencies(self, client, mock_bkt_engine):
        """Test getting learner competencies"""
        
        response = client.get(
            "/api/v1/bkt/competencies/test_learner",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "test_skill" in data
        competency = data["test_skill"]
        assert competency["learner_id"] == "test_learner"
        assert competency["skill_id"] == "test_skill"
        assert competency["p_known"] == 0.6
        assert competency["total_attempts"] == 5
        assert competency["correct_attempts"] == 3
        
        # Verify engine was called
        mock_bkt_engine.get_learner_competencies.assert_called_once_with(
            "test_learner", None
        )
    
    def test_get_learner_competencies_with_skill_filter(self, client, mock_bkt_engine):
        """Test getting specific learner competencies"""
        
        response = client.get(
            "/api/v1/bkt/competencies/test_learner?skill_ids=test_skill&skill_ids=another_skill",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        
        # Verify engine was called with skill filter
        mock_bkt_engine.get_learner_competencies.assert_called_once_with(
            "test_learner", ["test_skill", "another_skill"]
        )
    
    def test_predict_performance(self, client, mock_bkt_engine):
        """Test performance prediction endpoint"""
        
        response = client.get(
            "/api/v1/bkt/prediction/test_learner/test_skill",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learner_id"] == "test_learner"
        assert data["skill_id"] == "test_skill"
        assert data["probability_correct"] == 0.65
        assert data["confidence_interval"] == 0.8
        assert "prediction_timestamp" in data
        
        # Verify engine was called
        mock_bkt_engine.predict_performance.assert_called_once_with(
            "test_learner", "test_skill"
        )
    
    def test_get_mastery_status(self, client, mock_bkt_engine):
        """Test mastery status endpoint"""
        
        response = client.get(
            "/api/v1/bkt/mastery/test_learner",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["learner_id"] == "test_learner"
        assert data["mastered_skills"] == []  # No mastered skills in mock
        assert data["total_skills"] == 1
        assert data["mastery_rate"] == 0.0
        
        # Verify engine was called
        mock_bkt_engine.get_mastery_status.assert_called_once_with(
            "test_learner", None
        )
    
    def test_health_check(self, client, mock_bkt_engine):
        """Test health check endpoint"""
        
        # Mock cache stats
        mock_bkt_engine.cache.get_stats.return_value = {
            "connected_clients": 1,
            "used_memory": 1024
        }
        mock_bkt_engine._skill_parameters = {"test_skill": MagicMock()}
        
        response = client.get("/api/v1/bkt/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "cache_stats" in data
        assert data["skills_loaded"] == 1
    
    def test_authentication_required(self, client):
        """Test that authentication is required for protected endpoints"""
        
        # Test without authorization header
        response = client.post(
            "/api/v1/bkt/events",
            json={
                "learner_id": "test_learner",
                "skill_id": "test_skill",
                "activity_id": "test_activity",
                "is_correct": True
            }
        )
        
        assert response.status_code == 403  # Forbidden without auth
    
    def test_learner_permission_restriction(self, test_app, mock_bkt_engine):
        """Test that learners can only access their own data"""
        
        # Override with learner user
        test_app.dependency_overrides[get_current_user] = TestDependencies.get_test_user(
            role="learner", user_id="learner1"
        )
        
        client = TestClient(test_app)
        
        # Try to access another learner's data
        response = client.get(
            "/api/v1/bkt/competencies/learner2",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 403
    
    def test_educator_permissions(self, test_app, mock_bkt_engine):
        """Test educator permissions for analytics endpoints"""
        
        # Override with educator user
        test_app.dependency_overrides[get_current_user] = TestDependencies.get_test_user(
            role="educator", user_id="educator1"
        )
        
        # Mock repository for analytics
        mock_bkt_engine.repository.get_competency_statistics.return_value = {
            "total_learners": 10,
            "mastery_rate": 0.6
        }
        
        client = TestClient(test_app)
        
        response = client.get(
            "/api/v1/bkt/analytics/skill/test_skill",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["skill_id"] == "test_skill"
        assert "statistics" in data
        assert data["statistics"]["total_learners"] == 10
    
    def test_admin_permissions(self, test_app, mock_bkt_engine):
        """Test admin permissions for parameter management"""
        
        # Override with admin user
        test_app.dependency_overrides[get_current_user] = TestDependencies.get_test_user(
            role="admin", user_id="admin1"
        )
        
        client = TestClient(test_app)
        
        # Test updating skill parameters
        parameter_data = {
            "skill_id": "test_skill",
            "p_l0": 0.15,
            "p_t": 0.12,
            "p_g": 0.25,
            "p_s": 0.08
        }
        
        response = client.put(
            "/api/v1/bkt/parameters/test_skill",
            json=parameter_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["skill_id"] == "test_skill"
        assert data["p_l0"] == 0.15
        
        # Verify repository was called
        mock_bkt_engine.repository.save_skill_parameters.assert_called_once()
    
    def test_validation_errors(self, client, mock_bkt_engine):
        """Test input validation errors"""
        
        # Test invalid probability values
        invalid_event = {
            "learner_id": "test_learner",
            "skill_id": "test_skill",
            "activity_id": "test_activity",
            "is_correct": True,
            "confidence_level": 1.5  # Invalid: > 1.0
        }
        
        response = client.post(
            "/api/v1/bkt/events",
            json=invalid_event,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_error_handling(self, client, mock_bkt_engine):
        """Test error handling in endpoints"""
        
        # Mock engine to raise exception
        mock_bkt_engine.update_competency.side_effect = Exception("Database error")
        
        event_data = {
            "learner_id": "test_learner",
            "skill_id": "test_skill",
            "activity_id": "test_activity",
            "is_correct": True
        }
        
        response = client.post(
            "/api/v1/bkt/events",
            json=event_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
    
    def test_concurrent_requests(self, client, mock_bkt_engine):
        """Test handling of concurrent API requests"""
        
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                event_data = {
                    "learner_id": "test_learner",
                    "skill_id": "test_skill",
                    "activity_id": "test_activity",
                    "is_correct": True
                }
                
                response = client.post(
                    "/api/v1/bkt/events",
                    json=event_data,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                results.append(response.status_code)
                
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(errors) == 0
        assert len(results) == 10
        assert all(status == 200 for status in results)


# Import required dependencies for testing
try:
    from src.utils.dependencies import get_bkt_engine, get_current_user
except ImportError:
    # Mock the dependencies if not available
    def get_bkt_engine():
        return AsyncMock()
    
    def get_current_user():
        return {"id": "test_user", "role": "learner"}