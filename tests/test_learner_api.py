"""
Tests for learner profile API endpoints

This module contains integration tests for the learner profile API endpoints,
testing the complete request/response cycle.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app
from src.models.learner import (
    LearningStyle,
    EducationLevel,
    ProgrammingExperienceLevel,
    AccessibilityNeed
)


# Test data
VALID_LEARNER_DATA = {
    "username": "test_user",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "demographics": {
        "age": 25,
        "location": "Test City",
        "language": "en",
        "education_level": "bachelors",
        "occupation": "Software Developer"
    },
    "preferences": {
        "learning_style": "visual",
        "accessibility_needs": ["high_contrast"],
        "preferred_session_duration": 30,
        "difficulty_preference": "adaptive"
    },
    "programming_experience": {
        "overall_level": "intermediate",
        "languages_known": ["Python", "JavaScript"],
        "years_experience": 3,
        "data_structures_familiarity": {
            "arrays": "advanced",
            "linked_lists": "intermediate"
        }
    },
    "privacy_consent": True,
    "data_processing_consent": True
}

UPDATE_DATA = {
    "first_name": "Updated",
    "demographics": {
        "age": 26,
        "location": "Updated City"
    },
    "preferences": {
        "learning_style": "auditory",
        "preferred_session_duration": 45
    }
}

SELF_REPORTED_DATA = {
    "confidence_level": 7,
    "learning_goals": ["Master algorithms", "Improve problem solving"],
    "motivation_level": 8,
    "time_availability": 15
}


class TestLearnerProfileAPI:
    """Test cases for learner profile API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_create_learner_profile_success(self, client):
        """Test successful learner profile creation"""
        response = client.post("/api/v1/learners/", json=VALID_LEARNER_DATA)
        
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "learner_id" in data
        assert data["username"] == "test_user"
    
    def test_create_learner_profile_missing_consent(self, client):
        """Test learner profile creation without required consent"""
        invalid_data = VALID_LEARNER_DATA.copy()
        invalid_data["privacy_consent"] = False
        
        response = client.post("/api/v1/learners/", json=invalid_data)
        
        assert response.status_code == 400
        assert "Privacy consent is required" in response.json()["detail"]
    
    def test_create_learner_profile_invalid_email(self, client):
        """Test learner profile creation with invalid email"""
        invalid_data = VALID_LEARNER_DATA.copy()
        invalid_data["email"] = "invalid-email"
        
        response = client.post("/api/v1/learners/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_learner_profile_invalid_age(self, client):
        """Test learner profile creation with invalid age"""
        invalid_data = VALID_LEARNER_DATA.copy()
        invalid_data["demographics"]["age"] = 10  # Too young
        
        response = client.post("/api/v1/learners/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_learner_profile_not_found(self, client):
        """Test getting non-existent learner profile"""
        fake_id = "507f1f77bcf86cd799439011"
        response = client.get(f"/api/v1/learners/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_learner_profile_invalid_id(self, client):
        """Test getting learner profile with invalid ID format"""
        invalid_id = "invalid-id"
        response = client.get(f"/api/v1/learners/{invalid_id}")
        
        assert response.status_code == 404
    
    def test_update_learner_profile_not_found(self, client):
        """Test updating non-existent learner profile"""
        fake_id = "507f1f77bcf86cd799439011"
        response = client.put(f"/api/v1/learners/{fake_id}", json=UPDATE_DATA)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_add_self_reported_data_not_found(self, client):
        """Test adding self-reported data to non-existent learner"""
        fake_id = "507f1f77bcf86cd799439011"
        response = client.post(
            f"/api/v1/learners/{fake_id}/self-reported-data",
            json=SELF_REPORTED_DATA
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_add_self_reported_data_invalid_confidence(self, client):
        """Test adding self-reported data with invalid confidence level"""
        fake_id = "507f1f77bcf86cd799439011"
        invalid_data = SELF_REPORTED_DATA.copy()
        invalid_data["confidence_level"] = 15  # Too high
        
        response = client.post(
            f"/api/v1/learners/{fake_id}/self-reported-data",
            json=invalid_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_last_login_not_found(self, client):
        """Test updating last login for non-existent learner"""
        fake_id = "507f1f77bcf86cd799439011"
        response = client.patch(f"/api/v1/learners/{fake_id}/last-login")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_deactivate_learner_profile_not_found(self, client):
        """Test deactivating non-existent learner profile"""
        fake_id = "507f1f77bcf86cd799439011"
        response = client.delete(f"/api/v1/learners/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_learners_with_pagination(self, client):
        """Test getting learners with pagination parameters"""
        response = client.get("/api/v1/learners/?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert "learners" in data
        assert "total_count" in data
        assert "skip" in data
        assert "limit" in data
        assert "has_more" in data
    
    def test_get_learners_with_filters(self, client):
        """Test getting learners with filter parameters"""
        response = client.get(
            "/api/v1/learners/?is_active=true&education_level=bachelors&programming_experience=intermediate"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "learners" in data
        assert "total_count" in data
    
    def test_get_learners_invalid_pagination(self, client):
        """Test getting learners with invalid pagination parameters"""
        response = client.get("/api/v1/learners/?skip=-1&limit=0")
        
        assert response.status_code == 422  # Validation error


class TestHealthAndRoot:
    """Test cases for health check and root endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "documentation" in data


class TestAPIDocumentation:
    """Test cases for API documentation endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_docs_endpoint(self, client):
        """Test Swagger UI documentation endpoint"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_endpoint(self, client):
        """Test ReDoc documentation endpoint"""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]