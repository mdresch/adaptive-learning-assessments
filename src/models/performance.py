"""
Performance tracking and activity models for the Adaptive Learning System.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class ActivityType(str, Enum):
    """Types of learning activities."""
    QUIZ = "quiz"
    CODING_CHALLENGE = "coding_challenge"
    INTERACTIVE_EXERCISE = "interactive_exercise"
    VIDEO = "video"
    READING = "reading"
    PRACTICE_PROBLEM = "practice_problem"
    PROJECT = "project"


class ActivityStatus(str, Enum):
    """Activity completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class InteractionType(str, Enum):
    """Types of learner interactions."""
    START_ACTIVITY = "start_activity"
    SUBMIT_ANSWER = "submit_answer"
    REQUEST_HINT = "request_hint"
    PAUSE_ACTIVITY = "pause_activity"
    RESUME_ACTIVITY = "resume_activity"
    COMPLETE_ACTIVITY = "complete_activity"
    SKIP_ACTIVITY = "skip_activity"


class LearningActivity(BaseModel):
    """Learning activity definition."""
    id: Optional[str] = Field(None, alias="_id")
    activity_id: str = Field(..., description="Unique activity identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Activity name")
    description: str = Field(..., description="Activity description")
    
    # Activity properties
    activity_type: ActivityType = Field(..., description="Type of activity")
    difficulty_level: str = Field(..., description="Difficulty level")
    estimated_duration_minutes: int = Field(
        15,
        ge=1,
        le=300,
        description="Estimated completion time"
    )
    
    # Content and structure
    content: Dict[str, Any] = Field(
        default_factory=dict,
        description="Activity content and configuration"
    )
    questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Questions or challenges in the activity"
    )
    
    # Competency mapping
    target_competencies: List[str] = Field(
        default_factory=list,
        description="Competency IDs this activity targets"
    )
    prerequisite_competencies: List[str] = Field(
        default_factory=list,
        description="Required competency IDs"
    )
    
    # Scoring and assessment
    max_score: float = Field(100.0, ge=0.0, description="Maximum possible score")
    passing_score: float = Field(70.0, ge=0.0, description="Minimum passing score")
    scoring_method: str = Field(
        "percentage",
        description="Scoring method: percentage, points, binary"
    )
    
    # Adaptive parameters
    adaptive_difficulty: bool = Field(
        True,
        description="Whether difficulty adapts based on performance"
    )
    hints_available: bool = Field(True, description="Whether hints are available")
    max_attempts: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum attempts allowed"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether activity is active")
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ActivityResult(BaseModel):
    """Result of a completed activity attempt."""
    id: Optional[str] = Field(None, alias="_id")
    result_id: str = Field(..., description="Unique result identifier")
    learner_id: str = Field(..., description="Learner identifier")
    activity_id: str = Field(..., description="Activity identifier")
    
    # Attempt information
    attempt_number: int = Field(1, ge=1, description="Attempt number for this activity")
    status: ActivityStatus = Field(..., description="Completion status")
    
    # Performance metrics
    score: float = Field(0.0, ge=0.0, description="Achieved score")
    max_possible_score: float = Field(100.0, ge=0.0, description="Maximum possible score")
    percentage_score: float = Field(0.0, ge=0.0, le=100.0, description="Percentage score")
    
    # Time tracking
    start_time: datetime = Field(..., description="Activity start time")
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = Field(None, ge=0.0, description="Duration in minutes")
    
    # Detailed responses
    responses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Individual question responses"
    )
    correct_answers: int = Field(0, ge=0, description="Number of correct answers")
    total_questions: int = Field(0, ge=0, description="Total number of questions")
    
    # Learning analytics
    hints_used: int = Field(0, ge=0, description="Number of hints used")
    time_per_question: List[float] = Field(
        default_factory=list,
        description="Time spent on each question"
    )
    difficulty_progression: List[str] = Field(
        default_factory=list,
        description="Difficulty levels encountered"
    )
    
    # Competency impact
    competency_updates: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Competency probability updates from this attempt"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    
    @validator('percentage_score', always=True)
    def calculate_percentage(cls, v, values):
        if 'score' in values and 'max_possible_score' in values:
            max_score = values['max_possible_score']
            if max_score > 0:
                return (values['score'] / max_score) * 100
        return v
    
    @validator('duration_minutes', always=True)
    def calculate_duration(cls, v, values):
        if 'start_time' in values and 'end_time' in values and values['end_time']:
            delta = values['end_time'] - values['start_time']
            return delta.total_seconds() / 60
        return v


class PerformanceRecord(BaseModel):
    """Detailed performance tracking record."""
    id: Optional[str] = Field(None, alias="_id")
    record_id: str = Field(..., description="Unique record identifier")
    learner_id: str = Field(..., description="Learner identifier")
    activity_id: str = Field(..., description="Activity identifier")
    
    # Interaction details
    interaction_type: InteractionType = Field(..., description="Type of interaction")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Context information
    session_id: str = Field(..., description="Learning session identifier")
    competency_id: Optional[str] = Field(None, description="Related competency")
    question_id: Optional[str] = Field(None, description="Specific question ID")
    
    # Interaction data
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Interaction-specific data"
    )
    response: Optional[Union[str, int, float, bool, Dict[str, Any]]] = Field(
        None,
        description="Learner response or action"
    )
    is_correct: Optional[bool] = Field(None, description="Whether response was correct")
    
    # Performance context
    current_difficulty: Optional[str] = Field(None, description="Current difficulty level")
    time_since_start: Optional[float] = Field(
        None,
        ge=0.0,
        description="Time since activity start in minutes"
    )
    
    # System state
    bkt_state_before: Optional[Dict[str, float]] = Field(
        None,
        description="BKT parameters before this interaction"
    )
    bkt_state_after: Optional[Dict[str, float]] = Field(
        None,
        description="BKT parameters after this interaction"
    )
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class LearningSession(BaseModel):
    """Learning session tracking."""
    id: Optional[str] = Field(None, alias="_id")
    session_id: str = Field(..., description="Unique session identifier")
    learner_id: str = Field(..., description="Learner identifier")
    
    # Session details
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    
    # Activities in session
    activities_attempted: List[str] = Field(
        default_factory=list,
        description="Activity IDs attempted in this session"
    )
    activities_completed: List[str] = Field(
        default_factory=list,
        description="Activity IDs completed in this session"
    )
    
    # Session metrics
    total_score: float = Field(0.0, ge=0.0, description="Total score achieved")
    total_questions: int = Field(0, ge=0, description="Total questions attempted")
    correct_answers: int = Field(0, ge=0, description="Total correct answers")
    
    # Learning progress
    competencies_practiced: List[str] = Field(
        default_factory=list,
        description="Competency IDs practiced"
    )
    mastery_improvements: Dict[str, float] = Field(
        default_factory=dict,
        description="Competency mastery probability improvements"
    )
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }