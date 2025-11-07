"""
Tests for learner profile models

This module contains unit tests for the learner profile data models,
validating data validation, serialization, and business logic.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.learner import (
    LearnerProfile,
    LearnerProfileUpdate,
    Demographics,
    LearningPreferences,
    ProgrammingExperience,
    SelfReportedData,
    LearningStyle,
    EducationLevel,
    ProgrammingExperienceLevel,
    AccessibilityNeed
)


class TestDemographics:
    """Test cases for Demographics model"""
    
    def test_valid_demographics(self):
        """Test creating valid demographics"""
        demographics = Demographics(
            age=25,
            location="New York, NY",
            language="en",
            education_level=EducationLevel.BACHELORS,
            occupation="Software Developer"
        )
        
        assert demographics.age == 25
        assert demographics.location == "New York, NY"
        assert demographics.education_level == EducationLevel.BACHELORS
    
    def test_age_validation(self):
        """Test age validation constraints"""
        # Valid age
        demographics = Demographics(age=25)
        assert demographics.age == 25
        
        # Invalid age - too young
        with pytest.raises(ValidationError):
            Demographics(age=10)
        
        # Invalid age - too old
        with pytest.raises(ValidationError):
            Demographics(age=150)
    
    def test_optional_fields(self):
        """Test that all demographics fields are optional"""
        demographics = Demographics()
        assert demographics.age is None
        assert demographics.location is None
        assert demographics.language == "en"  # Default value


class TestLearningPreferences:
    """Test cases for LearningPreferences model"""
    
    def test_valid_preferences(self):
        """Test creating valid learning preferences"""
        preferences = LearningPreferences(
            learning_style=LearningStyle.VISUAL,
            accessibility_needs=[AccessibilityNeed.HIGH_CONTRAST, AccessibilityNeed.LARGE_TEXT],
            preferred_session_duration=30,
            difficulty_preference="adaptive"
        )
        
        assert preferences.learning_style == LearningStyle.VISUAL
        assert len(preferences.accessibility_needs) == 2
        assert preferences.preferred_session_duration == 30
    
    def test_session_duration_validation(self):
        """Test session duration validation"""
        # Valid duration
        preferences = LearningPreferences(preferred_session_duration=30)
        assert preferences.preferred_session_duration == 30
        
        # Invalid duration - too short
        with pytest.raises(ValidationError):
            LearningPreferences(preferred_session_duration=2)
        
        # Invalid duration - too long
        with pytest.raises(ValidationError):
            LearningPreferences(preferred_session_duration=200)


class TestProgrammingExperience:
    """Test cases for ProgrammingExperience model"""
    
    def test_valid_experience(self):
        """Test creating valid programming experience"""
        experience = ProgrammingExperience(
            overall_level=ProgrammingExperienceLevel.INTERMEDIATE,
            languages_known=["Python", "JavaScript"],
            years_experience=3,
            data_structures_familiarity={
                "arrays": "advanced",
                "linked_lists": "intermediate"
            }
        )
        
        assert experience.overall_level == ProgrammingExperienceLevel.INTERMEDIATE
        assert "Python" in experience.languages_known
        assert experience.years_experience == 3
    
    def test_years_experience_validation(self):
        """Test years of experience validation"""
        # Valid years
        experience = ProgrammingExperience(years_experience=5)
        assert experience.years_experience == 5
        
        # Invalid years - negative
        with pytest.raises(ValidationError):
            ProgrammingExperience(years_experience=-1)
        
        # Invalid years - too many
        with pytest.raises(ValidationError):
            ProgrammingExperience(years_experience=60)


class TestSelfReportedData:
    """Test cases for SelfReportedData model"""
    
    def test_valid_self_reported_data(self):
        """Test creating valid self-reported data"""
        data = SelfReportedData(
            confidence_level=7,
            learning_goals=["Master data structures", "Improve algorithms"],
            motivation_level=8,
            time_availability=10
        )
        
        assert data.confidence_level == 7
        assert len(data.learning_goals) == 2
        assert data.motivation_level == 8
        assert isinstance(data.reported_date, datetime)
    
    def test_confidence_level_validation(self):
        """Test confidence level validation"""
        # Valid confidence level
        data = SelfReportedData(confidence_level=5)
        assert data.confidence_level == 5
        
        # Invalid confidence level - too low
        with pytest.raises(ValidationError):
            SelfReportedData(confidence_level=0)
        
        # Invalid confidence level - too high
        with pytest.raises(ValidationError):
            SelfReportedData(confidence_level=11)


class TestLearnerProfile:
    """Test cases for LearnerProfile model"""
    
    def test_valid_learner_profile(self):
        """Test creating a valid learner profile"""
        profile = LearnerProfile(
            username="john_doe",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            demographics=Demographics(age=25, education_level=EducationLevel.BACHELORS),
            preferences=LearningPreferences(learning_style=LearningStyle.VISUAL),
            programming_experience=ProgrammingExperience(
                overall_level=ProgrammingExperienceLevel.INTERMEDIATE
            ),
            privacy_consent=True,
            data_processing_consent=True
        )
        
        assert profile.username == "john_doe"
        assert profile.email == "john.doe@example.com"
        assert profile.demographics.age == 25
        assert profile.preferences.learning_style == LearningStyle.VISUAL
        assert profile.privacy_consent is True
    
    def test_username_validation(self):
        """Test username validation"""
        # Valid username
        profile = LearnerProfile(
            username="valid_user",
            email="test@example.com",
            privacy_consent=True,
            data_processing_consent=True
        )
        assert profile.username == "valid_user"
        
        # Invalid username - too short
        with pytest.raises(ValidationError):
            LearnerProfile(
                username="ab",
                email="test@example.com",
                privacy_consent=True,
                data_processing_consent=True
            )
        
        # Invalid username - too long
        with pytest.raises(ValidationError):
            LearnerProfile(
                username="a" * 60,
                email="test@example.com",
                privacy_consent=True,
                data_processing_consent=True
            )
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid email
        profile = LearnerProfile(
            username="test_user",
            email="valid@example.com",
            privacy_consent=True,
            data_processing_consent=True
        )
        assert profile.email == "valid@example.com"
        
        # Invalid email
        with pytest.raises(ValidationError):
            LearnerProfile(
                username="test_user",
                email="invalid-email",
                privacy_consent=True,
                data_processing_consent=True
            )
    
    def test_default_values(self):
        """Test default values for optional fields"""
        profile = LearnerProfile(
            username="test_user",
            email="test@example.com",
            privacy_consent=True,
            data_processing_consent=True
        )
        
        assert profile.is_active is True
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)
        assert profile.last_login is None
        assert isinstance(profile.demographics, Demographics)
        assert isinstance(profile.preferences, LearningPreferences)
        assert isinstance(profile.programming_experience, ProgrammingExperience)
        assert profile.self_reported_data == []


class TestLearnerProfileUpdate:
    """Test cases for LearnerProfileUpdate model"""
    
    def test_valid_update(self):
        """Test creating a valid profile update"""
        update = LearnerProfileUpdate(
            first_name="Jane",
            demographics=Demographics(age=30),
            preferences=LearningPreferences(learning_style=LearningStyle.AUDITORY)
        )
        
        assert update.first_name == "Jane"
        assert update.demographics.age == 30
        assert update.preferences.learning_style == LearningStyle.AUDITORY
    
    def test_partial_update(self):
        """Test partial updates with only some fields"""
        update = LearnerProfileUpdate(first_name="Jane")
        
        assert update.first_name == "Jane"
        assert update.demographics is None
        assert update.preferences is None
    
    def test_empty_update(self):
        """Test empty update object"""
        update = LearnerProfileUpdate()
        
        assert update.first_name is None
        assert update.demographics is None
        assert update.preferences is None