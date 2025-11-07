"""
Tests for the mastery tracking API endpoints.

This module contains integration tests for the FastAPI endpoints
that handle learner interactions and mastery tracking.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from src.main import app
from src.models.mastery import (
    InteractionLogRequest,
    LearnerInteraction,
    MasteryLevel,
    ActivityType,
    InteractionType,
    DifficultyLevel,
    BKTParameters
)


class TestMasteryEndpoints:
    """Test cases for mastery tracking API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_bkt_engine(self):
        """Create mock BKT engine."""
        return MagicMock()
    
    @pytest.fixture
    def sample_interaction_request(self):
        """Create sample interaction request."""
        return {
            "learner_id": "test_learner_001",
            "activity_id": "quiz_arrays_001",
            "activity_type": "quiz",
            "interaction_type": "completion",
            "competency_ids": ["arrays_basic", "arrays_traversal"],
            "score": 0.85,
            "is_correct": True,
            "attempts": 1,
            "time_spent": 120.5,
            "hints_used": 0,
            "difficulty_level": "intermediate",
            "session_id": "session_123",
            "metadata": {
                "browser": "Chrome",
                "device": "desktop"
            }
        }
    
    @pytest.fixture
    def sample_mastery_level(self):
        """Create sample mastery level."""
        return MasteryLevel(
            learner_id="test_learner_001",
            competency_id="arrays_basic",
            current_mastery=0.65,
            bkt_parameters=BKTParameters(),
            total_interactions=5,
            correct_interactions=4,
            average_score=0.78,
            is_mastered=False
        )
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
    
    @pytest.mark.asyncio
    async def test_log_interaction_success(self, sample_interaction_request, mock_repository, mock_bkt_engine):
        """Test successful interaction logging."""
        # Mock repository responses
        mock_repository.save_interaction.return_value = "interaction_123"
        mock_repository.get_mastery_level.return_value = None
        mock_repository.create_initial_mastery_level.return_value = MasteryLevel(
            learner_id="test_learner_001",
            competency_id="arrays_basic",
            current_mastery=0.1
        )
        mock_repository.save_mastery_level.return_value = "mastery_123"
        
        # Mock BKT engine response
        updated_mastery = MasteryLevel(
            learner_id="test_learner_001",
            competency_id="arrays_basic",
            current_mastery=0.25,
            is_mastered=False
        )
        mock_bkt_engine.update_mastery.return_value = updated_mastery
        
        # Override dependencies
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository,
            "src.utils.dependencies.get_bkt_engine": lambda: mock_bkt_engine
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/mastery/interactions",
                    json=sample_interaction_request
                )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["learner_id"] == "test_learner_001"
            assert "arrays_basic" in data["updated_competencies"]
            assert "arrays_traversal" in data["updated_competencies"]
            assert "processing_time" in data
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_log_interaction_invalid_data(self):
        """Test interaction logging with invalid data."""
        invalid_request = {
            "learner_id": "",  # Invalid empty learner ID
            "activity_id": "quiz_001",
            "activity_type": "invalid_type",  # Invalid activity type
            "interaction_type": "completion",
            "competency_ids": [],  # Empty competency list
            "score": 1.5  # Invalid score > 1.0
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/mastery/interactions",
                json=invalid_request
            )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_learner_progress_success(self, sample_mastery_level, mock_repository):
        """Test successful progress report retrieval."""
        # Mock repository responses
        mock_repository.get_mastery_levels_by_learner.return_value = [sample_mastery_level]
        mock_repository.get_interactions_by_learner.return_value = []
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/mastery/progress/test_learner_001")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["learner_id"] == "test_learner_001"
            assert data["total_competencies"] == 1
            assert data["mastered_competencies"] == 0
            assert "competency_mastery" in data
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_get_learner_progress_not_found(self, mock_repository):
        """Test progress report for non-existent learner."""
        mock_repository.get_mastery_levels_by_learner.return_value = []
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/mastery/progress/nonexistent_learner")
            
            assert response.status_code == 404
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_get_mastery_level_success(self, sample_mastery_level, mock_repository):
        """Test successful mastery level retrieval."""
        mock_repository.get_mastery_level.return_value = sample_mastery_level
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/mastery/mastery/test_learner_001/arrays_basic"
                )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["learner_id"] == "test_learner_001"
            assert data["competency_id"] == "arrays_basic"
            assert data["current_mastery"] == 0.65
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_get_mastery_level_not_found(self, mock_repository):
        """Test mastery level retrieval for non-existent data."""
        mock_repository.get_mastery_level.return_value = None
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/mastery/mastery/nonexistent/nonexistent"
                )
            
            assert response.status_code == 404
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_get_learner_interactions(self, mock_repository):
        """Test learner interactions retrieval."""
        sample_interactions = [
            LearnerInteraction(
                learner_id="test_learner_001",
                activity_id="quiz_001",
                activity_type=ActivityType.QUIZ,
                interaction_type=InteractionType.COMPLETION,
                competency_ids=["arrays_basic"],
                score=0.8,
                is_correct=True
            )
        ]
        
        mock_repository.get_interactions_by_learner.return_value = sample_interactions
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/mastery/interactions/test_learner_001?limit=10"
                )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["learner_id"] == "test_learner_001"
            assert data["total_interactions"] == 1
            assert len(data["interactions"]) == 1
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_get_competency_stats(self, mock_repository):
        """Test competency statistics retrieval."""
        mock_stats = {
            "total_learners": 10,
            "mastered_learners": 6,
            "average_mastery": 0.72,
            "mastery_rate": 60.0
        }
        
        mock_repository.get_competency_performance_stats.return_value = mock_stats
        mock_repository.get_competency.return_value = None
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/mastery/competencies/arrays_basic/stats")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["competency_id"] == "arrays_basic"
            assert data["statistics"]["total_learners"] == 10
            assert data["statistics"]["mastery_rate"] == 60.0
            
        finally:
            app.dependency_overrides = {}
    
    @pytest.mark.asyncio
    async def test_get_learner_dashboard(self, mock_repository, mock_bkt_engine):
        """Test learner dashboard data retrieval."""
        mock_summary = {
            "total_competencies": 5,
            "mastered_competencies": 2,
            "average_mastery": 0.65,
            "mastery_percentage": 40.0
        }
        
        sample_mastery_levels = [
            MasteryLevel(
                learner_id="test_learner_001",
                competency_id="arrays_basic",
                current_mastery=0.75,
                is_mastered=False
            )
        ]
        
        mock_repository.get_learner_progress_summary.return_value = mock_summary
        mock_repository.get_mastery_levels_by_learner.return_value = sample_mastery_levels
        mock_repository.get_interactions_by_learner.return_value = []
        
        mock_bkt_engine.calculate_confidence_interval.return_value = (0.6, 0.9)
        mock_bkt_engine.get_learning_velocity.return_value = 0.05
        mock_bkt_engine.recommend_practice_intensity.return_value = "moderate"
        
        app.dependency_overrides = {
            "src.utils.dependencies.get_mastery_repository": lambda: mock_repository,
            "src.utils.dependencies.get_bkt_engine": lambda: mock_bkt_engine
        }
        
        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/mastery/analytics/dashboard/test_learner_001")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["learner_id"] == "test_learner_001"
            assert "summary" in data
            assert "insights" in data
            assert len(data["insights"]) == 1
            assert data["insights"][0]["practice_recommendation"] == "moderate"
            
        finally:
            app.dependency_overrides = {}
    
    def test_api_documentation_accessible(self, client):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Verify OpenAPI schema contains our endpoints
        openapi_data = response.json()
        assert "/api/v1/mastery/interactions" in openapi_data["paths"]
        assert "/api/v1/mastery/progress/{learner_id}" in openapi_data["paths"]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/mastery/interactions")
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_process_time_header(self, client):
        """Test that process time header is added."""
        response = client.get("/health")
        
        # Should have process time header
        assert "x-process-time" in response.headers
        assert float(response.headers["x-process-time"]) >= 0