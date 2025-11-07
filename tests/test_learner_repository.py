"""
Tests for learner repository

This module tests the database operations for learner profiles including
CRUD operations, authentication, and data integrity.
"""

import pytest
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

from src.db.learner_repository import LearnerRepository
from src.models.learner_profile import (
    LearnerProfileCreate,
    LearnerProfileUpdate,
    EducationLevel,
    LearningStyle,
    ProgrammingExperienceLevel
)


@pytest.fixture
async def test_db():
    """Create test database connection"""
    # Use a test database
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.test_adaptive_learning
    collection = db.test_learner_profiles
    
    # Clean up before test
    await collection.drop()
    
    yield collection
    
    # Clean up after test
    await collection.drop()
    client.close()


@pytest.fixture
async def repository(test_db):
    """Create repository instance with test database"""
    repo = LearnerRepository(test_db)
    await repo.create_indexes()
    return repo


@pytest.fixture
def sample_learner_data():
    """Sample learner profile data for testing"""
    return LearnerProfileCreate(
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        password="SecurePass123",
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
            "overall_experience": ProgrammingExperienceLevel.BEGINNER,
            "languages_known": ["python"],
            "years_of_experience": 1
        },
        goals=["Learn data structures"],
        interests=["algorithms"]
    )


class TestLearnerRepository:
    """Test cases for learner repository"""
    
    @pytest.mark.asyncio
    async def test_create_learner_profile(self, repository, sample_learner_data):
        """Test creating a new learner profile"""
        profile = await repository.create_learner_profile(sample_learner_data)
        
        assert profile is not None
        assert profile.email == "test@example.com"
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.username == "johndoe"
        assert profile.is_active is True
        assert profile.created_at is not None
        assert profile.updated_at is not None
        assert profile.profile_completion_percentage > 0
    
    @pytest.mark.asyncio
    async def test_create_duplicate_email(self, repository, sample_learner_data):
        """Test creating learner with duplicate email"""
        # Create first profile
        await repository.create_learner_profile(sample_learner_data)
        
        # Try to create another with same email
        duplicate_data = sample_learner_data.copy()
        duplicate_data.username = "different_username"
        
        with pytest.raises(ValueError, match="Email address already exists"):
            await repository.create_learner_profile(duplicate_data)
    
    @pytest.mark.asyncio
    async def test_create_duplicate_username(self, repository, sample_learner_data):
        """Test creating learner with duplicate username"""
        # Create first profile
        await repository.create_learner_profile(sample_learner_data)
        
        # Try to create another with same username
        duplicate_data = sample_learner_data.copy()
        duplicate_data.email = "different@example.com"
        
        with pytest.raises(ValueError, match="Username already exists"):
            await repository.create_learner_profile(duplicate_data)
    
    @pytest.mark.asyncio
    async def test_get_learner_by_id(self, repository, sample_learner_data):
        """Test retrieving learner by ID"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        retrieved_profile = await repository.get_learner_by_id(str(created_profile.id))
        
        assert retrieved_profile is not None
        assert retrieved_profile.id == created_profile.id
        assert retrieved_profile.email == created_profile.email
    
    @pytest.mark.asyncio
    async def test_get_learner_by_email(self, repository, sample_learner_data):
        """Test retrieving learner by email"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        retrieved_profile = await repository.get_learner_by_email("test@example.com")
        
        assert retrieved_profile is not None
        assert retrieved_profile.email == "test@example.com"
        assert retrieved_profile.id == created_profile.id
    
    @pytest.mark.asyncio
    async def test_get_learner_by_username(self, repository, sample_learner_data):
        """Test retrieving learner by username"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        retrieved_profile = await repository.get_learner_by_username("johndoe")
        
        assert retrieved_profile is not None
        assert retrieved_profile.username == "johndoe"
        assert retrieved_profile.id == created_profile.id
    
    @pytest.mark.asyncio
    async def test_update_learner_profile(self, repository, sample_learner_data):
        """Test updating learner profile"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        update_data = LearnerProfileUpdate(
            first_name="Jane",
            demographics={
                "age": 30,
                "education_level": EducationLevel.MASTER
            },
            goals=["Master algorithms", "Get a job"]
        )
        
        updated_profile = await repository.update_learner_profile(
            str(created_profile.id), update_data
        )
        
        assert updated_profile is not None
        assert updated_profile.first_name == "Jane"
        assert updated_profile.demographics.age == 30
        assert updated_profile.demographics.education_level == EducationLevel.MASTER
        assert len(updated_profile.goals) == 2
        assert updated_profile.updated_at > created_profile.updated_at
    
    @pytest.mark.asyncio
    async def test_delete_learner_profile(self, repository, sample_learner_data):
        """Test soft deleting learner profile"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        # Delete the profile
        success = await repository.delete_learner_profile(str(created_profile.id))
        assert success is True
        
        # Try to retrieve deleted profile
        retrieved_profile = await repository.get_learner_by_id(str(created_profile.id))
        assert retrieved_profile is None  # Should not be found (soft deleted)
    
    @pytest.mark.asyncio
    async def test_authenticate_learner(self, repository, sample_learner_data):
        """Test learner authentication"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        # Correct credentials
        authenticated = await repository.authenticate_learner(
            "test@example.com", "SecurePass123"
        )
        assert authenticated is not None
        assert authenticated.email == "test@example.com"
        
        # Wrong password
        not_authenticated = await repository.authenticate_learner(
            "test@example.com", "WrongPassword"
        )
        assert not_authenticated is None
        
        # Wrong email
        not_authenticated = await repository.authenticate_learner(
            "wrong@example.com", "SecurePass123"
        )
        assert not_authenticated is None
    
    @pytest.mark.asyncio
    async def test_update_last_login(self, repository, sample_learner_data):
        """Test updating last login timestamp"""
        created_profile = await repository.create_learner_profile(sample_learner_data)
        
        # Update last login
        success = await repository.update_last_login(str(created_profile.id))
        assert success is True
        
        # Verify last login was updated
        updated_profile = await repository.get_learner_by_id(str(created_profile.id))
        assert updated_profile.last_login is not None
        assert updated_profile.last_login > created_profile.created_at
    
    @pytest.mark.asyncio
    async def test_search_learners(self, repository):
        """Test searching learners with filters"""
        # Create multiple test profiles
        profiles_data = [
            LearnerProfileCreate(
                email="user1@example.com",
                first_name="Alice",
                last_name="Smith",
                password="SecurePass123",
                demographics={"country": "United States", "education_level": EducationLevel.BACHELOR}
            ),
            LearnerProfileCreate(
                email="user2@example.com",
                first_name="Bob",
                last_name="Johnson",
                password="SecurePass123",
                demographics={"country": "Canada", "education_level": EducationLevel.MASTER}
            ),
            LearnerProfileCreate(
                email="user3@example.com",
                first_name="Charlie",
                last_name="Brown",
                password="SecurePass123",
                demographics={"country": "United States", "education_level": EducationLevel.BACHELOR}
            )
        ]
        
        for profile_data in profiles_data:
            await repository.create_learner_profile(profile_data)
        
        # Search by country
        us_learners = await repository.search_learners(filters={"country": "United States"})
        assert len(us_learners) == 2
        
        # Search by education level
        bachelor_learners = await repository.search_learners(filters={"education_level": "bachelor"})
        assert len(bachelor_learners) == 2
        
        # Search with text
        alice_learners = await repository.search_learners(filters={"search_text": "Alice"})
        assert len(alice_learners) == 1
        assert alice_learners[0].first_name == "Alice"
        
        # Test pagination
        first_page = await repository.search_learners(skip=0, limit=2)
        assert len(first_page) == 2
        
        second_page = await repository.search_learners(skip=2, limit=2)
        assert len(second_page) == 1
    
    @pytest.mark.asyncio
    async def test_get_learner_count(self, repository):
        """Test getting learner count with filters"""
        # Create test profiles
        profiles_data = [
            LearnerProfileCreate(
                email="user1@example.com",
                first_name="Alice",
                last_name="Smith",
                password="SecurePass123",
                demographics={"country": "United States"}
            ),
            LearnerProfileCreate(
                email="user2@example.com",
                first_name="Bob",
                last_name="Johnson",
                password="SecurePass123",
                demographics={"country": "Canada"}
            )
        ]
        
        for profile_data in profiles_data:
            await repository.create_learner_profile(profile_data)
        
        # Total count
        total_count = await repository.get_learner_count()
        assert total_count == 2
        
        # Count with filter
        us_count = await repository.get_learner_count(filters={"country": "United States"})
        assert us_count == 1
    
    @pytest.mark.asyncio
    async def test_profile_completion_calculation(self, repository):
        """Test profile completion percentage calculation"""
        # Minimal profile
        minimal_data = LearnerProfileCreate(
            email="minimal@example.com",
            first_name="Min",
            last_name="User",
            password="SecurePass123"
        )
        minimal_profile = await repository.create_learner_profile(minimal_data)
        assert minimal_profile.profile_completion_percentage < 50
        
        # Complete profile
        complete_data = LearnerProfileCreate(
            email="complete@example.com",
            first_name="Complete",
            last_name="User",
            password="SecurePass123",
            demographics={
                "age": 25,
                "education_level": EducationLevel.BACHELOR,
                "country": "United States",
                "timezone": "America/New_York"
            },
            learning_preferences={
                "learning_styles": [LearningStyle.VISUAL]
            },
            programming_experience={
                "overall_experience": ProgrammingExperienceLevel.BEGINNER
            },
            goals=["Learn programming"],
            interests=["algorithms"]
        )
        complete_profile = await repository.create_learner_profile(complete_data)
        assert complete_profile.profile_completion_percentage > 80