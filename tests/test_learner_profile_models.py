"""
Tests for learner profile models

This module tests the Pydantic models for learner profiles including
validation, serialization, and data integrity.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.learner_profile import (
    LearnerProfileCreate,
    LearnerProfileUpdate,
    LearnerProfile,
    Demographics,
    LearningPreferences,
    ProgrammingExperience,
    AccessibilitySettings,
    EducationLevel,
    LearningStyle,
    ProgrammingExperienceLevel,
    AccessibilityPreference
)


class TestLearnerProfileModels:
    """Test cases for learner profile models"""
    
    def test_valid_learner_profile_create(self):
        """Test creating a valid learner profile"""
        profile_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123",
            "username": "johndoe",
            "demographics": {
                "age": 25,
                "education_level": "bachelor",
                "country": "United States",
                "timezone": "America/New_York"
            },
            "learning_preferences": {
                "learning_styles": ["visual", "kinesthetic"],
                "session_duration_preference": 30
            },
            "programming_experience": {
                "overall_experience": "beginner",
                "languages_known": ["python", "javascript"],
                "years_of_experience": 1
            },
            "accessibility_settings": {
                "enabled_features": ["large_text"],
                "font_size_multiplier": 1.2
            },
            "goals": ["Learn data structures"],
            "interests": ["algorithms"]
        }
        
        profile = LearnerProfileCreate(**profile_data)
        
        assert profile.email == "test@example.com"
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"
        assert profile.username == "johndoe"
        assert profile.demographics.age == 25
        assert profile.demographics.education_level == EducationLevel.BACHELOR
        assert LearningStyle.VISUAL in profile.learning_preferences.learning_styles
        assert profile.programming_experience.overall_experience == ProgrammingExperienceLevel.BEGINNER
        assert AccessibilityPreference.LARGE_TEXT in profile.accessibility_settings.enabled_features
    
    def test_email_validation(self):
        """Test email validation"""
        # Valid email
        profile_data = {
            "email": "valid@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123"
        }
        profile = LearnerProfileCreate(**profile_data)
        assert profile.email == "valid@example.com"
        
        # Invalid email should raise validation error
        with pytest.raises(ValidationError):
            LearnerProfileCreate(
                email="invalid-email",
                first_name="John",
                last_name="Doe",
                password="SecurePass123"
            )
    
    def test_password_validation(self):
        """Test password validation requirements"""
        base_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        # Valid password
        profile = LearnerProfileCreate(**base_data, password="SecurePass123")
        assert profile.password == "SecurePass123"
        
        # Too short password
        with pytest.raises(ValidationError) as exc_info:
            LearnerProfileCreate(**base_data, password="short")
        assert "at least 8 characters" in str(exc_info.value)
        
        # No uppercase letter
        with pytest.raises(ValidationError) as exc_info:
            LearnerProfileCreate(**base_data, password="lowercase123")
        assert "uppercase letter" in str(exc_info.value)
        
        # No lowercase letter
        with pytest.raises(ValidationError) as exc_info:
            LearnerProfileCreate(**base_data, password="UPPERCASE123")
        assert "lowercase letter" in str(exc_info.value)
        
        # No digit
        with pytest.raises(ValidationError) as exc_info:
            LearnerProfileCreate(**base_data, password="NoDigitsHere")
        assert "digit" in str(exc_info.value)
    
    def test_username_validation(self):
        """Test username validation"""
        base_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123"
        }
        
        # Valid usernames
        valid_usernames = ["johndoe", "john_doe", "john-doe", "user123"]
        for username in valid_usernames:
            profile = LearnerProfileCreate(**base_data, username=username)
            assert profile.username == username.lower()
        
        # Invalid username with special characters
        with pytest.raises(ValidationError):
            LearnerProfileCreate(**base_data, username="john@doe")
    
    def test_demographics_validation(self):
        """Test demographics field validation"""
        # Valid age range
        demo = Demographics(age=25)
        assert demo.age == 25
        
        # Age too young
        with pytest.raises(ValidationError):
            Demographics(age=12)
        
        # Age too old
        with pytest.raises(ValidationError):
            Demographics(age=121)
        
        # Valid education level
        demo = Demographics(education_level=EducationLevel.BACHELOR)
        assert demo.education_level == EducationLevel.BACHELOR
    
    def test_learning_preferences_validation(self):
        """Test learning preferences validation"""
        # Valid session duration
        prefs = LearningPreferences(session_duration_preference=30)
        assert prefs.session_duration_preference == 30
        
        # Session duration too short
        with pytest.raises(ValidationError):
            LearningPreferences(session_duration_preference=4)
        
        # Session duration too long
        with pytest.raises(ValidationError):
            LearningPreferences(session_duration_preference=181)
        
        # Valid learning styles
        prefs = LearningPreferences(learning_styles=[LearningStyle.VISUAL, LearningStyle.AUDITORY])
        assert len(prefs.learning_styles) == 2
    
    def test_programming_experience_validation(self):
        """Test programming experience validation"""
        # Valid experience
        exp = ProgrammingExperience(
            overall_experience=ProgrammingExperienceLevel.INTERMEDIATE,
            languages_known=["python", "java"],
            years_of_experience=3
        )
        assert exp.overall_experience == ProgrammingExperienceLevel.INTERMEDIATE
        assert "python" in exp.languages_known
        
        # Years of experience too high
        with pytest.raises(ValidationError):
            ProgrammingExperience(years_of_experience=51)
    
    def test_accessibility_settings_validation(self):
        """Test accessibility settings validation"""
        # Valid font size multiplier
        settings = AccessibilitySettings(font_size_multiplier=1.5)
        assert settings.font_size_multiplier == 1.5
        
        # Font size too small
        with pytest.raises(ValidationError):
            AccessibilitySettings(font_size_multiplier=0.4)
        
        # Font size too large
        with pytest.raises(ValidationError):
            AccessibilitySettings(font_size_multiplier=3.1)
        
        # Valid accessibility features
        settings = AccessibilitySettings(
            enabled_features=[AccessibilityPreference.SCREEN_READER, AccessibilityPreference.HIGH_CONTRAST]
        )
        assert len(settings.enabled_features) == 2
    
    def test_learner_profile_update(self):
        """Test learner profile update model"""
        update_data = {
            "first_name": "Jane",
            "demographics": {
                "age": 30,
                "education_level": "master"
            },
            "goals": ["Master algorithms", "Get a job"]
        }
        
        update = LearnerProfileUpdate(**update_data)
        assert update.first_name == "Jane"
        assert update.demographics.age == 30
        assert len(update.goals) == 2
    
    def test_learner_profile_with_defaults(self):
        """Test learner profile with default values"""
        profile_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass123"
        }
        
        profile = LearnerProfileCreate(**profile_data)
        
        # Check default values
        assert profile.demographics.preferred_language == "en"
        assert profile.learning_preferences.difficulty_preference == "adaptive"
        assert profile.programming_experience.overall_experience == ProgrammingExperienceLevel.NONE
        assert profile.accessibility_settings.font_size_multiplier == 1.0
        assert profile.accessibility_settings.audio_enabled is True
        assert profile.is_active is True
        assert len(profile.goals) == 0
        assert len(profile.interests) == 0