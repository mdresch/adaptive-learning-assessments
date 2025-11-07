"""
Data models for mastery tracking system.

This module defines Pydantic models for learner interactions, competencies,
and mastery tracking data structures used in the Bayesian Knowledge Tracing system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""
    
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


class ActivityType(str, Enum):
    """Types of learning activities."""
    QUIZ = "quiz"
    CODING_CHALLENGE = "coding_challenge"
    INTERACTIVE_EXERCISE = "interactive_exercise"
    ASSESSMENT = "assessment"


class InteractionType(str, Enum):
    """Types of learner interactions."""
    ATTEMPT = "attempt"
    COMPLETION = "completion"
    HINT_REQUEST = "hint_request"
    SUBMISSION = "submission"
    REVIEW = "review"


class DifficultyLevel(str, Enum):
    """Difficulty levels for activities."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MicroCompetency(BaseModel):
    """Represents a granular skill or knowledge component."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    competency_id: str = Field(..., description="Unique identifier for the competency")
    name: str = Field(..., description="Human-readable name of the competency")
    description: str = Field(..., description="Detailed description of the competency")
    category: str = Field(..., description="Category or domain (e.g., 'data_structures', 'algorithms')")
    subcategory: Optional[str] = Field(None, description="Subcategory for finer classification")
    prerequisites: List[str] = Field(default_factory=list, description="List of prerequisite competency IDs")
    difficulty_level: DifficultyLevel = Field(..., description="Difficulty level of the competency")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class LearnerInteraction(BaseModel):
    """Represents a single learner interaction with an activity."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    learner_id: str = Field(..., description="Unique identifier for the learner")
    activity_id: str = Field(..., description="Unique identifier for the activity")
    activity_type: ActivityType = Field(..., description="Type of activity")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    competency_ids: List[str] = Field(..., description="List of competencies addressed in this interaction")
    
    # Performance data
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized score (0.0 to 1.0)")
    is_correct: Optional[bool] = Field(None, description="Whether the response was correct")
    attempts: int = Field(default=1, ge=1, description="Number of attempts made")
    time_spent: Optional[float] = Field(None, ge=0.0, description="Time spent in seconds")
    hints_used: int = Field(default=0, ge=0, description="Number of hints requested")
    
    # Context data
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Difficulty level of the activity")
    session_id: Optional[str] = Field(None, description="Session identifier for grouping interactions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="When the interaction started")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="When the interaction was completed")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BKTParameters(BaseModel):
    """Bayesian Knowledge Tracing parameters for a competency."""
    
    prior_knowledge: float = Field(default=0.1, ge=0.0, le=1.0, description="P(L0) - Initial probability of knowing the skill")
    learning_rate: float = Field(default=0.3, ge=0.0, le=1.0, description="P(T) - Probability of learning the skill")
    slip_probability: float = Field(default=0.1, ge=0.0, le=1.0, description="P(S) - Probability of making a mistake despite knowing")
    guess_probability: float = Field(default=0.25, ge=0.0, le=1.0, description="P(G) - Probability of guessing correctly")


class MasteryLevel(BaseModel):
    """Represents a learner's mastery level for a specific competency."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    learner_id: str = Field(..., description="Unique identifier for the learner")
    competency_id: str = Field(..., description="Unique identifier for the competency")
    
    # BKT state
    current_mastery: float = Field(..., ge=0.0, le=1.0, description="Current probability of mastery")
    bkt_parameters: BKTParameters = Field(default_factory=BKTParameters, description="BKT model parameters")
    
    # Performance statistics
    total_interactions: int = Field(default=0, ge=0, description="Total number of interactions")
    correct_interactions: int = Field(default=0, ge=0, description="Number of correct interactions")
    average_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average score across interactions")
    recent_performance: List[float] = Field(default_factory=list, description="Recent performance scores (last 10)")
    
    # Confidence metrics
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Learner's self-reported confidence")
    mastery_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Threshold for considering mastery achieved")
    is_mastered: bool = Field(default=False, description="Whether mastery threshold has been reached")
    
    # Timestamps
    first_interaction: Optional[datetime] = Field(None, description="Timestamp of first interaction")
    last_interaction: Optional[datetime] = Field(None, description="Timestamp of most recent interaction")
    mastery_achieved_at: Optional[datetime] = Field(None, description="When mastery was first achieved")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ProgressReport(BaseModel):
    """Comprehensive progress report for a learner."""
    
    learner_id: str = Field(..., description="Unique identifier for the learner")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Overall statistics
    total_competencies: int = Field(..., ge=0, description="Total number of competencies tracked")
    mastered_competencies: int = Field(..., ge=0, description="Number of competencies mastered")
    mastery_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall mastery percentage")
    
    # Competency breakdown
    competency_mastery: List[MasteryLevel] = Field(..., description="Detailed mastery levels per competency")
    
    # Performance trends
    recent_interactions: List[LearnerInteraction] = Field(default_factory=list, description="Recent interactions")
    performance_trend: List[Dict[str, Any]] = Field(default_factory=list, description="Performance over time")
    
    # Recommendations
    recommended_activities: List[str] = Field(default_factory=list, description="Recommended activity IDs")
    focus_areas: List[str] = Field(default_factory=list, description="Competencies needing attention")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class InteractionLogRequest(BaseModel):
    """Request model for logging learner interactions."""
    
    learner_id: str = Field(..., description="Unique identifier for the learner")
    activity_id: str = Field(..., description="Unique identifier for the activity")
    activity_type: ActivityType = Field(..., description="Type of activity")
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    competency_ids: List[str] = Field(..., description="List of competencies addressed")
    
    # Performance data
    score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized score")
    is_correct: Optional[bool] = Field(None, description="Whether the response was correct")
    attempts: int = Field(default=1, ge=1, description="Number of attempts")
    time_spent: Optional[float] = Field(None, ge=0.0, description="Time spent in seconds")
    hints_used: int = Field(default=0, ge=0, description="Number of hints used")
    
    # Context
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Activity difficulty")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="When interaction started")
    completed_at: Optional[datetime] = Field(None, description="When interaction completed")


class MasteryUpdateResponse(BaseModel):
    """Response model for mastery updates."""
    
    learner_id: str = Field(..., description="Learner identifier")
    updated_competencies: List[str] = Field(..., description="List of updated competency IDs")
    new_mastery_levels: Dict[str, float] = Field(..., description="New mastery levels by competency ID")
    newly_mastered: List[str] = Field(default_factory=list, description="Newly mastered competencies")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)