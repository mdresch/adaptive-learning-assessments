"""
Learner profile data models for the Adaptive Learning System.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class LearningStyle(str, Enum):
    """Learning style preferences."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class ExperienceLevel(str, Enum):
    """Programming experience levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AccessibilityNeed(str, Enum):
    """Accessibility requirements."""
    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    KEYBOARD_ONLY = "keyboard_only"
    REDUCED_MOTION = "reduced_motion"


class LearnerDemographics(BaseModel):
    """Learner demographic information."""
    age: Optional[int] = Field(None, ge=13, le=120, description="Learner age")
    gender: Optional[str] = Field(None, description="Gender identity")
    location: Optional[str] = Field(None, description="Geographic location")
    timezone: Optional[str] = Field(None, description="Timezone preference")
    language: str = Field("en", description="Primary language")
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 13 or v > 120):
            raise ValueError('Age must be between 13 and 120')
        return v


class LearnerPreferences(BaseModel):
    """Learner learning preferences and settings."""
    learning_styles: List[LearningStyle] = Field(
        default_factory=list,
        description="Preferred learning styles"
    )
    difficulty_preference: str = Field(
        "adaptive",
        description="Difficulty preference: easy, medium, hard, adaptive"
    )
    session_duration_minutes: int = Field(
        30,
        ge=5,
        le=180,
        description="Preferred session duration in minutes"
    )
    notifications_enabled: bool = Field(
        True,
        description="Whether to receive notifications"
    )
    gamification_enabled: bool = Field(
        True,
        description="Whether to enable gamification features"
    )
    accessibility_needs: List[AccessibilityNeed] = Field(
        default_factory=list,
        description="Accessibility requirements"
    )
    
    @validator('difficulty_preference')
    def validate_difficulty(cls, v):
        valid_options = ["easy", "medium", "hard", "adaptive"]
        if v not in valid_options:
            raise ValueError(f'Difficulty preference must be one of {valid_options}')
        return v


class LearnerProfile(BaseModel):
    """Complete learner profile model."""
    id: Optional[str] = Field(None, alias="_id")
    learner_id: str = Field(..., description="Unique learner identifier")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="Email address")
    
    # Profile information
    demographics: LearnerDemographics = Field(
        default_factory=LearnerDemographics,
        description="Demographic information"
    )
    preferences: LearnerPreferences = Field(
        default_factory=LearnerPreferences,
        description="Learning preferences"
    )
    
    # Experience and background
    programming_experience: ExperienceLevel = Field(
        ExperienceLevel.BEGINNER,
        description="Overall programming experience level"
    )
    prior_topics: List[str] = Field(
        default_factory=list,
        description="Previously studied topics"
    )
    learning_goals: List[str] = Field(
        default_factory=list,
        description="Current learning objectives"
    )
    
    # System metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    is_active: bool = Field(True, description="Whether the profile is active")
    
    # Privacy and consent
    data_consent: bool = Field(False, description="Data processing consent")
    analytics_consent: bool = Field(False, description="Analytics consent")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "learner_id": "learner_123",
                "username": "john_doe",
                "email": "john@example.com",
                "demographics": {
                    "age": 25,
                    "location": "New York, USA",
                    "language": "en"
                },
                "preferences": {
                    "learning_styles": ["visual", "kinesthetic"],
                    "difficulty_preference": "adaptive",
                    "session_duration_minutes": 45
                },
                "programming_experience": "intermediate",
                "learning_goals": ["master data structures", "improve algorithms"],
                "data_consent": True,
                "analytics_consent": True
            }
        }
    
    @validator('email')
    def validate_email(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()


class LearnerProfileUpdate(BaseModel):
    """Model for updating learner profiles."""
    demographics: Optional[LearnerDemographics] = None
    preferences: Optional[LearnerPreferences] = None
    programming_experience: Optional[ExperienceLevel] = None
    learning_goals: Optional[List[str]] = None
    data_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None