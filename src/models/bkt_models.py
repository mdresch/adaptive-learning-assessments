"""
Bayesian Knowledge Tracing (BKT) specific models for the Adaptive Learning System.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class BKTParameters(BaseModel):
    """BKT model parameters for a specific competency."""
    id: Optional[str] = Field(None, alias="_id")
    competency_id: str = Field(..., description="Competency identifier")
    
    # Core BKT parameters
    prior_knowledge: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="P(L0) - Initial probability of knowing the skill"
    )
    learning_rate: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="P(T) - Probability of learning the skill on each opportunity"
    )
    guess_probability: float = Field(
        0.25,
        ge=0.0,
        le=1.0,
        description="P(G) - Probability of guessing correctly when not knowing"
    )
    slip_probability: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="P(S) - Probability of making an error when knowing"
    )
    
    # Parameter metadata
    parameter_source: str = Field(
        "default",
        description="Source of parameters: default, fitted, expert"
    )
    confidence_level: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in parameter estimates"
    )
    sample_size: int = Field(
        0,
        ge=0,
        description="Number of observations used to fit parameters"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_fitted: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "competency_id": "arrays_basic",
                "prior_knowledge": 0.1,
                "learning_rate": 0.3,
                "guess_probability": 0.25,
                "slip_probability": 0.1,
                "parameter_source": "fitted",
                "confidence_level": 0.8,
                "sample_size": 150
            }
        }
    
    @validator('updated_at', always=True)
    def set_updated_at(cls, v):
        return datetime.utcnow()


class BKTState(BaseModel):
    """Current BKT state for a learner-competency pair."""
    id: Optional[str] = Field(None, alias="_id")
    learner_id: str = Field(..., description="Learner identifier")
    competency_id: str = Field(..., description="Competency identifier")
    
    # Current state
    mastery_probability: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Current probability of mastery P(Ln)"
    )
    evidence_count: int = Field(
        0,
        ge=0,
        description="Number of evidence observations"
    )
    
    # Performance history summary
    total_attempts: int = Field(0, ge=0, description="Total attempts")
    correct_attempts: int = Field(0, ge=0, description="Correct attempts")
    recent_performance: List[bool] = Field(
        default_factory=list,
        description="Recent performance history (True=correct, False=incorrect)"
    )
    
    # Learning trajectory
    mastery_trajectory: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical mastery probability updates"
    )
    learning_velocity: float = Field(
        0.0,
        description="Rate of learning (change in mastery probability)"
    )
    
    # Confidence and reliability
    confidence_interval: Dict[str, float] = Field(
        default_factory=lambda: {"lower": 0.0, "upper": 1.0},
        description="Confidence interval for mastery probability"
    )
    prediction_accuracy: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Historical prediction accuracy"
    )
    
    # Timestamps
    first_attempt: Optional[datetime] = None
    last_update: datetime = Field(default_factory=datetime.utcnow)
    mastery_achieved_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
    
    @validator('correct_attempts')
    def validate_correct_attempts(cls, v, values):
        if 'total_attempts' in values and v > values['total_attempts']:
            raise ValueError('Correct attempts cannot exceed total attempts')
        return v
    
    @validator('recent_performance')
    def limit_recent_performance(cls, v):
        # Keep only the last 20 attempts for efficiency
        return v[-20:] if len(v) > 20 else v


class CompetencyUpdate(BaseModel):
    """Record of a BKT update event."""
    id: Optional[str] = Field(None, alias="_id")
    update_id: str = Field(..., description="Unique update identifier")
    learner_id: str = Field(..., description="Learner identifier")
    competency_id: str = Field(..., description="Competency identifier")
    
    # Update context
    activity_id: str = Field(..., description="Activity that triggered update")
    question_id: Optional[str] = Field(None, description="Specific question ID")
    session_id: str = Field(..., description="Learning session identifier")
    
    # Evidence
    is_correct: bool = Field(..., description="Whether the response was correct")
    response_time_seconds: Optional[float] = Field(
        None,
        ge=0.0,
        description="Time taken to respond"
    )
    difficulty_level: Optional[str] = Field(None, description="Question difficulty")
    
    # BKT calculation details
    prior_mastery: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mastery probability before update"
    )
    posterior_mastery: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mastery probability after update"
    )
    mastery_change: float = Field(
        ...,
        description="Change in mastery probability"
    )
    
    # Parameters used
    bkt_parameters: Dict[str, float] = Field(
        ...,
        description="BKT parameters used for this update"
    )
    
    # Update metadata
    update_method: str = Field(
        "standard_bkt",
        description="Method used for update: standard_bkt, adaptive_bkt, etc."
    )
    confidence_score: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in this update"
    )
    
    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "update_id": "update_123",
                "learner_id": "learner_456",
                "competency_id": "arrays_basic",
                "activity_id": "quiz_arrays_01",
                "is_correct": True,
                "prior_mastery": 0.3,
                "posterior_mastery": 0.45,
                "mastery_change": 0.15,
                "bkt_parameters": {
                    "prior_knowledge": 0.1,
                    "learning_rate": 0.3,
                    "guess_probability": 0.25,
                    "slip_probability": 0.1
                }
            }
        }


class BKTDiagnostics(BaseModel):
    """Diagnostic information for BKT model performance."""
    competency_id: str = Field(..., description="Competency identifier")
    
    # Model fit statistics
    log_likelihood: float = Field(..., description="Model log-likelihood")
    aic: float = Field(..., description="Akaike Information Criterion")
    bic: float = Field(..., description="Bayesian Information Criterion")
    
    # Prediction accuracy
    overall_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall prediction accuracy"
    )
    precision: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Precision of mastery predictions"
    )
    recall: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Recall of mastery predictions"
    )
    f1_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="F1 score for mastery predictions"
    )
    
    # Parameter stability
    parameter_stability: Dict[str, float] = Field(
        default_factory=dict,
        description="Stability metrics for each parameter"
    )
    convergence_iterations: int = Field(
        ...,
        ge=0,
        description="Iterations required for parameter convergence"
    )
    
    # Data quality
    sample_size: int = Field(..., ge=0, description="Sample size used")
    data_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall data quality score"
    )
    
    # Timestamps
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }