#!/bin/bash

# Phase 1.1: Create the first Pydantic model - Learner Profile
echo "Creating learner model for Phase 1..."

# Ensure we're in the virtual environment
source venv/bin/activate

# Create the learner model file
cat > src/models/learner.py << 'EOF'
"""
Learner Profile Models for Adaptive Learning System

This module contains Pydantic models for learner profiles, demographics,
preferences, and related data structures.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator
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


class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class ExperienceLevel(str, Enum):
    """Experience level options"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Demographics(BaseModel):
    """Learner demographic information"""
    age: Optional[int] = Field(None, ge=13, le=120, description="Learner age")
    location: Optional[str] = Field(None, max_length=100, description="Geographic location")
    education_level: Optional[str] = Field(None, max_length=50, description="Highest education level")
    language: Optional[str] = Field("en", max_length=10, description="Preferred language")
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 13 or v > 120):
            raise ValueError('Age must be between 13 and 120')
        return v


class LearningPreferences(BaseModel):
    """Learner preferences for personalization"""
    learning_style: Optional[LearningStyle] = Field(None, description="Preferred learning style")
    accessibility_needs: List[str] = Field(default_factory=list, description="Accessibility requirements")
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email_notifications": True,
            "progress_updates": True,
            "challenge_reminders": False
        },
        description="Notification preferences"
    )
    study_time_preference: Optional[str] = Field(None, description="Preferred study time")


class PriorExperience(BaseModel):
    """Learner's prior experience in programming and data structures"""
    programming_languages: List[str] = Field(default_factory=list, description="Known programming languages")
    data_structures_familiarity: Optional[ExperienceLevel] = Field(
        None, 
        description="Familiarity with data structures"
    )
    algorithms_familiarity: Optional[ExperienceLevel] = Field(
        None,
        description="Familiarity with algorithms"
    )
    years_of_experience: Optional[int] = Field(None, ge=0, le=50, description="Years of programming experience")
    previous_courses: List[str] = Field(default_factory=list, description="Previous relevant courses")


class SelfReportedData(BaseModel):
    """Self-reported data from learners"""
    date: datetime = Field(default_factory=datetime.utcnow, description="Date of self-report")
    confidence_level: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Self-reported confidence level (0-1)"
    )
    learning_goals: List[str] = Field(default_factory=list, description="Current learning goals")
    motivation_level: Optional[int] = Field(None, ge=1, le=10, description="Motivation level (1-10)")
    study_hours_per_week: Optional[int] = Field(None, ge=0, le=168, description="Planned study hours per week")


class LearnerProfile(BaseModel):
    """Complete learner profile model"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Learner email address")
    hashed_password: str = Field(..., description="Hashed password")
    
    # Profile sections
    demographics: Optional[Demographics] = Field(None, description="Demographic information")
    preferences: Optional[LearningPreferences] = Field(None, description="Learning preferences")
    prior_experience: Optional[PriorExperience] = Field(None, description="Prior experience")
    self_reported: List[SelfReportedData] = Field(default_factory=list, description="Self-reported data history")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_active: bool = Field(True, description="Whether the profile is active")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "demographics": {
                    "age": 25,
                    "location": "San Francisco, CA",
                    "education_level": "Bachelor's Degree",
                    "language": "en"
                },
                "preferences": {
                    "learning_style": "visual",
                    "accessibility_needs": [],
                    "notification_preferences": {
                        "email_notifications": True,
                        "progress_updates": True
                    }
                },
                "prior_experience": {
                    "programming_languages": ["Python", "JavaScript"],
                    "data_structures_familiarity": "intermediate",
                    "years_of_experience": 2
                }
            }
        }


# Request/Response models for API
class LearnerCreate(BaseModel):
    """Model for creating a new learner"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Plain password (will be hashed)")
    demographics: Optional[Demographics] = None
    preferences: Optional[LearningPreferences] = None
    prior_experience: Optional[PriorExperience] = None


class LearnerUpdate(BaseModel):
    """Model for updating learner profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    demographics: Optional[Demographics] = None
    preferences: Optional[LearningPreferences] = None
    prior_experience: Optional[PriorExperience] = None


class LearnerResponse(BaseModel):
    """Model for learner profile responses (excludes sensitive data)"""
    id: str = Field(..., description="Learner ID")
    username: str
    email: EmailStr
    demographics: Optional[Demographics] = None
    preferences: Optional[LearningPreferences] = None
    prior_experience: Optional[PriorExperience] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "username": "john_doe",
                "email": "john@example.com",
                "demographics": {
                    "age": 25,
                    "location": "San Francisco, CA"
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "is_active": True
            }
        }
EOF

echo "✅ Created src/models/learner.py"
echo "📋 Learner model includes:"
echo "   - Demographics with age, location, education"
echo "   - Learning preferences and accessibility needs"
echo "   - Prior experience in programming/data structures"
echo "   - Self-reported data for confidence and goals"
echo "   - Request/response models for API"
echo "   - GDPR-compliant data structure"