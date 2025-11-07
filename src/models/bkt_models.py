"""
BKT (Bayesian Knowledge Tracing) Data Models

This module defines the data models for the BKT algorithm implementation,
including learner competency tracking, skill models, and performance data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
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


class BKTParameters(BaseModel):
    """BKT algorithm parameters for a specific skill"""
    
    skill_id: str = Field(..., description="Unique identifier for the skill")
    p_l0: float = Field(0.1, ge=0.0, le=1.0, description="Initial probability of knowing the skill")
    p_t: float = Field(0.1, ge=0.0, le=1.0, description="Probability of learning (transition)")
    p_g: float = Field(0.2, ge=0.0, le=1.0, description="Probability of guessing correctly")
    p_s: float = Field(0.1, ge=0.0, le=1.0, description="Probability of slipping (error when knowing)")
    
    @validator('p_g', 'p_s')
    def validate_guess_slip(cls, v, values):
        """Ensure P(G) + P(S) <= 1 for mathematical consistency"""
        if 'p_g' in values and v + values['p_g'] > 1.0:
            raise ValueError("P(G) + P(S) must be <= 1.0")
        return v


class LearnerCompetency(BaseModel):
    """Represents a learner's competency level for a specific skill"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    learner_id: str = Field(..., description="Unique identifier for the learner")
    skill_id: str = Field(..., description="Unique identifier for the skill")
    p_known: float = Field(..., ge=0.0, le=1.0, description="Current probability of knowing the skill")
    mastery_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Threshold for considering skill mastered")
    is_mastered: bool = Field(False, description="Whether the skill is considered mastered")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_attempts: int = Field(0, ge=0, description="Total number of attempts for this skill")
    correct_attempts: int = Field(0, ge=0, description="Number of correct attempts")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    @validator('correct_attempts')
    def validate_correct_attempts(cls, v, values):
        """Ensure correct attempts don't exceed total attempts"""
        if 'total_attempts' in values and v > values['total_attempts']:
            raise ValueError("Correct attempts cannot exceed total attempts")
        return v


class PerformanceEvent(BaseModel):
    """Represents a single performance event (answer/attempt) by a learner"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    learner_id: str = Field(..., description="Unique identifier for the learner")
    skill_id: str = Field(..., description="Unique identifier for the skill")
    activity_id: str = Field(..., description="Unique identifier for the learning activity")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    response_time: Optional[float] = Field(None, ge=0.0, description="Time taken to respond in seconds")
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Self-reported confidence")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event metadata")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BKTUpdateResult(BaseModel):
    """Result of a BKT update operation"""
    
    learner_id: str
    skill_id: str
    previous_p_known: float
    new_p_known: float
    is_mastered: bool
    mastery_gained: bool = Field(False, description="Whether mastery was gained in this update")
    update_timestamp: datetime = Field(default_factory=datetime.utcnow)


class SkillHierarchy(BaseModel):
    """Represents the hierarchical relationship between skills"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    skill_id: str = Field(..., description="Unique identifier for the skill")
    parent_skills: List[str] = Field(default_factory=list, description="List of prerequisite skill IDs")
    child_skills: List[str] = Field(default_factory=list, description="List of dependent skill IDs")
    difficulty_level: int = Field(1, ge=1, le=10, description="Difficulty level (1-10)")
    domain: str = Field(..., description="Subject domain (e.g., 'programming', 'mathematics')")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class LearnerProfile(BaseModel):
    """Extended learner profile with BKT-specific data"""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    learner_id: str = Field(..., description="Unique identifier for the learner")
    competencies: Dict[str, float] = Field(default_factory=dict, description="Skill ID to P(Known) mapping")
    learning_preferences: Dict[str, Any] = Field(default_factory=dict)
    performance_history: List[str] = Field(default_factory=list, description="List of performance event IDs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BKTConfiguration(BaseModel):
    """Global BKT algorithm configuration"""
    
    default_parameters: BKTParameters
    mastery_threshold: float = Field(0.8, ge=0.0, le=1.0)
    min_attempts_for_mastery: int = Field(3, ge=1)
    enable_forgetting: bool = Field(False, description="Whether to model skill forgetting over time")
    forgetting_rate: float = Field(0.01, ge=0.0, le=1.0, description="Daily forgetting rate if enabled")
    update_batch_size: int = Field(100, ge=1, description="Batch size for bulk updates")
    cache_ttl_seconds: int = Field(300, ge=0, description="Cache TTL for competency data")