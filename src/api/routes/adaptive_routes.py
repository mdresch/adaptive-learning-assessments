"""
Adaptive learning API routes.

Provides endpoints for adaptive content selection and BKT operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

from ...core.adaptive_selector import SelectionStrategy
from ..main import get_app_state


router = APIRouter()


class ActivityRecommendationRequest(BaseModel):
    """Request model for activity recommendations."""
    learner_id: str
    num_activities: int = 3
    strategy: SelectionStrategy = SelectionStrategy.MASTERY_BASED
    session_duration_minutes: int = 30


class BKTUpdateRequest(BaseModel):
    """Request model for BKT updates."""
    learner_id: str
    competency_id: str
    is_correct: bool
    activity_id: str
    session_id: str
    question_id: Optional[str] = None
    response_time_seconds: Optional[float] = None
    difficulty_level: Optional[str] = None


@router.post("/recommendations")
async def get_activity_recommendations(request: ActivityRecommendationRequest):
    """
    Get adaptive activity recommendations for a learner.
    
    Returns personalized activity recommendations based on the learner's
    current competency levels and learning preferences.
    """
    try:
        app_state = get_app_state()
        adaptive_selector = app_state.get("adaptive_selector")
        
        if not adaptive_selector:
            raise HTTPException(status_code=503, detail="Adaptive selector not available")
        
        recommendations = await adaptive_selector.select_next_activities(
            learner_id=request.learner_id,
            num_activities=request.num_activities,
            strategy=request.strategy,
            session_duration_minutes=request.session_duration_minutes
        )
        
        return {
            "learner_id": request.learner_id,
            "strategy": request.strategy,
            "recommendations": recommendations,
            "total_estimated_duration": sum(
                rec["activity"].estimated_duration_minutes for rec in recommendations
            )
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/bkt/update")
async def update_bkt_mastery(request: BKTUpdateRequest):
    """
    Update learner mastery using BKT based on performance evidence.
    
    Updates the Bayesian Knowledge Tracing model with new evidence
    from learner interactions.
    """
    try:
        app_state = get_app_state()
        bkt_engine = app_state.get("bkt_engine")
        
        if not bkt_engine:
            raise HTTPException(status_code=503, detail="BKT engine not available")
        
        update_result = await bkt_engine.update_mastery(
            learner_id=request.learner_id,
            competency_id=request.competency_id,
            is_correct=request.is_correct,
            activity_id=request.activity_id,
            session_id=request.session_id,
            question_id=request.question_id,
            response_time_seconds=request.response_time_seconds,
            difficulty_level=request.difficulty_level
        )
        
        return {
            "update_id": update_result.update_id,
            "learner_id": update_result.learner_id,
            "competency_id": update_result.competency_id,
            "prior_mastery": update_result.prior_mastery,
            "posterior_mastery": update_result.posterior_mastery,
            "mastery_change": update_result.mastery_change,
            "timestamp": update_result.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update BKT: {str(e)}")


@router.get("/bkt/state/{learner_id}/{competency_id}")
async def get_bkt_state(learner_id: str, competency_id: str):
    """
    Get current BKT state for a learner-competency pair.
    
    Returns the current mastery probability and learning state
    for a specific competency.
    """
    try:
        app_state = get_app_state()
        bkt_engine = app_state.get("bkt_engine")
        
        if not bkt_engine:
            raise HTTPException(status_code=503, detail="BKT engine not available")
        
        bkt_state = await bkt_engine.get_bkt_state(learner_id, competency_id)
        
        return {
            "learner_id": bkt_state.learner_id,
            "competency_id": bkt_state.competency_id,
            "mastery_probability": bkt_state.mastery_probability,
            "evidence_count": bkt_state.evidence_count,
            "total_attempts": bkt_state.total_attempts,
            "correct_attempts": bkt_state.correct_attempts,
            "learning_velocity": bkt_state.learning_velocity,
            "confidence_interval": bkt_state.confidence_interval,
            "last_update": bkt_state.last_update.isoformat() if bkt_state.last_update else None,
            "mastery_achieved_at": bkt_state.mastery_achieved_at.isoformat() if bkt_state.mastery_achieved_at else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get BKT state: {str(e)}")


@router.get("/personalization/{learner_id}")
async def get_personalization_settings(learner_id: str):
    """
    Get personalization settings for adaptive content delivery.
    
    Returns learner-specific settings that influence content selection
    and presentation.
    """
    try:
        app_state = get_app_state()
        learner_profiler = app_state.get("learner_profiler")
        
        if not learner_profiler:
            raise HTTPException(status_code=503, detail="Learner profiler not available")
        
        settings = await learner_profiler.get_personalization_settings(learner_id)
        
        return settings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personalization settings: {str(e)}")


@router.post("/predict-performance")
async def predict_performance(
    learner_id: str,
    competency_id: str,
    difficulty_adjustment: float = 1.0
):
    """
    Predict learner performance for a competency.
    
    Uses BKT model to predict the probability of correct response
    given current mastery level.
    """
    try:
        app_state = get_app_state()
        bkt_engine = app_state.get("bkt_engine")
        
        if not bkt_engine:
            raise HTTPException(status_code=503, detail="BKT engine not available")
        
        # Get current state and parameters
        bkt_state = await bkt_engine.get_bkt_state(learner_id, competency_id)
        parameters = await bkt_engine.get_bkt_parameters(competency_id)
        
        # Predict performance
        prediction = bkt_engine.predict_performance(
            bkt_state.mastery_probability,
            parameters,
            difficulty_adjustment
        )
        
        return {
            "learner_id": learner_id,
            "competency_id": competency_id,
            "current_mastery": bkt_state.mastery_probability,
            "difficulty_adjustment": difficulty_adjustment,
            "prediction": prediction
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict performance: {str(e)}")