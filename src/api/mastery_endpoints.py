"""
FastAPI endpoints for mastery tracking system.

This module provides REST API endpoints for logging learner interactions,
retrieving progress reports, and managing mastery data.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import time

from ..models.mastery import (
    InteractionLogRequest,
    LearnerInteraction,
    MasteryLevel,
    ProgressReport,
    MasteryUpdateResponse,
    MicroCompetency,
    ActivityType,
    DifficultyLevel
)
from ..core.bkt_engine import BKTEngine
from ..db.mastery_repository import MasteryRepository
from ..utils.dependencies import get_mastery_repository, get_bkt_engine

logger = logging.getLogger(__name__)

# Create router for mastery tracking endpoints
router = APIRouter(prefix="/api/v1/mastery", tags=["mastery"])


@router.post("/interactions", response_model=MasteryUpdateResponse)
async def log_interaction(
    interaction_request: InteractionLogRequest,
    background_tasks: BackgroundTasks,
    repository: MasteryRepository = Depends(get_mastery_repository),
    bkt_engine: BKTEngine = Depends(get_bkt_engine)
):
    """
    Log a learner interaction and update mastery levels.
    
    This endpoint logs a learner's interaction with an activity and triggers
    real-time updates to their mastery levels using the BKT algorithm.
    """
    start_time = time.time()
    
    try:
        # Convert request to interaction model
        interaction = LearnerInteraction(
            learner_id=interaction_request.learner_id,
            activity_id=interaction_request.activity_id,
            activity_type=interaction_request.activity_type,
            interaction_type=interaction_request.interaction_type,
            competency_ids=interaction_request.competency_ids,
            score=interaction_request.score,
            is_correct=interaction_request.is_correct,
            attempts=interaction_request.attempts,
            time_spent=interaction_request.time_spent,
            hints_used=interaction_request.hints_used,
            difficulty_level=interaction_request.difficulty_level,
            session_id=interaction_request.session_id,
            metadata=interaction_request.metadata,
            started_at=interaction_request.started_at,
            completed_at=interaction_request.completed_at or datetime.utcnow()
        )
        
        # Save the interaction
        interaction_id = await repository.save_interaction(interaction)
        logger.info(f"Logged interaction {interaction_id} for learner {interaction.learner_id}")
        
        # Update mastery levels for all competencies in the interaction
        updated_competencies = []
        new_mastery_levels = {}
        newly_mastered = []
        
        for competency_id in interaction.competency_ids:
            # Get or create mastery level
            mastery_level = await repository.get_mastery_level(
                interaction.learner_id, 
                competency_id
            )
            
            if mastery_level is None:
                mastery_level = await repository.create_initial_mastery_level(
                    interaction.learner_id, 
                    competency_id
                )
            
            # Update mastery using BKT
            was_mastered = mastery_level.is_mastered
            updated_mastery = bkt_engine.update_mastery(mastery_level, interaction)
            
            # Save updated mastery level
            await repository.save_mastery_level(updated_mastery)
            
            # Track changes
            updated_competencies.append(competency_id)
            new_mastery_levels[competency_id] = updated_mastery.current_mastery
            
            if not was_mastered and updated_mastery.is_mastered:
                newly_mastered.append(competency_id)
        
        processing_time = time.time() - start_time
        
        # Schedule background analytics update if needed
        background_tasks.add_task(
            update_analytics_cache,
            repository,
            interaction.learner_id,
            interaction.competency_ids
        )
        
        response = MasteryUpdateResponse(
            learner_id=interaction.learner_id,
            updated_competencies=updated_competencies,
            new_mastery_levels=new_mastery_levels,
            newly_mastered=newly_mastered,
            processing_time=processing_time
        )
        
        logger.info(
            f"Updated mastery for learner {interaction.learner_id}, "
            f"competencies: {updated_competencies}, "
            f"processing time: {processing_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error logging interaction: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to log interaction: {str(e)}")


@router.get("/progress/{learner_id}", response_model=ProgressReport)
async def get_learner_progress(
    learner_id: str,
    include_recent_interactions: bool = Query(True, description="Include recent interactions in report"),
    recent_days: int = Query(7, ge=1, le=30, description="Number of recent days for interactions"),
    repository: MasteryRepository = Depends(get_mastery_repository)
):
    """
    Get detailed progress report for a learner.
    
    Returns comprehensive mastery information including current levels,
    performance trends, and recommendations.
    """
    try:
        # Get all mastery levels for the learner
        mastery_levels = await repository.get_mastery_levels_by_learner(learner_id)
        
        if not mastery_levels:
            raise HTTPException(
                status_code=404, 
                detail=f"No mastery data found for learner {learner_id}"
            )
        
        # Calculate overall statistics
        total_competencies = len(mastery_levels)
        mastered_competencies = sum(1 for ml in mastery_levels if ml.is_mastered)
        mastery_percentage = (mastered_competencies / total_competencies * 100) if total_competencies > 0 else 0
        
        # Get recent interactions if requested
        recent_interactions = []
        if include_recent_interactions:
            since = datetime.utcnow() - timedelta(days=recent_days)
            recent_interactions = await repository.get_interactions_by_learner(
                learner_id, 
                limit=50, 
                since=since
            )
        
        # Generate performance trend data
        performance_trend = await generate_performance_trend(
            repository, 
            learner_id, 
            days=30
        )
        
        # Generate recommendations
        recommended_activities, focus_areas = await generate_recommendations(
            repository,
            mastery_levels
        )
        
        progress_report = ProgressReport(
            learner_id=learner_id,
            total_competencies=total_competencies,
            mastered_competencies=mastered_competencies,
            mastery_percentage=mastery_percentage,
            competency_mastery=mastery_levels,
            recent_interactions=recent_interactions,
            performance_trend=performance_trend,
            recommended_activities=recommended_activities,
            focus_areas=focus_areas
        )
        
        logger.info(f"Generated progress report for learner {learner_id}")
        return progress_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating progress report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate progress report: {str(e)}")


@router.get("/mastery/{learner_id}/{competency_id}", response_model=MasteryLevel)
async def get_mastery_level(
    learner_id: str,
    competency_id: str,
    repository: MasteryRepository = Depends(get_mastery_repository)
):
    """Get mastery level for a specific learner and competency."""
    try:
        mastery_level = await repository.get_mastery_level(learner_id, competency_id)
        
        if mastery_level is None:
            raise HTTPException(
                status_code=404,
                detail=f"No mastery data found for learner {learner_id} and competency {competency_id}"
            )
        
        return mastery_level
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mastery level: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get mastery level: {str(e)}")


@router.get("/interactions/{learner_id}")
async def get_learner_interactions(
    learner_id: str,
    limit: Optional[int] = Query(50, ge=1, le=500, description="Maximum number of interactions to return"),
    activity_type: Optional[ActivityType] = Query(None, description="Filter by activity type"),
    since: Optional[datetime] = Query(None, description="Only return interactions after this timestamp"),
    repository: MasteryRepository = Depends(get_mastery_repository)
):
    """Get interactions for a specific learner with optional filtering."""
    try:
        interactions = await repository.get_interactions_by_learner(
            learner_id, 
            limit=limit, 
            since=since
        )
        
        # Filter by activity type if specified
        if activity_type:
            interactions = [i for i in interactions if i.activity_type == activity_type]
        
        return {
            "learner_id": learner_id,
            "total_interactions": len(interactions),
            "interactions": interactions
        }
        
    except Exception as e:
        logger.error(f"Error getting learner interactions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get interactions: {str(e)}")


@router.get("/competencies/{competency_id}/stats")
async def get_competency_stats(
    competency_id: str,
    repository: MasteryRepository = Depends(get_mastery_repository)
):
    """Get performance statistics for a specific competency across all learners."""
    try:
        stats = await repository.get_competency_performance_stats(competency_id)
        
        # Get competency details
        competency = await repository.get_competency(competency_id)
        
        return {
            "competency_id": competency_id,
            "competency_name": competency.name if competency else "Unknown",
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting competency stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get competency stats: {str(e)}")


@router.get("/analytics/dashboard/{learner_id}")
async def get_learner_dashboard(
    learner_id: str,
    repository: MasteryRepository = Depends(get_mastery_repository),
    bkt_engine: BKTEngine = Depends(get_bkt_engine)
):
    """Get dashboard data for a learner including analytics and insights."""
    try:
        # Get basic progress summary
        summary = await repository.get_learner_progress_summary(learner_id)
        
        # Get mastery levels with additional analytics
        mastery_levels = await repository.get_mastery_levels_by_learner(learner_id)
        
        # Calculate additional insights
        insights = []
        for mastery_level in mastery_levels:
            # Calculate confidence interval
            confidence_interval = bkt_engine.calculate_confidence_interval(mastery_level)
            
            # Calculate learning velocity
            velocity = bkt_engine.get_learning_velocity(mastery_level)
            
            # Get practice recommendation
            practice_intensity = bkt_engine.recommend_practice_intensity(mastery_level)
            
            insights.append({
                "competency_id": mastery_level.competency_id,
                "current_mastery": mastery_level.current_mastery,
                "confidence_interval": confidence_interval,
                "learning_velocity": velocity,
                "practice_recommendation": practice_intensity,
                "is_mastered": mastery_level.is_mastered
            })
        
        # Get recent performance trend
        recent_interactions = await repository.get_interactions_by_learner(
            learner_id, 
            limit=20
        )
        
        return {
            "learner_id": learner_id,
            "summary": summary,
            "insights": insights,
            "recent_activity": len(recent_interactions),
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


# Helper functions

async def update_analytics_cache(
    repository: MasteryRepository,
    learner_id: str,
    competency_ids: List[str]
):
    """Background task to update analytics cache."""
    try:
        # This could update cached analytics, trigger notifications, etc.
        logger.info(f"Updating analytics cache for learner {learner_id}")
        
        # Example: Update learner progress summary cache
        summary = await repository.get_learner_progress_summary(learner_id)
        
        # Example: Update competency performance stats cache
        for competency_id in competency_ids:
            stats = await repository.get_competency_performance_stats(competency_id)
        
        logger.info(f"Analytics cache updated for learner {learner_id}")
        
    except Exception as e:
        logger.error(f"Error updating analytics cache: {str(e)}")


async def generate_performance_trend(
    repository: MasteryRepository,
    learner_id: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """Generate performance trend data for a learner."""
    try:
        since = datetime.utcnow() - timedelta(days=days)
        interactions = await repository.get_interactions_by_learner(
            learner_id, 
            since=since
        )
        
        # Group interactions by day and calculate daily performance
        daily_performance = {}
        for interaction in interactions:
            day = interaction.completed_at.date()
            if day not in daily_performance:
                daily_performance[day] = {"total": 0, "correct": 0, "scores": []}
            
            daily_performance[day]["total"] += 1
            if interaction.is_correct:
                daily_performance[day]["correct"] += 1
            if interaction.score is not None:
                daily_performance[day]["scores"].append(interaction.score)
        
        # Convert to trend data
        trend_data = []
        for day, data in sorted(daily_performance.items()):
            accuracy = data["correct"] / data["total"] if data["total"] > 0 else 0
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            
            trend_data.append({
                "date": day.isoformat(),
                "interactions": data["total"],
                "accuracy": accuracy,
                "average_score": avg_score
            })
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error generating performance trend: {str(e)}")
        return []


async def generate_recommendations(
    repository: MasteryRepository,
    mastery_levels: List[MasteryLevel]
) -> tuple[List[str], List[str]]:
    """Generate activity recommendations and focus areas."""
    try:
        recommended_activities = []
        focus_areas = []
        
        # Sort by mastery level to identify areas needing attention
        sorted_mastery = sorted(mastery_levels, key=lambda x: x.current_mastery)
        
        # Focus areas: competencies with low mastery
        for mastery_level in sorted_mastery[:5]:  # Top 5 lowest
            if mastery_level.current_mastery < 0.6:
                focus_areas.append(mastery_level.competency_id)
        
        # Recommended activities: based on current mastery levels
        # This would typically integrate with an activity recommendation system
        for mastery_level in mastery_levels:
            if 0.3 <= mastery_level.current_mastery <= 0.7:
                # Competencies in the learning zone
                recommended_activities.append(f"practice_{mastery_level.competency_id}")
        
        return recommended_activities[:10], focus_areas  # Limit recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return [], []