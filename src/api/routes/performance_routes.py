"""
Performance tracking API routes.

Provides endpoints for recording learner interactions and retrieving performance analytics.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from ...models.performance import (
    PerformanceRecord, ActivityResult, LearningSession,
    InteractionType, ActivityStatus
)
from ..main import get_app_state


router = APIRouter()


class RecordInteractionRequest(BaseModel):
    """Request model for recording learner interactions."""
    learner_id: str
    activity_id: str
    interaction_type: InteractionType
    session_id: str
    competency_id: Optional[str] = None
    question_id: Optional[str] = None
    response: Optional[Any] = None
    is_correct: Optional[bool] = None
    data: Optional[Dict[str, Any]] = None


class RecordActivityResultRequest(BaseModel):
    """Request model for recording activity results."""
    learner_id: str
    activity_id: str
    session_id: str
    status: ActivityStatus
    score: float
    max_possible_score: float
    start_time: datetime
    end_time: Optional[datetime] = None
    responses: Optional[List[Dict[str, Any]]] = None
    competency_updates: Optional[List[Dict[str, Any]]] = None


class StartSessionRequest(BaseModel):
    """Request model for starting learning sessions."""
    learner_id: str
    session_id: Optional[str] = None


@router.post("/interactions")
async def record_interaction(request: RecordInteractionRequest):
    """
    Record a learner interaction.
    
    Tracks detailed learner interactions including responses,
    timing, and context for adaptive learning analysis.
    """
    try:
        app_state = get_app_state()
        performance_tracker = app_state.get("performance_tracker")
        
        if not performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")
        
        record = await performance_tracker.record_interaction(
            learner_id=request.learner_id,
            activity_id=request.activity_id,
            interaction_type=request.interaction_type,
            session_id=request.session_id,
            competency_id=request.competency_id,
            question_id=request.question_id,
            response=request.response,
            is_correct=request.is_correct,
            data=request.data
        )
        
        return {
            "record_id": record.record_id,
            "learner_id": record.learner_id,
            "interaction_type": record.interaction_type,
            "timestamp": record.timestamp.isoformat(),
            "bkt_updated": record.bkt_state_after is not None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record interaction: {str(e)}")


@router.post("/activity-results")
async def record_activity_result(request: RecordActivityResultRequest):
    """
    Record the result of a completed activity.
    
    Captures comprehensive activity completion data including
    scores, responses, and performance metrics.
    """
    try:
        app_state = get_app_state()
        performance_tracker = app_state.get("performance_tracker")
        
        if not performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")
        
        result = await performance_tracker.record_activity_result(
            learner_id=request.learner_id,
            activity_id=request.activity_id,
            session_id=request.session_id,
            status=request.status,
            score=request.score,
            max_possible_score=request.max_possible_score,
            start_time=request.start_time,
            end_time=request.end_time,
            responses=request.responses,
            competency_updates=request.competency_updates
        )
        
        return {
            "result_id": result.result_id,
            "learner_id": result.learner_id,
            "activity_id": result.activity_id,
            "attempt_number": result.attempt_number,
            "status": result.status,
            "score": result.score,
            "percentage_score": result.percentage_score,
            "duration_minutes": result.duration_minutes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record activity result: {str(e)}")


@router.post("/sessions/start")
async def start_learning_session(request: StartSessionRequest):
    """
    Start a new learning session.
    
    Initializes session tracking for comprehensive learning
    analytics and adaptive content delivery.
    """
    try:
        app_state = get_app_state()
        performance_tracker = app_state.get("performance_tracker")
        
        if not performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")
        
        session = await performance_tracker.start_learning_session(
            learner_id=request.learner_id,
            session_id=request.session_id
        )
        
        return {
            "session_id": session.session_id,
            "learner_id": session.learner_id,
            "start_time": session.start_time.isoformat(),
            "status": "active"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start learning session: {str(e)}")


@router.post("/sessions/{session_id}/end")
async def end_learning_session(session_id: str):
    """
    End a learning session and calculate final metrics.
    
    Finalizes session tracking and computes comprehensive
    session analytics and learning outcomes.
    """
    try:
        app_state = get_app_state()
        performance_tracker = app_state.get("performance_tracker")
        
        if not performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")
        
        session = await performance_tracker.end_learning_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Learning session not found")
        
        return {
            "session_id": session.session_id,
            "learner_id": session.learner_id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration_minutes": session.duration_minutes,
            "activities_attempted": len(session.activities_attempted),
            "activities_completed": len(session.activities_completed),
            "total_score": session.total_score,
            "competencies_practiced": len(session.competencies_practiced)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end learning session: {str(e)}")


@router.get("/analytics/{learner_id}")
async def get_performance_analytics(
    learner_id: str,
    time_period_days: int = 30,
    competency_id: Optional[str] = None
):
    """
    Get comprehensive performance analytics for a learner.
    
    Returns detailed analytics including performance trends,
    learning patterns, and competency progress over time.
    """
    try:
        app_state = get_app_state()
        performance_tracker = app_state.get("performance_tracker")
        
        if not performance_tracker:
            raise HTTPException(status_code=503, detail="Performance tracker not available")
        
        analytics = await performance_tracker.get_performance_analytics(
            learner_id=learner_id,
            time_period_days=time_period_days,
            competency_id=competency_id
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")


@router.get("/sessions/{learner_id}")
async def get_learning_sessions(
    learner_id: str,
    limit: int = 10,
    offset: int = 0
):
    """
    Get learning sessions for a learner.
    
    Returns paginated list of learning sessions with
    summary metrics and activity information.
    """
    try:
        # This would be implemented with actual database queries
        # For now, return a placeholder response
        
        return {
            "learner_id": learner_id,
            "sessions": [],
            "total_sessions": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning sessions: {str(e)}")


@router.get("/interactions/{learner_id}")
async def get_performance_records(
    learner_id: str,
    activity_id: Optional[str] = None,
    session_id: Optional[str] = None,
    interaction_type: Optional[InteractionType] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get performance records for a learner.
    
    Returns detailed interaction history with filtering
    and pagination support.
    """
    try:
        # This would be implemented with actual database queries
        # For now, return a placeholder response
        
        return {
            "learner_id": learner_id,
            "records": [],
            "total_records": 0,
            "filters": {
                "activity_id": activity_id,
                "session_id": session_id,
                "interaction_type": interaction_type
            },
            "limit": limit,
            "offset": offset,
            "has_more": False
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance records: {str(e)}")