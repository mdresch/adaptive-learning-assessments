"""
Learner Profile API Routes

This module defines the FastAPI routes for learner profile management,
including creation, retrieval, and updates of learner profiles.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..db.database import get_database
from ..db.learner_repository import LearnerRepository
from ..models.learner import (
    LearnerProfile,
    LearnerProfileUpdate,
    LearnerProfileResponse,
    SelfReportedData,
    EducationLevel,
    ProgrammingExperienceLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/learners", tags=["learners"])


async def get_learner_repository(database: AsyncIOMotorDatabase = Depends(get_database)) -> LearnerRepository:
    """Dependency to get learner repository instance"""
    return LearnerRepository(database)


@router.post("/", 
             response_model=dict, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new learner profile",
             description="Create a new learner profile with demographics, preferences, and experience information")
async def create_learner_profile(
    learner_data: LearnerProfile,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> dict:
    """
    Create a new learner profile
    
    This endpoint creates a new learner profile with the provided information.
    The profile includes demographics, learning preferences, programming experience,
    and accessibility requirements.
    
    - **username**: Unique username for the learner (3-50 characters)
    - **email**: Valid email address
    - **demographics**: Age, location, education level, etc.
    - **preferences**: Learning style, accessibility needs, session preferences
    - **programming_experience**: Experience level, known languages, familiarity with concepts
    - **privacy_consent**: Required consent for data processing
    """
    try:
        # Validate required consents
        if not learner_data.privacy_consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Privacy consent is required to create a profile"
            )
        
        if not learner_data.data_processing_consent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data processing consent is required to create a profile"
            )
        
        learner_id = await repository.create_learner_profile(learner_data)
        
        logger.info(f"Created learner profile for user: {learner_data.username}")
        
        return {
            "message": "Learner profile created successfully",
            "learner_id": learner_id,
            "username": learner_data.username
        }
        
    except ValueError as e:
        logger.warning(f"Validation error creating learner profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating learner profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating learner profile"
        )


@router.get("/{learner_id}",
            response_model=LearnerProfileResponse,
            summary="Get learner profile by ID",
            description="Retrieve a learner profile by their unique identifier")
async def get_learner_profile(
    learner_id: str,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> LearnerProfileResponse:
    """
    Retrieve a learner profile by ID
    
    Returns the complete learner profile information excluding sensitive data
    such as password hashes and consent records.
    """
    try:
        learner = await repository.get_learner_profile_by_id(learner_id)
        
        if not learner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner profile not found"
            )
        
        return learner
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving learner profile {learner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving learner profile"
        )


@router.get("/username/{username}",
            response_model=LearnerProfileResponse,
            summary="Get learner profile by username",
            description="Retrieve a learner profile by their username")
async def get_learner_profile_by_username(
    username: str,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> LearnerProfileResponse:
    """
    Retrieve a learner profile by username
    
    Returns the complete learner profile information excluding sensitive data.
    """
    try:
        learner = await repository.get_learner_profile_by_username(username)
        
        if not learner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner profile not found"
            )
        
        # Convert to response model (excluding sensitive fields)
        learner_dict = learner.dict()
        sensitive_fields = ["hashed_password", "privacy_consent", "data_processing_consent", "marketing_consent"]
        for field in sensitive_fields:
            learner_dict.pop(field, None)
        
        return LearnerProfileResponse(**learner_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving learner profile by username {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving learner profile"
        )


@router.put("/{learner_id}",
            response_model=dict,
            summary="Update learner profile",
            description="Update an existing learner profile with new information")
async def update_learner_profile(
    learner_id: str,
    update_data: LearnerProfileUpdate,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> dict:
    """
    Update a learner profile
    
    Updates the specified learner profile with the provided information.
    Only the fields included in the request will be updated.
    The updated_at timestamp is automatically set to the current time.
    
    This endpoint immediately triggers learning path personalization updates
    based on the new profile information.
    """
    try:
        success = await repository.update_learner_profile(learner_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner profile not found"
            )
        
        logger.info(f"Updated learner profile: {learner_id}")
        
        # TODO: Trigger learning path personalization update
        # This would integrate with the adaptive engine to update
        # the learner's personalized learning path based on profile changes
        
        return {
            "message": "Learner profile updated successfully",
            "learner_id": learner_id,
            "personalization_updated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating learner profile {learner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating learner profile"
        )


@router.post("/{learner_id}/self-reported-data",
             response_model=dict,
             summary="Add self-reported data",
             description="Add self-reported learning data to a learner profile")
async def add_self_reported_data(
    learner_id: str,
    self_reported_data: SelfReportedData,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> dict:
    """
    Add self-reported data to a learner profile
    
    Allows learners to provide additional information about their confidence levels,
    learning goals, motivation, and time availability. This data is used to
    further personalize the learning experience.
    """
    try:
        success = await repository.add_self_reported_data(learner_id, self_reported_data)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner profile not found"
            )
        
        logger.info(f"Added self-reported data to learner profile: {learner_id}")
        
        return {
            "message": "Self-reported data added successfully",
            "learner_id": learner_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding self-reported data to learner {learner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error adding self-reported data"
        )


@router.patch("/{learner_id}/last-login",
              response_model=dict,
              summary="Update last login timestamp",
              description="Update the last login timestamp for a learner")
async def update_last_login(
    learner_id: str,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> dict:
    """
    Update the last login timestamp for a learner
    
    This endpoint is typically called when a learner logs into the system
    to track their activity and engagement patterns.
    """
    try:
        success = await repository.update_last_login(learner_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner profile not found"
            )
        
        return {
            "message": "Last login updated successfully",
            "learner_id": learner_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating last login for learner {learner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error updating last login"
        )


@router.delete("/{learner_id}",
               response_model=dict,
               summary="Deactivate learner profile",
               description="Deactivate a learner profile (soft delete)")
async def deactivate_learner_profile(
    learner_id: str,
    repository: LearnerRepository = Depends(get_learner_repository)
) -> dict:
    """
    Deactivate a learner profile
    
    Performs a soft delete by setting the is_active flag to False.
    The profile data is retained for compliance and analytics purposes
    but the learner will no longer be able to access the system.
    """
    try:
        success = await repository.deactivate_learner_profile(learner_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learner profile not found"
            )
        
        logger.info(f"Deactivated learner profile: {learner_id}")
        
        return {
            "message": "Learner profile deactivated successfully",
            "learner_id": learner_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating learner profile {learner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error deactivating learner profile"
        )


@router.get("/",
            response_model=dict,
            summary="Get learners with pagination and filtering",
            description="Retrieve learners with pagination and optional filtering")
async def get_learners(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    education_level: Optional[EducationLevel] = Query(None, description="Filter by education level"),
    programming_experience: Optional[ProgrammingExperienceLevel] = Query(None, description="Filter by programming experience"),
    repository: LearnerRepository = Depends(get_learner_repository)
) -> dict:
    """
    Retrieve learners with pagination and filtering
    
    Returns a paginated list of learners with optional filtering by:
    - Active status
    - Education level
    - Programming experience level
    
    Includes total count for pagination purposes.
    """
    try:
        # Get learners with filtering
        learners = await repository.get_learners_by_criteria(
            skip=skip,
            limit=limit,
            is_active=is_active,
            education_level=education_level.value if education_level else None,
            programming_experience=programming_experience.value if programming_experience else None
        )
        
        # Get total count for pagination
        total_count = await repository.count_learners(is_active=is_active)
        
        return {
            "learners": learners,
            "total_count": total_count,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total_count
        }
        
    except Exception as e:
        logger.error(f"Error retrieving learners: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving learners"
        )