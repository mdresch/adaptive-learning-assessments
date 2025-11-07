"""
FastAPI endpoints for adaptive challenge selection.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from src.models.adaptive_models import (
    AdaptationRequest, AdaptationResponse, DifficultyFeedback,
    ActivityResult, CompetencyLevel, ChallengeMetadata
)
from src.algorithms.adaptive_engine import AdaptiveEngine
from src.algorithms.bkt_engine import BKTEngine
from src.database.adaptive_repository import AdaptiveRepository
from src.auth.dependencies import get_current_learner, get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/adaptive", tags=["adaptive"])

# Initialize engines
adaptive_engine = AdaptiveEngine()
bkt_engine = BKTEngine()
adaptive_repository = AdaptiveRepository()


@router.post("/recommendations", response_model=AdaptationResponse)
async def get_adaptive_recommendations(
    request: AdaptationRequest,
    current_user: dict = Depends(get_current_learner)
):
    """
    Get personalized challenge recommendations for a learner.
    
    This endpoint evaluates the learner's current competency levels using BKT
    and recommends challenges that match their Zone of Proximal Development.
    """
    try:
        # Validate learner access
        if str(request.learner_id) != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot request recommendations for another learner"
            )
        
        # Get available challenges from database
        available_challenges = await adaptive_repository.get_available_challenges(
            competency_ids=[comp.competency_id for comp in request.current_competencies],
            challenge_types=request.challenge_types,
            max_difficulty=1.0,
            exclude_completed=True,
            learner_id=request.learner_id
        )
        
        if not available_challenges:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No suitable challenges found for current competency level"
            )
        
        # Generate adaptive recommendations
        response = adaptive_engine.generate_recommendations(request, available_challenges)
        
        # Store recommendation history
        await adaptive_repository.store_recommendation_history(
            learner_id=request.learner_id,
            recommendations=response.challenge_sequence.recommendations,
            context=response.adaptation_metadata
        )
        
        logger.info(f"Generated {len(response.challenge_sequence.recommendations)} recommendations for learner {request.learner_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )


@router.get("/competencies/{learner_id}", response_model=List[CompetencyLevel])
async def get_learner_competencies(
    learner_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get current competency levels for a learner.
    
    Returns BKT-based competency assessments including mastery probabilities
    and confidence levels.
    """
    try:
        # Check authorization (learner can view own, educators can view students)
        if not _can_access_learner_data(current_user, learner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access learner data"
            )
        
        competencies = await adaptive_repository.get_learner_competencies(learner_id)
        
        if not competencies:
            # Initialize default competencies for new learner
            competencies = await _initialize_default_competencies(learner_id)
        
        return competencies
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving competencies for learner {learner_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve competencies"
        )


@router.post("/activity-completion")
async def record_activity_completion(
    activity_result: ActivityResult,
    current_user: dict = Depends(get_current_learner)
):
    """
    Record completion of a learning activity and update competencies.
    
    This endpoint updates the learner's competency levels using BKT based on
    their performance on the completed activity.
    """
    try:
        # Validate learner access
        if str(activity_result.learner_id) != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot record activity for another learner"
            )
        
        # Get current competencies
        current_competencies = await adaptive_repository.get_learner_competencies(
            str(activity_result.learner_id)
        )
        
        if not current_competencies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner competencies not found"
            )
        
        # Update competencies using adaptive engine
        updated_competencies = adaptive_engine.adapt_after_activity(
            learner_id=str(activity_result.learner_id),
            activity_result=activity_result,
            current_competencies=current_competencies,
            difficulty_feedback=activity_result.difficulty_feedback
        )
        
        # Store updated competencies
        await adaptive_repository.update_learner_competencies(
            learner_id=str(activity_result.learner_id),
            competencies=updated_competencies
        )
        
        # Store activity log
        await adaptive_repository.store_activity_log(activity_result)
        
        logger.info(f"Updated competencies for learner {activity_result.learner_id} after activity {activity_result.challenge_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Activity recorded and competencies updated",
                "updated_competencies": len(updated_competencies),
                "mastery_changes": _calculate_mastery_changes(current_competencies, updated_competencies)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording activity completion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record activity completion"
        )


@router.post("/difficulty-feedback")
async def submit_difficulty_feedback(
    feedback: DifficultyFeedback,
    current_user: dict = Depends(get_current_learner)
):
    """
    Submit feedback on challenge difficulty.
    
    This feedback is used to calibrate the adaptive algorithm and improve
    future challenge recommendations.
    """
    try:
        # Validate learner access
        if str(feedback.learner_id) != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot submit feedback for another learner"
            )
        
        # Store feedback
        await adaptive_repository.store_difficulty_feedback(feedback)
        
        # Get current competencies for potential adjustment
        current_competencies = await adaptive_repository.get_learner_competencies(
            str(feedback.learner_id)
        )
        
        if current_competencies:
            # Apply feedback to competency estimates
            adjusted_competencies = adaptive_engine._apply_difficulty_feedback(
                current_competencies, feedback
            )
            
            # Update competencies if significant changes
            if _has_significant_changes(current_competencies, adjusted_competencies):
                await adaptive_repository.update_learner_competencies(
                    learner_id=str(feedback.learner_id),
                    competencies=adjusted_competencies
                )
        
        logger.info(f"Recorded difficulty feedback from learner {feedback.learner_id} for challenge {feedback.challenge_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Difficulty feedback recorded successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording difficulty feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record difficulty feedback"
        )


@router.get("/optimal-difficulty/{learner_id}/{challenge_id}")
async def get_optimal_difficulty(
    learner_id: str,
    challenge_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get optimal difficulty level for a specific challenge and learner.
    
    This endpoint calculates the ideal difficulty level based on the learner's
    current competency levels and the challenge requirements.
    """
    try:
        # Check authorization
        if not _can_access_learner_data(current_user, learner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access learner data"
            )
        
        # Get learner competencies
        competencies = await adaptive_repository.get_learner_competencies(learner_id)
        if not competencies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner competencies not found"
            )
        
        # Get challenge metadata
        challenge = await adaptive_repository.get_challenge_metadata(challenge_id)
        if not challenge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found"
            )
        
        # Calculate optimal difficulty
        optimal_difficulty = adaptive_engine.calculate_optimal_difficulty(
            competencies, challenge
        )
        
        # Get prediction for current difficulty
        relevant_competencies = [
            comp for comp in competencies 
            if comp.competency_id in challenge.competencies
        ]
        
        predictions = []
        for comp in relevant_competencies:
            success_prob, confidence = bkt_engine.predict_performance(
                comp, challenge.difficulty_level
            )
            predictions.append({
                "competency": comp.competency_name,
                "success_probability": success_prob,
                "confidence": confidence
            })
        
        return {
            "learner_id": learner_id,
            "challenge_id": challenge_id,
            "optimal_difficulty": optimal_difficulty,
            "current_difficulty": challenge.difficulty_level,
            "difficulty_adjustment": optimal_difficulty - challenge.difficulty_level,
            "performance_predictions": predictions,
            "recommendation": _get_difficulty_recommendation(optimal_difficulty, challenge.difficulty_level)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating optimal difficulty: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate optimal difficulty"
        )


@router.get("/insights/{learner_id}")
async def get_competency_insights(
    learner_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get insights about learner's competency profile.
    
    Provides analysis of strengths, weaknesses, and learning recommendations.
    """
    try:
        # Check authorization
        if not _can_access_learner_data(current_user, learner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access learner data"
            )
        
        # Get learner competencies
        competencies = await adaptive_repository.get_learner_competencies(learner_id)
        if not competencies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner competencies not found"
            )
        
        # Generate insights using BKT engine
        insights = bkt_engine.get_competency_insights(competencies)
        
        # Add learning path recommendations
        insights["learning_path_recommendations"] = await _generate_learning_path_recommendations(
            learner_id, competencies
        )
        
        # Add recent activity summary
        insights["recent_activity"] = await adaptive_repository.get_recent_activity_summary(
            learner_id, days=7
        )
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating competency insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate competency insights"
        )


# Helper functions

def _can_access_learner_data(current_user: dict, learner_id: str) -> bool:
    """Check if current user can access learner data."""
    user_role = current_user.get("role", "learner")
    user_id = current_user.get("id")
    
    # Learners can access their own data
    if user_role == "learner" and user_id == learner_id:
        return True
    
    # Educators and admins can access learner data
    if user_role in ["educator", "admin"]:
        return True
    
    return False


async def _initialize_default_competencies(learner_id: str) -> List[CompetencyLevel]:
    """Initialize default competencies for a new learner."""
    # Get all available competencies
    all_competencies = await adaptive_repository.get_all_competencies()
    
    # Initialize with default BKT parameters
    default_competencies = []
    for comp_meta in all_competencies:
        competency = bkt_engine.initialize_competency(
            competency_id=str(comp_meta["_id"]),
            competency_name=comp_meta["name"]
        )
        default_competencies.append(competency)
    
    # Store in database
    await adaptive_repository.update_learner_competencies(learner_id, default_competencies)
    
    return default_competencies


def _calculate_mastery_changes(
    old_competencies: List[CompetencyLevel],
    new_competencies: List[CompetencyLevel]
) -> List[dict]:
    """Calculate changes in mastery levels."""
    changes = []
    old_map = {comp.competency_id: comp for comp in old_competencies}
    
    for new_comp in new_competencies:
        if new_comp.competency_id in old_map:
            old_comp = old_map[new_comp.competency_id]
            mastery_change = new_comp.mastery_probability - old_comp.mastery_probability
            
            if abs(mastery_change) > 0.01:  # Only report significant changes
                changes.append({
                    "competency": new_comp.competency_name,
                    "old_mastery": old_comp.mastery_probability,
                    "new_mastery": new_comp.mastery_probability,
                    "change": mastery_change
                })
    
    return changes


def _has_significant_changes(
    old_competencies: List[CompetencyLevel],
    new_competencies: List[CompetencyLevel]
) -> bool:
    """Check if there are significant changes in competencies."""
    changes = _calculate_mastery_changes(old_competencies, new_competencies)
    return len(changes) > 0


def _get_difficulty_recommendation(optimal_difficulty: float, current_difficulty: float) -> str:
    """Get human-readable difficulty recommendation."""
    diff = optimal_difficulty - current_difficulty
    
    if abs(diff) < 0.1:
        return "Current difficulty is appropriate"
    elif diff > 0.2:
        return "Consider increasing difficulty significantly"
    elif diff > 0.1:
        return "Consider slightly increasing difficulty"
    elif diff < -0.2:
        return "Consider decreasing difficulty significantly"
    else:
        return "Consider slightly decreasing difficulty"


async def _generate_learning_path_recommendations(
    learner_id: str,
    competencies: List[CompetencyLevel]
) -> List[dict]:
    """Generate learning path recommendations based on competencies."""
    recommendations = []
    
    # Find competencies that need development
    developing_competencies = [
        comp for comp in competencies 
        if 0.2 <= comp.mastery_probability <= 0.7
    ]
    
    # Sort by mastery level (focus on those closest to mastery)
    developing_competencies.sort(key=lambda x: x.mastery_probability, reverse=True)
    
    for comp in developing_competencies[:5]:  # Top 5 recommendations
        recommendations.append({
            "competency": comp.competency_name,
            "current_mastery": comp.mastery_probability,
            "recommendation": f"Focus on {comp.competency_name} - you're making good progress!",
            "priority": "high" if comp.mastery_probability > 0.5 else "medium"
        })
    
    return recommendations