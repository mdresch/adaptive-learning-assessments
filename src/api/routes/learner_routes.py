"""
Learner profile API routes.

Provides endpoints for learner profile management and analytics.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from ...models.learner_profile import (
    LearnerProfile, LearnerProfileUpdate, LearnerPreferences, 
    LearnerDemographics, ExperienceLevel
)
from ..main import get_app_state


router = APIRouter()


class CreateLearnerRequest(BaseModel):
    """Request model for creating a learner profile."""
    learner_id: str
    username: str
    email: str
    demographics: Optional[LearnerDemographics] = None
    preferences: Optional[LearnerPreferences] = None
    programming_experience: ExperienceLevel = ExperienceLevel.BEGINNER
    learning_goals: Optional[List[str]] = None


@router.post("/", response_model=LearnerProfile)
async def create_learner_profile(request: CreateLearnerRequest):
    """
    Create a new learner profile.
    
    Creates a comprehensive learner profile with demographics,
    preferences, and learning objectives.
    """
    try:
        app_state = get_app_state()
        learner_profiler = app_state.get("learner_profiler")
        
        if not learner_profiler:
            raise HTTPException(status_code=503, detail="Learner profiler not available")
        
        profile = await learner_profiler.create_profile(
            learner_id=request.learner_id,
            username=request.username,
            email=request.email,
            demographics=request.demographics,
            preferences=request.preferences,
            programming_experience=request.programming_experience,
            learning_goals=request.learning_goals
        )
        
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create learner profile: {str(e)}")


@router.get("/{learner_id}", response_model=LearnerProfile)
async def get_learner_profile(learner_id: str):
    """
    Get a learner profile by ID.
    
    Returns the complete learner profile including demographics,
    preferences, and learning history.
    """
    try:
        app_state = get_app_state()
        learner_profiler = app_state.get("learner_profiler")
        
        if not learner_profiler:
            raise HTTPException(status_code=503, detail="Learner profiler not available")
        
        profile = await learner_profiler.get_profile(learner_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Learner profile not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learner profile: {str(e)}")


@router.put("/{learner_id}", response_model=LearnerProfile)
async def update_learner_profile(learner_id: str, updates: LearnerProfileUpdate):
    """
    Update a learner profile.
    
    Updates specific fields of a learner profile while preserving
    existing data for unchanged fields.
    """
    try:
        app_state = get_app_state()
        learner_profiler = app_state.get("learner_profiler")
        
        if not learner_profiler:
            raise HTTPException(status_code=503, detail="Learner profiler not available")
        
        updated_profile = await learner_profiler.update_profile(learner_id, updates)
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail="Learner profile not found")
        
        return updated_profile
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update learner profile: {str(e)}")


@router.get("/{learner_id}/analytics")
async def get_learner_analytics(
    learner_id: str,
    time_period_days: int = 30,
    competency_id: Optional[str] = None
):
    """
    Get comprehensive learning analytics for a learner.
    
    Returns detailed analytics including performance trends,
    learning patterns, and competency progress.
    """
    try:
        app_state = get_app_state()
        learner_profiler = app_state.get("learner_profiler")
        performance_tracker = app_state.get("performance_tracker")
        
        if not learner_profiler or not performance_tracker:
            raise HTTPException(status_code=503, detail="Analytics services not available")
        
        # Get performance analytics
        analytics = await performance_tracker.get_performance_analytics(
            learner_id=learner_id,
            time_period_days=time_period_days,
            competency_id=competency_id
        )
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learner analytics: {str(e)}")


@router.get("/{learner_id}/learning-patterns")
async def analyze_learning_patterns(learner_id: str):
    """
    Analyze learner's learning patterns and provide insights.
    
    Returns detailed analysis of learning style, engagement patterns,
    and personalized recommendations.
    """
    try:
        app_state = get_app_state()
        learner_profiler = app_state.get("learner_profiler")
        performance_tracker = app_state.get("performance_tracker")
        
        if not learner_profiler or not performance_tracker:
            raise HTTPException(status_code=503, detail="Analysis services not available")
        
        # Get performance data (this would be implemented with actual database queries)
        performance_history = []  # Would fetch from database
        activity_results = []     # Would fetch from database
        
        # Analyze patterns
        analysis = await learner_profiler.analyze_learning_patterns(
            learner_id=learner_id,
            performance_history=performance_history,
            activity_results=activity_results
        )
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze learning patterns: {str(e)}")


@router.delete("/{learner_id}")
async def delete_learner_profile(learner_id: str):
    """
    Delete a learner profile and all associated data.
    
    WARNING: This permanently removes all learner data including
    performance history and competency progress.
    """
    try:
        # This would be implemented with actual database operations
        # For now, return a placeholder response
        
        return {
            "message": f"Learner profile {learner_id} deletion requested",
            "status": "pending",
            "note": "Full implementation requires database integration"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete learner profile: {str(e)}")