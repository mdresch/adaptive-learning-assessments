"""
Learner Profile Models

This module defines the data models for learner profiles including demographics,
preferences, prior experience, and accessibility requirements.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from bson import ObjectId
from enum import Enum


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


class LearningStyle(str, Enum):
    """Enumeration of learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MULTIMODAL = "multimodal"


class EducationLevel(str, Enum):
    """Enumeration of education levels"""
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    PROFESSIONAL = "professional"
    OTHER = "other"


class ProgrammingExperienceLevel(str, Enum):
    """Enumeration of programming experience levels"""
    NONE = "none"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AccessibilityNeed(str, Enum):
    """Enumeration of accessibility needs"""
    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    CLOSED_CAPTIONS = "closed_captions"
    AUDIO_DESCRIPTIONS = "audio_descriptions"
    REDUCED_MOTION = "reduced_motion"
    COLOR_BLIND_SUPPORT = "color_blind_support"


class Demographics(BaseModel):
    """Demographics information for learner profile"""
    age: Optional[int] = Field(None, ge=13, le=120, description="Learner's age")
    location: Optional[str] = Field(None, max_length=100, description="Geographic location")
    language: Optional[str] = Field("en", max_length=10, description="Preferred language code")
    education_level: Optional[EducationLevel] = Field(None, description="Highest education level")
    occupation: Optional[str] = Field(None, max_length=100, description="Current occupation")
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 13 or v > 120):
            raise ValueError('Age must be between 13 and 120')
        return v


class LearningPreferences(BaseModel):
    """Learning preferences and style information"""
    learning_style: Optional[LearningStyle] = Field(None, description="Preferred learning style")
    accessibility_needs: List[AccessibilityNeed] = Field(default_factory=list, description="Accessibility requirements")
    preferred_session_duration: Optional[int] = Field(None, ge=5, le=180, description="Preferred session duration in minutes")
    difficulty_preference: Optional[str] = Field("adaptive", description="Difficulty preference: easy, medium, hard, adaptive")
    notification_preferences: Dict[str, bool] = Field(default_factory=dict, description="Notification settings")
    
    @validator('preferred_session_duration')
    def validate_session_duration(cls, v):
        if v is not None and (v < 5 or v > 180):
            raise ValueError('Session duration must be between 5 and 180 minutes')
        return v


class ProgrammingExperience(BaseModel):
    """Programming experience and background information"""
    overall_level: ProgrammingExperienceLevel = Field(ProgrammingExperienceLevel.NONE, description="Overall programming experience level")
    languages_known: List[str] = Field(default_factory=list, description="Programming languages known")
    years_experience: Optional[int] = Field(None, ge=0, le=50, description="Years of programming experience")
    data_structures_familiarity: Dict[str, str] = Field(default_factory=dict, description="Familiarity with specific data structures")
    algorithms_familiarity: Dict[str, str] = Field(default_factory=dict, description="Familiarity with specific algorithms")
    previous_courses: List[str] = Field(default_factory=list, description="Previous programming courses taken")
    
    @validator('years_experience')
    def validate_years_experience(cls, v):
        if v is not None and (v < 0 or v > 50):
            raise ValueError('Years of experience must be between 0 and 50')
        return v


class SelfReportedData(BaseModel):
    """Self-reported data from learner"""
    confidence_level: Optional[int] = Field(None, ge=1, le=10, description="Self-reported confidence level (1-10)")
    learning_goals: List[str] = Field(default_factory=list, description="Learner's stated learning goals")
    motivation_level: Optional[int] = Field(None, ge=1, le=10, description="Self-reported motivation level (1-10)")
    time_availability: Optional[int] = Field(None, ge=1, le=40, description="Hours per week available for learning")
    reported_date: datetime = Field(default_factory=datetime.utcnow, description="When this data was reported")


class LearnerProfile(BaseModel):
    """Complete learner profile model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Learner's email address")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    
    # Core profile components
    demographics: Demographics = Field(default_factory=Demographics, description="Demographic information")
    preferences: LearningPreferences = Field(default_factory=LearningPreferences, description="Learning preferences")
    programming_experience: ProgrammingExperience = Field(default_factory=ProgrammingExperience, description="Programming background")
    self_reported_data: List[SelfReportedData] = Field(default_factory=list, description="Self-reported learning data")
    
    # System fields
    is_active: bool = Field(True, description="Whether the profile is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Privacy and consent
    privacy_consent: bool = Field(False, description="Whether learner has given privacy consent")
    data_processing_consent: bool = Field(False, description="Whether learner consents to data processing")
    marketing_consent: bool = Field(False, description="Whether learner consents to marketing communications")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "demographics": {
                    "age": 25,
                    "location": "New York, NY",
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
                        "linked_lists": "intermediate",
                        "trees": "beginner"
                    }
                },
                "privacy_consent": True,
                "data_processing_consent": True
            }
        }


class LearnerProfileUpdate(BaseModel):
    """Model for updating learner profile (excludes system-generated fields)"""
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    demographics: Optional[Demographics] = None
    preferences: Optional[LearningPreferences] = None
    programming_experience: Optional[ProgrammingExperience] = None
    privacy_consent: Optional[bool] = None
    data_processing_consent: Optional[bool] = None
    marketing_consent: Optional[bool] = None


class LearnerProfileResponse(BaseModel):
    """Response model for learner profile (excludes sensitive data)"""
    id: str
    username: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    demographics: Demographics
    preferences: LearningPreferences
    programming_experience: ProgrammingExperience
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "demographics": {
                    "age": 25,
                    "location": "New York, NY",
                    "education_level": "bachelors"
                },
                "preferences": {
                    "learning_style": "visual",
                    "accessibility_needs": ["high_contrast"]
                },
                "programming_experience": {
                    "overall_level": "intermediate",
                    "languages_known": ["Python", "JavaScript"]
                },
                "is_active": True,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
        }