"""
Competency and skill tracking models for the Adaptive Learning System.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class CompetencyType(str, Enum):
    """Types of competencies."""
    CONCEPT = "concept"
    SKILL = "skill"
    KNOWLEDGE = "knowledge"
    APPLICATION = "application"


class DifficultyLevel(str, Enum):
    """Difficulty levels for competencies."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CompetencyLevel(str, Enum):
    """Learner competency achievement levels."""
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    PRACTICING = "practicing"
    MASTERED = "mastered"
    EXPERT = "expert"


class Competency(BaseModel):
    """Core competency definition model."""
    id: Optional[str] = Field(None, alias="_id")
    competency_id: str = Field(..., description="Unique competency identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Competency name")
    description: str = Field(..., description="Detailed competency description")
    
    # Categorization
    category: str = Field(..., description="Competency category (e.g., 'data_structures')")
    subcategory: Optional[str] = Field(None, description="Competency subcategory")
    competency_type: CompetencyType = Field(
        CompetencyType.CONCEPT,
        description="Type of competency"
    )
    difficulty_level: DifficultyLevel = Field(
        DifficultyLevel.BEGINNER,
        description="Base difficulty level"
    )
    
    # Relationships
    prerequisites: List[str] = Field(
        default_factory=list,
        description="Required prerequisite competency IDs"
    )
    related_competencies: List[str] = Field(
        default_factory=list,
        description="Related competency IDs"
    )
    
    # Learning objectives
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="Specific learning objectives"
    )
    assessment_criteria: List[str] = Field(
        default_factory=list,
        description="Criteria for assessing mastery"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    estimated_hours: Optional[float] = Field(
        None,
        ge=0.1,
        le=100.0,
        description="Estimated learning time in hours"
    )
    
    # System metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether competency is active")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "competency_id": "arrays_basic",
                "name": "Basic Array Operations",
                "description": "Understanding array creation, access, and basic operations",
                "category": "data_structures",
                "subcategory": "arrays",
                "competency_type": "skill",
                "difficulty_level": "beginner",
                "learning_objectives": [
                    "Create arrays in programming language",
                    "Access array elements by index",
                    "Perform basic array operations"
                ],
                "estimated_hours": 2.5
            }
        }


class LearnerCompetency(BaseModel):
    """Learner's competency tracking and progress."""
    id: Optional[str] = Field(None, alias="_id")
    learner_id: str = Field(..., description="Learner identifier")
    competency_id: str = Field(..., description="Competency identifier")
    
    # Current status
    current_level: CompetencyLevel = Field(
        CompetencyLevel.NOT_STARTED,
        description="Current achievement level"
    )
    mastery_probability: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="BKT-calculated mastery probability"
    )
    confidence_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in mastery assessment"
    )
    
    # Progress tracking
    attempts_count: int = Field(0, ge=0, description="Total attempts on this competency")
    successful_attempts: int = Field(0, ge=0, description="Successful attempts")
    time_spent_minutes: float = Field(0.0, ge=0.0, description="Total time spent")
    
    # BKT parameters (specific to this learner-competency pair)
    prior_knowledge: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Prior knowledge probability"
    )
    learning_rate: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Learning rate parameter"
    )
    guess_probability: float = Field(
        0.25,
        ge=0.0,
        le=1.0,
        description="Probability of correct guess"
    )
    slip_probability: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Probability of slip (knowing but answering incorrectly)"
    )
    
    # Learning path
    recommended_activities: List[str] = Field(
        default_factory=list,
        description="Recommended activity IDs"
    )
    completed_activities: List[str] = Field(
        default_factory=list,
        description="Completed activity IDs"
    )
    
    # Timestamps
    first_attempt: Optional[datetime] = None
    last_attempt: Optional[datetime] = None
    mastery_achieved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    
    @validator('successful_attempts')
    def validate_successful_attempts(cls, v, values):
        if 'attempts_count' in values and v > values['attempts_count']:
            raise ValueError('Successful attempts cannot exceed total attempts')
        return v
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()


class CompetencyProgress(BaseModel):
    """Aggregated competency progress for reporting."""
    learner_id: str
    competency_id: str
    competency_name: str
    category: str
    current_level: CompetencyLevel
    mastery_probability: float
    progress_percentage: float
    time_spent_hours: float
    last_activity: Optional[datetime]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }