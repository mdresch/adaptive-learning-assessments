"""
BKT API Endpoints

FastAPI endpoints for BKT algorithm operations including real-time competency updates,
performance tracking, and mastery assessment.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..core.bkt_engine import BKTEngine
from ..models.bkt_models import (
    BKTParameters, LearnerCompetency, PerformanceEvent, 
    BKTUpdateResult, BKTConfiguration
)
from ..utils.dependencies import get_bkt_engine, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/bkt", tags=["BKT Algorithm"])


# Request/Response models
class PerformanceEventRequest(BaseModel):
    """Request model for submitting a performance event"""
    learner_id: str = Field(..., description="Unique identifier for the learner")
    skill_id: str = Field(..., description="Unique identifier for the skill")
    activity_id: str = Field(..., description="Unique identifier for the learning activity")
    is_correct: bool = Field(..., description="Whether the response was correct")
    response_time: Optional[float] = Field(None, ge=0.0, description="Time taken to respond in seconds")
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Self-reported confidence")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event metadata")


class BatchPerformanceRequest(BaseModel):
    """Request model for batch performance event submission"""
    events: List[PerformanceEventRequest] = Field(..., description="List of performance events")


class CompetencyResponse(BaseModel):
    """Response model for competency data"""
    learner_id: str
    skill_id: str
    p_known: float
    is_mastered: bool
    mastery_threshold: float
    total_attempts: int
    correct_attempts: int
    last_updated: datetime


class PredictionResponse(BaseModel):
    """Response model for performance prediction"""
    learner_id: str
    skill_id: str
    probability_correct: float
    confidence_interval: float
    prediction_timestamp: datetime


class MasteryStatusResponse(BaseModel):
    """Response model for mastery status"""
    learner_id: str
    mastered_skills: List[str]
    total_skills: int
    mastery_rate: float


# Endpoints
@router.post("/events", response_model=BKTUpdateResult)
async def submit_performance_event(
    event_request: PerformanceEventRequest,
    background_tasks: BackgroundTasks,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a single performance event and update learner competency in real-time.
    
    This endpoint processes a learner's response to a learning activity and updates
    their competency level using the BKT algorithm.
    """
    try:
        # Validate permissions (learners can only submit their own events)
        if current_user.get("role") == "learner" and current_user.get("id") != event_request.learner_id:
            raise HTTPException(status_code=403, detail="Cannot submit events for other learners")
        
        # Update competency using BKT algorithm
        result = await bkt_engine.update_competency(
            learner_id=event_request.learner_id,
            skill_id=event_request.skill_id,
            is_correct=event_request.is_correct,
            activity_id=event_request.activity_id,
            response_time=event_request.response_time,
            confidence_level=event_request.confidence_level,
            metadata=event_request.metadata
        )
        
        # Log significant changes for analytics
        if result.mastery_gained:
            logger.info(f"Mastery gained: learner {result.learner_id}, skill {result.skill_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to submit performance event: {e}")
        raise HTTPException(status_code=500, detail="Failed to process performance event")


@router.post("/events/batch", response_model=List[BKTUpdateResult])
async def submit_batch_performance_events(
    batch_request: BatchPerformanceRequest,
    background_tasks: BackgroundTasks,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit multiple performance events in batch for optimized processing.
    
    This endpoint is designed for high-throughput scenarios and bulk data imports.
    """
    try:
        # Validate permissions
        if current_user.get("role") == "learner":
            learner_id = current_user.get("id")
            for event in batch_request.events:
                if event.learner_id != learner_id:
                    raise HTTPException(status_code=403, detail="Cannot submit events for other learners")
        
        # Convert requests to performance events
        events = []
        for event_req in batch_request.events:
            event = PerformanceEvent(
                learner_id=event_req.learner_id,
                skill_id=event_req.skill_id,
                activity_id=event_req.activity_id,
                is_correct=event_req.is_correct,
                response_time=event_req.response_time,
                confidence_level=event_req.confidence_level,
                metadata=event_req.metadata
            )
            events.append(event)
        
        # Process batch update
        results = await bkt_engine.batch_update_competencies(events)
        
        # Log batch statistics
        mastery_gains = sum(1 for r in results if r.mastery_gained)
        logger.info(f"Batch processed: {len(events)} events, {mastery_gains} mastery gains")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to submit batch performance events: {e}")
        raise HTTPException(status_code=500, detail="Failed to process batch events")


@router.get("/competencies/{learner_id}", response_model=Dict[str, CompetencyResponse])
async def get_learner_competencies(
    learner_id: str,
    skill_ids: Optional[List[str]] = Query(None, description="Specific skills to retrieve"),
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Get current competency levels for a learner across all or specified skills.
    """
    try:
        # Validate permissions
        if current_user.get("role") == "learner" and current_user.get("id") != learner_id:
            raise HTTPException(status_code=403, detail="Cannot access other learners' competencies")
        
        # Get competencies
        competencies = await bkt_engine.get_learner_competencies(learner_id, skill_ids)
        
        # Convert to response format
        response = {}
        for skill_id, competency in competencies.items():
            response[skill_id] = CompetencyResponse(
                learner_id=competency.learner_id,
                skill_id=competency.skill_id,
                p_known=competency.p_known,
                is_mastered=competency.is_mastered,
                mastery_threshold=competency.mastery_threshold,
                total_attempts=competency.total_attempts,
                correct_attempts=competency.correct_attempts,
                last_updated=competency.last_updated
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get learner competencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve competencies")


@router.get("/prediction/{learner_id}/{skill_id}", response_model=PredictionResponse)
async def predict_performance(
    learner_id: str,
    skill_id: str,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Predict the probability of correct response for a learner on a specific skill.
    """
    try:
        # Validate permissions
        if current_user.get("role") == "learner" and current_user.get("id") != learner_id:
            raise HTTPException(status_code=403, detail="Cannot access predictions for other learners")
        
        # Get prediction
        probability_correct, confidence_interval = await bkt_engine.predict_performance(learner_id, skill_id)
        
        return PredictionResponse(
            learner_id=learner_id,
            skill_id=skill_id,
            probability_correct=probability_correct,
            confidence_interval=confidence_interval,
            prediction_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Failed to predict performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate prediction")


@router.get("/mastery/{learner_id}", response_model=MasteryStatusResponse)
async def get_mastery_status(
    learner_id: str,
    skill_ids: Optional[List[str]] = Query(None, description="Specific skills to check"),
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Get mastery status for a learner's skills.
    """
    try:
        # Validate permissions
        if current_user.get("role") == "learner" and current_user.get("id") != learner_id:
            raise HTTPException(status_code=403, detail="Cannot access mastery status for other learners")
        
        # Get mastery status
        mastery_status = await bkt_engine.get_mastery_status(learner_id, skill_ids)
        
        # Calculate statistics
        mastered_skills = [skill_id for skill_id, is_mastered in mastery_status.items() if is_mastered]
        total_skills = len(mastery_status)
        mastery_rate = len(mastered_skills) / total_skills if total_skills > 0 else 0.0
        
        return MasteryStatusResponse(
            learner_id=learner_id,
            mastered_skills=mastered_skills,
            total_skills=total_skills,
            mastery_rate=mastery_rate
        )
        
    except Exception as e:
        logger.error(f"Failed to get mastery status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mastery status")


@router.get("/parameters/{skill_id}", response_model=BKTParameters)
async def get_skill_parameters(
    skill_id: str,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Get BKT parameters for a specific skill.
    
    Requires educator or admin role.
    """
    try:
        # Validate permissions
        if current_user.get("role") not in ["educator", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get parameters from engine's internal cache
        parameters = await bkt_engine._get_skill_parameters(skill_id)
        return parameters
        
    except Exception as e:
        logger.error(f"Failed to get skill parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve skill parameters")


@router.put("/parameters/{skill_id}", response_model=BKTParameters)
async def update_skill_parameters(
    skill_id: str,
    parameters: BKTParameters,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Update BKT parameters for a specific skill.
    
    Requires admin role.
    """
    try:
        # Validate permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin role required")
        
        # Ensure skill_id matches
        if parameters.skill_id != skill_id:
            raise HTTPException(status_code=400, detail="Skill ID mismatch")
        
        # Save parameters
        await bkt_engine.repository.save_skill_parameters(parameters)
        
        # Update engine cache
        bkt_engine._skill_parameters[skill_id] = parameters
        
        logger.info(f"Updated BKT parameters for skill {skill_id}")
        return parameters
        
    except Exception as e:
        logger.error(f"Failed to update skill parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to update skill parameters")


@router.get("/analytics/skill/{skill_id}")
async def get_skill_analytics(
    skill_id: str,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics and statistics for a specific skill.
    
    Requires educator or admin role.
    """
    try:
        # Validate permissions
        if current_user.get("role") not in ["educator", "admin"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Get statistics from repository
        stats = await bkt_engine.repository.get_competency_statistics(skill_id)
        
        return {
            "skill_id": skill_id,
            "statistics": stats,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get skill analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve skill analytics")


@router.get("/analytics/learner/{learner_id}")
async def get_learner_analytics(
    learner_id: str,
    bkt_engine: BKTEngine = Depends(get_bkt_engine),
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics and progress summary for a specific learner.
    """
    try:
        # Validate permissions
        if current_user.get("role") == "learner" and current_user.get("id") != learner_id:
            raise HTTPException(status_code=403, detail="Cannot access analytics for other learners")
        
        # Get progress summary from repository
        summary = await bkt_engine.repository.get_learner_progress_summary(learner_id)
        
        return {
            "learner_id": learner_id,
            "progress_summary": summary,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get learner analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learner analytics")


@router.get("/health")
async def health_check(
    bkt_engine: BKTEngine = Depends(get_bkt_engine)
):
    """
    Health check endpoint for BKT service monitoring.
    """
    try:
        # Check cache connectivity
        cache_stats = await bkt_engine.cache.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "cache_stats": cache_stats,
            "skills_loaded": len(bkt_engine._skill_parameters)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }
        )