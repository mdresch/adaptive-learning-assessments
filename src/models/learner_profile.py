"""
Learner Profile Data Models

This module defines the data models for learner profiles including demographics,
learning preferences, prior experience, and accessibility settings.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class EducationLevel(str, Enum):
    """Education level enumeration"""
    HIGH_SCHOOL = "high_school"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    DOCTORATE = "doctorate"
    BOOTCAMP = "bootcamp"
    SELF_TAUGHT = "self_taught"
    OTHER = "other"


class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class ProgrammingExperienceLevel(str, Enum):
    """Programming experience levels"""
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AccessibilityPreference(str, Enum):
    """Accessibility preference types"""
    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    REDUCED_MOTION = "reduced_motion"
    AUDIO_DESCRIPTIONS = "audio_descriptions"
    CAPTIONS = "captions"


class Demographics(BaseModel):
    """Demographic information for learner"""
    age: Optional[int] = Field(None, ge=13, le=120, description="Learner's age")
    education_level: Optional[EducationLevel] = Field(None, description="Highest education level")
    country: Optional[str] = Field(None, max_length=100, description="Country of residence")
    timezone: Optional[str] = Field(None, description="Learner's timezone")
    preferred_language: Optional[str] = Field("en", description="Preferred language code")


class LearningPreferences(BaseModel):
    """Learning style and preference settings"""
    learning_styles: List[LearningStyle] = Field(default_factory=list, description="Preferred learning styles")
    session_duration_preference: Optional[int] = Field(None, ge=5, le=180, description="Preferred session duration in minutes")
    difficulty_preference: Optional[str] = Field("adaptive", description="Difficulty preference: easy, medium, hard, adaptive")
    notification_preferences: Dict[str, bool] = Field(default_factory=dict, description="Notification settings")
    study_time_preferences: List[str] = Field(default_factory=list, description="Preferred study times")


class ProgrammingExperience(BaseModel):
    """Programming experience and background"""
    overall_experience: ProgrammingExperienceLevel = Field(ProgrammingExperienceLevel.NONE, description="Overall programming experience")
    languages_known: List[str] = Field(default_factory=list, description="Programming languages known")
    data_structures_familiarity: Dict[str, int] = Field(default_factory=dict, description="Familiarity with data structures (1-5 scale)")
    algorithms_familiarity: Dict[str, int] = Field(default_factory=dict, description="Familiarity with algorithms (1-5 scale)")
    years_of_experience: Optional[int] = Field(None, ge=0, le=50, description="Years of programming experience")
    professional_experience: bool = Field(False, description="Has professional programming experience")


class AccessibilitySettings(BaseModel):
    """Accessibility preferences and requirements"""
    enabled_features: List[AccessibilityPreference] = Field(default_factory=list, description="Enabled accessibility features")
    screen_reader_type: Optional[str] = Field(None, description="Type of screen reader used")
    font_size_multiplier: float = Field(1.0, ge=0.5, le=3.0, description="Font size multiplier")
    contrast_preference: Optional[str] = Field("normal", description="Contrast preference: normal, high, custom")
    motion_sensitivity: bool = Field(False, description="Sensitive to motion/animations")
    audio_enabled: bool = Field(True, description="Audio feedback enabled")


class LearnerProfileBase(BaseModel):
    """Base learner profile model"""
    email: EmailStr = Field(..., description="Learner's email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    demographics: Demographics = Field(default_factory=Demographics, description="Demographic information")
    learning_preferences: LearningPreferences = Field(default_factory=LearningPreferences, description="Learning preferences")
    programming_experience: ProgrammingExperience = Field(default_factory=ProgrammingExperience, description="Programming experience")
    accessibility_settings: AccessibilitySettings = Field(default_factory=AccessibilitySettings, description="Accessibility settings")
    goals: List[str] = Field(default_factory=list, description="Learning goals")
    interests: List[str] = Field(default_factory=list, description="Areas of interest")
    is_active: bool = Field(True, description="Profile is active")

    @validator('email')
    def validate_email(cls, v):
        """Validate email format"""
        return v.lower()

    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower() if v else v


class LearnerProfileCreate(LearnerProfileBase):
    """Model for creating a new learner profile"""
    password: str = Field(..., min_length=8, description="Password for the account")

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class LearnerProfileUpdate(BaseModel):
    """Model for updating learner profile"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    demographics: Optional[Demographics] = None
    learning_preferences: Optional[LearningPreferences] = None
    programming_experience: Optional[ProgrammingExperience] = None
    accessibility_settings: Optional[AccessibilitySettings] = None
    goals: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class LearnerProfile(LearnerProfileBase):
    """Complete learner profile model with database fields"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    profile_completion_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Profile completion percentage")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "email": "learner@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
                "demographics": {
                    "age": 25,
                    "education_level": "bachelor",
                    "country": "United States",
                    "timezone": "America/New_York",
                    "preferred_language": "en"
                },
                "learning_preferences": {
                    "learning_styles": ["visual", "kinesthetic"],
                    "session_duration_preference": 30,
                    "difficulty_preference": "adaptive"
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
                "goals": ["Learn data structures", "Prepare for interviews"],
                "interests": ["algorithms", "web development"]
            }
        }


class LearnerProfileResponse(BaseModel):
    """Response model for learner profile"""
    id: str
    email: str
    first_name: str
    last_name: str
    username: Optional[str]
    demographics: Demographics
    learning_preferences: LearningPreferences
    programming_experience: ProgrammingExperience
    accessibility_settings: AccessibilitySettings
    goals: List[str]
    interests: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    profile_completion_percentage: float

    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "email": "learner@example.com",
                "first_name": "John",
                "last_name": "Doe",
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
                    "languages_known": ["python"]
                },
                "accessibility_settings": {
                    "enabled_features": [],
                    "font_size_multiplier": 1.0
                },
                "goals": ["Learn data structures"],
                "interests": ["algorithms"],
                "is_active": True,
                "profile_completion_percentage": 75.0
            }
        }