"""
Data models for adaptive challenge selection system.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
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


class BKTParameters(BaseModel):
    """Bayesian Knowledge Tracing parameters for a competency."""
    prior_knowledge: float = Field(default=0.1, ge=0.0, le=1.0, description="Initial probability of knowing the skill")
    learning_rate: float = Field(default=0.3, ge=0.0, le=1.0, description="Probability of learning the skill")
    slip_probability: float = Field(default=0.1, ge=0.0, le=1.0, description="Probability of making a mistake when knowing")
    guess_probability: float = Field(default=0.2, ge=0.0, le=1.0, description="Probability of guessing correctly when not knowing")


class CompetencyLevel(BaseModel):
    """Learner's competency level for a specific skill."""
    competency_id: PyObjectId = Field(alias="_id")
    competency_name: str
    mastery_probability: float = Field(ge=0.0, le=1.0, description="Current probability of mastery")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in the mastery estimate")
    last_updated: datetime
    bkt_parameters: BKTParameters
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ChallengeMetadata(BaseModel):
    """Metadata for a learning challenge."""
    challenge_id: PyObjectId = Field(alias="_id")
    title: str
    description: str
    competencies: List[PyObjectId] = Field(description="List of competency IDs this challenge addresses")
    difficulty_level: float = Field(ge=0.0, le=1.0, description="Normalized difficulty level")
    estimated_duration: int = Field(description="Estimated completion time in minutes")
    challenge_type: str = Field(description="Type of challenge (coding, quiz, exercise)")
    prerequisites: List[PyObjectId] = Field(default=[], description="Required competencies")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AdaptiveRecommendation(BaseModel):
    """Adaptive challenge recommendation for a learner."""
    challenge: ChallengeMetadata
    recommendation_score: float = Field(ge=0.0, le=1.0, description="How well this challenge fits the learner")
    target_competencies: List[CompetencyLevel] = Field(description="Competencies this challenge will help develop")
    reasoning: str = Field(description="Explanation for why this challenge was recommended")
    optimal_difficulty: float = Field(ge=0.0, le=1.0, description="Optimal difficulty for this learner")


class ChallengeSequence(BaseModel):
    """Personalized sequence of challenges for a learner."""
    learner_id: PyObjectId
    recommendations: List[AdaptiveRecommendation]
    sequence_id: str = Field(description="Unique identifier for this sequence")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(description="When this sequence should be refreshed")
    adaptation_context: Dict[str, Any] = Field(default={}, description="Context used for adaptation")


class DifficultyFeedback(BaseModel):
    """Learner feedback on challenge difficulty."""
    challenge_id: PyObjectId
    learner_id: PyObjectId
    perceived_difficulty: float = Field(ge=0.0, le=1.0, description="How difficult the learner found the challenge")
    actual_difficulty: float = Field(ge=0.0, le=1.0, description="System's assessed difficulty")
    completion_time: int = Field(description="Time taken to complete in minutes")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate on the challenge")
    feedback_text: Optional[str] = Field(default=None, description="Optional text feedback")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityResult(BaseModel):
    """Result of a completed learning activity."""
    learner_id: PyObjectId
    challenge_id: PyObjectId
    competencies_addressed: List[PyObjectId]
    success: bool = Field(description="Whether the activity was completed successfully")
    score: float = Field(ge=0.0, le=1.0, description="Normalized score achieved")
    attempts: int = Field(ge=1, description="Number of attempts made")
    time_spent: int = Field(description="Time spent in minutes")
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    difficulty_feedback: Optional[DifficultyFeedback] = None


class AdaptationRequest(BaseModel):
    """Request for adaptive challenge selection."""
    learner_id: PyObjectId
    current_competencies: List[CompetencyLevel]
    learning_goals: List[PyObjectId] = Field(default=[], description="Specific competencies to focus on")
    time_available: Optional[int] = Field(default=None, description="Available time in minutes")
    preferred_difficulty: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    challenge_types: List[str] = Field(default=[], description="Preferred challenge types")
    exclude_challenges: List[PyObjectId] = Field(default=[], description="Challenges to exclude")


class AdaptationResponse(BaseModel):
    """Response containing adaptive challenge recommendations."""
    learner_id: PyObjectId
    challenge_sequence: ChallengeSequence
    next_challenge: AdaptiveRecommendation
    alternative_challenges: List[AdaptiveRecommendation] = Field(default=[])
    adaptation_metadata: Dict[str, Any] = Field(default={})
    refresh_in_minutes: int = Field(description="When to request new recommendations")