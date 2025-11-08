"""
Tests for learner profile API endpoints

This module tests the FastAPI endpoints for learner profile management
including registration, authentication, profile updates, and data retrieval.
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.main import app
from src.models.learner_profile import LearnerProfile, EducationLevel, LearningStyle


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_registration_data():
    """Sample registration data for testing"""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123",
        "username": "johndoe",
        "demographics": {
            "age": 25,
            "education_level": "bachelor",
            "country": "United States"
        },
        "learning_preferences": {
            "learning_styles": ["visual"],
            "session_duration_preference": 30
        },
        "programming_experience": {
            "overall_experience": "beginner",
            "languages_known": ["python"],
            "years_of_experience": 1
        },
        "goals": ["Learn data structures"],
        "interests": ["algorithms"]
    }


@pytest.fixture
def sample_learner_profile():
    """Sample learner profile for mocking"""
    from datetime import datetime
    from bson import ObjectId
    
    return LearnerProfile(
        id=ObjectId(),
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        username="johndoe",
        demographics={
            "age": 25,
            "education_level": EducationLevel.BACHELOR,
            "country": "United States"
        },
        learning_preferences={
            "learning_styles": [LearningStyle.VISUAL],
            "session_duration_preference": 30
        },
        programming_experience={
            "overall_experience": "beginner",
            "languages_known": ["python"],
            "years_of_experience": 1
        },
        goals=["Learn data structures"],
        interests=["algorithms"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        profile_completion_percentage=85.0
    )


class TestLearnerProfileAPI:
    """Test cases for learner profile API endpoints"""
    
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.create_learner_profile')
    def test_register_learner_success(self, mock_create, mock_collection, client, sample_registration_data, sample_learner_profile):
        """Test successful learner registration"""
        mock_collection.return_value = AsyncMock()
        mock_create.return_value = sample_learner_profile
        
        response = client.post("/api/v1/learners/register", json=sample_registration_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["username"] == "johndoe"
        assert "id" in data
        assert "profile_completion_percentage" in data
    
    def test_register_learner_invalid_email(self, client, sample_registration_data):
        """Test registration with invalid email"""
        sample_registration_data["email"] = "invalid-email"
        
        response = client.post("/api/v1/learners/register", json=sample_registration_data)
        
        assert response.status_code == 422  # Validation error
        assert "email" in response.json()["detail"][0]["loc"]
    
    def test_register_learner_weak_password(self, client, sample_registration_data):
        """Test registration with weak password"""
        sample_registration_data["password"] = "weak"
        
        response = client.post("/api/v1/learners/register", json=sample_registration_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.create_learner_profile')
    def test_register_learner_duplicate_email(self, mock_create, mock_collection, client, sample_registration_data):
        """Test registration with duplicate email"""
        mock_collection.return_value = AsyncMock()
        mock_create.side_effect = ValueError("Email address already exists")
        
        response = client.post("/api/v1/learners/register", json=sample_registration_data)
        
        assert response.status_code == 400
        assert "Email address already exists" in response.json()["detail"]
    
    @patch('src.api.auth.authenticate_user')
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.update_last_login')
    def test_login_success(self, mock_update_login, mock_collection, mock_auth, client, sample_learner_profile):
        """Test successful login"""
        mock_collection.return_value = AsyncMock()
        mock_auth.return_value = sample_learner_profile
        mock_update_login.return_value = True
        
        login_data = {
            "username": "test@example.com",
            "password": "SecurePass123"
        }
        
        response = client.post("/api/v1/learners/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    @patch('src.api.auth.authenticate_user')
    def test_login_invalid_credentials(self, mock_auth, client):
        """Test login with invalid credentials"""
        mock_auth.return_value = None
        
        login_data = {
            "username": "test@example.com",
            "password": "WrongPassword"
        }
        
        response = client.post("/api/v1/learners/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @patch('src.api.auth.get_current_active_user')
    def test_get_current_profile(self, mock_current_user, client, sample_learner_profile):
        """Test getting current user profile"""
        mock_current_user.return_value = sample_learner_profile
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/v1/learners/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["profile_completion_percentage"] == 85.0
    
    def test_get_current_profile_unauthorized(self, client):
        """Test getting current profile without authentication"""
        response = client.get("/api/v1/learners/me")
        
        assert response.status_code == 403  # No authorization header
    
    @patch('src.api.auth.get_current_active_user')
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.update_learner_profile')
    def test_update_profile_success(self, mock_update, mock_collection, mock_current_user, client, sample_learner_profile):
        """Test successful profile update"""
        mock_current_user.return_value = sample_learner_profile
        mock_collection.return_value = AsyncMock()
        
        # Create updated profile
        updated_profile = sample_learner_profile.copy()
        updated_profile.first_name = "Jane"
        updated_profile.demographics.age = 30
        mock_update.return_value = updated_profile
        
        update_data = {
            "first_name": "Jane",
            "demographics": {
                "age": 30
            }
        }
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.put("/api/v1/learners/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
    
    @patch('src.api.auth.get_current_active_user')
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.update_learner_profile')
    def test_update_profile_not_found(self, mock_update, mock_collection, mock_current_user, client, sample_learner_profile):
        """Test profile update when profile not found"""
        mock_current_user.return_value = sample_learner_profile
        mock_collection.return_value = AsyncMock()
        mock_update.return_value = None
        
        update_data = {"first_name": "Jane"}
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.put("/api/v1/learners/me", json=update_data, headers=headers)
        
        assert response.status_code == 404
    
    @patch('src.api.auth.get_current_active_user')
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.get_learner_by_id')
    def test_get_learner_by_id_own_profile(self, mock_get, mock_collection, mock_current_user, client, sample_learner_profile):
        """Test getting learner profile by ID (own profile)"""
        mock_current_user.return_value = sample_learner_profile
        mock_collection.return_value = AsyncMock()
        mock_get.return_value = sample_learner_profile
        
        learner_id = str(sample_learner_profile.id)
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get(f"/api/v1/learners/{learner_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    @patch('src.api.auth.get_current_active_user')
    def test_get_learner_by_id_other_profile(self, mock_current_user, client, sample_learner_profile):
        """Test getting another learner's profile (should be forbidden)"""
        mock_current_user.return_value = sample_learner_profile
        
        other_id = "507f1f77bcf86cd799439011"  # Different ID
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get(f"/api/v1/learners/{other_id}", headers=headers)
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    @patch('src.api.auth.get_current_active_user')
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.delete_learner_profile')
    def test_delete_profile_success(self, mock_delete, mock_collection, mock_current_user, client, sample_learner_profile):
        """Test successful profile deletion"""
        mock_current_user.return_value = sample_learner_profile
        mock_collection.return_value = AsyncMock()
        mock_delete.return_value = True
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.delete("/api/v1/learners/me", headers=headers)
        
        assert response.status_code == 204
    
    @patch('src.api.auth.get_current_active_user')
    @patch('src.db.database.get_learner_collection')
    @patch('src.db.learner_repository.LearnerRepository.delete_learner_profile')
    def test_delete_profile_not_found(self, mock_delete, mock_collection, mock_current_user, client, sample_learner_profile):
        """Test profile deletion when profile not found"""
        mock_current_user.return_value = sample_learner_profile
        mock_collection.return_value = AsyncMock()
        mock_delete.return_value = False
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.delete("/api/v1/learners/me", headers=headers)
        
        assert response.status_code == 404
    
    @patch('src.api.auth.get_current_active_user')
    def test_search_learners_forbidden(self, mock_current_user, client, sample_learner_profile):
        """Test searching learners (should be forbidden for regular users)"""
        mock_current_user.return_value = sample_learner_profile
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/v1/learners", headers=headers)
        
        assert response.status_code == 403
        assert "Insufficient privileges" in response.json()["detail"]
    
    @patch('src.api.auth.get_current_active_user')
    def test_get_profile_completion_stats(self, mock_current_user, client, sample_learner_profile):
        """Test getting profile completion statistics"""
        mock_current_user.return_value = sample_learner_profile
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/v1/learners/stats/completion", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "completion_percentage" in data
        assert "is_complete" in data
        assert "missing_fields" in data
        assert "suggestions" in data
        assert data["completion_percentage"] == 85.0
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        with patch('src.db.database.db.database.command') as mock_command:
            mock_command.return_value = {"ok": 1}
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Adaptive Learning System"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
