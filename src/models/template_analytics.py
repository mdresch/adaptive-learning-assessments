"""
Template Analytics Data Models

This module contains data models for template entity profiles and document domain inference
functionality in the adaptive learning system.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId

from .learner_profile import PyObjectId


class TemplateType(str, Enum):
    """Template type enumeration"""
    QUIZ = "quiz"
    EXERCISE = "exercise"
    LESSON = "lesson"
    ASSESSMENT = "assessment"
    INTERACTIVE = "interactive"
    VIDEO = "video"
    READING = "reading"


class DomainCategory(str, Enum):
    """Learning domain categories"""
    PROGRAMMING = "programming"
    DATA_STRUCTURES = "data_structures"
    ALGORITHMS = "algorithms"
    MATHEMATICS = "mathematics"
    COMPUTER_SCIENCE = "computer_science"
    SOFTWARE_ENGINEERING = "software_engineering"
    WEB_DEVELOPMENT = "web_development"
    DATABASE = "database"
    MACHINE_LEARNING = "machine_learning"
    CYBERSECURITY = "cybersecurity"
    OTHER = "other"


class TemplateUsageMetrics(BaseModel):
    """Template usage metrics"""
    total_uses: int = Field(default=0, description="Total number of times template was used")
    unique_users: int = Field(default=0, description="Number of unique users who used this template")
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Average completion rate")
    average_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Average user score")
    average_time_spent: int = Field(default=0, description="Average time spent in seconds")
    last_used: Optional[datetime] = Field(default=None, description="Last time template was used")


class DomainAssociation(BaseModel):
    """Domain association with confidence score"""
    domain: DomainCategory = Field(..., description="Associated domain")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this association")
    evidence_count: int = Field(default=1, description="Number of evidence points supporting this association")


class TemplateEntityProfileBase(BaseModel):
    """Base template entity profile model"""
    template_id: str = Field(..., description="Unique template identifier")
    template_name: str = Field(..., min_length=1, max_length=200, description="Template name")
    template_type: TemplateType = Field(..., description="Type of template")
    description: Optional[str] = Field(None, max_length=1000, description="Template description")
    domain_associations: List[DomainAssociation] = Field(default_factory=list, description="Associated domains")
    usage_metrics: TemplateUsageMetrics = Field(default_factory=TemplateUsageMetrics, description="Usage statistics")
    effectiveness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall effectiveness score")
    tags: List[str] = Field(default_factory=list, description="Template tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional template metadata")
    is_active: bool = Field(default=True, description="Whether template is currently active")


class TemplateEntityProfileCreate(TemplateEntityProfileBase):
    """Template entity profile creation model"""
    pass


class TemplateEntityProfileUpdate(BaseModel):
    """Template entity profile update model"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=200)
    template_type: Optional[TemplateType] = None
    description: Optional[str] = Field(None, max_length=1000)
    domain_associations: Optional[List[DomainAssociation]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class TemplateEntityProfile(TemplateEntityProfileBase):
    """Complete template entity profile model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "template_id": "quiz_001",
                "template_name": "Basic Python Quiz",
                "template_type": "quiz",
                "description": "A quiz covering basic Python concepts",
                "domain_associations": [
                    {
                        "domain": "programming",
                        "confidence": 0.95,
                        "evidence_count": 10
                    }
                ],
                "usage_metrics": {
                    "total_uses": 150,
                    "unique_users": 75,
                    "completion_rate": 0.85,
                    "average_score": 0.78,
                    "average_time_spent": 1200
                },
                "effectiveness_score": 0.82,
                "tags": ["python", "basics", "programming"],
                "is_active": True
            }
        }


class DocumentDomainInferenceBase(BaseModel):
    """Base document domain inference model"""
    document_id: str = Field(..., description="Unique document identifier")
    document_type: str = Field(..., description="Type of document")
    inferred_primary_domain: DomainCategory = Field(..., description="Primary inferred domain")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in primary domain inference")
    secondary_domains: List[DomainAssociation] = Field(default_factory=list, description="Secondary domain associations")
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict, description="Analysis metadata and features")
    content_features: Dict[str, float] = Field(default_factory=dict, description="Extracted content features")
    manual_override: Optional[DomainCategory] = Field(None, description="Manual domain override if needed")


class DocumentDomainInferenceCreate(DocumentDomainInferenceBase):
    """Document domain inference creation model"""
    pass


class DocumentDomainInferenceUpdate(BaseModel):
    """Document domain inference update model"""
    inferred_primary_domain: Optional[DomainCategory] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    secondary_domains: Optional[List[DomainAssociation]] = None
    analysis_metadata: Optional[Dict[str, Any]] = None
    content_features: Optional[Dict[str, float]] = None
    manual_override: Optional[DomainCategory] = None


class DocumentDomainInference(DocumentDomainInferenceBase):
    """Complete document domain inference model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    inference_date: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "document_id": "doc_001",
                "document_type": "lesson",
                "inferred_primary_domain": "programming",
                "confidence_score": 0.89,
                "secondary_domains": [
                    {
                        "domain": "data_structures",
                        "confidence": 0.65,
                        "evidence_count": 5
                    }
                ],
                "analysis_metadata": {
                    "algorithm_version": "1.0",
                    "processing_time_ms": 150,
                    "features_analyzed": ["keywords", "content_structure", "examples"]
                },
                "content_features": {
                    "programming_keywords_ratio": 0.15,
                    "code_examples_count": 3,
                    "technical_complexity": 0.7
                }
            }
        }


class TemplateAnalyticsAggregation(BaseModel):
    """Template analytics aggregation results"""
    total_templates: int = Field(..., description="Total number of templates")
    active_templates: int = Field(..., description="Number of active templates")
    templates_by_type: Dict[str, int] = Field(..., description="Template count by type")
    templates_by_domain: Dict[str, int] = Field(..., description="Template count by domain")
    average_effectiveness: float = Field(..., description="Average effectiveness score")
    top_performing_templates: List[Dict[str, Any]] = Field(..., description="Top performing templates")
    usage_trends: Dict[str, Any] = Field(..., description="Usage trend data")


class DomainAnalyticsAggregation(BaseModel):
    """Domain analytics aggregation results"""
    total_documents: int = Field(..., description="Total number of analyzed documents")
    domain_distribution: Dict[str, int] = Field(..., description="Document count by domain")
    average_confidence: float = Field(..., description="Average confidence score")
    high_confidence_documents: int = Field(..., description="Number of high confidence inferences")
    domain_trends: Dict[str, Any] = Field(..., description="Domain trend data")
    content_feature_stats: Dict[str, Dict[str, float]] = Field(..., description="Content feature statistics")


# Response models for API endpoints
class TemplateEntityProfileResponse(BaseModel):
    """Template entity profile API response"""
    id: str
    template_id: str
    template_name: str
    template_type: str
    description: Optional[str]
    domain_associations: List[DomainAssociation]
    usage_metrics: TemplateUsageMetrics
    effectiveness_score: float
    tags: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str}


class DocumentDomainInferenceResponse(BaseModel):
    """Document domain inference API response"""
    id: str
    document_id: str
    document_type: str
    inferred_primary_domain: str
    confidence_score: float
    secondary_domains: List[DomainAssociation]
    manual_override: Optional[str]
    inference_date: datetime
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str}