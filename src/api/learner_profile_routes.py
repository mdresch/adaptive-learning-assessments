"""
Learner Profile API Routes

This module defines the FastAPI routes for learner profile management
including CRUD operations, authentication, and profile updates.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm

from ..db.database import get_learner_collection
from ..db.learner_repository import LearnerRepository
from ..models.learner_profile import (
    LearnerProfile,
    LearnerProfileCreate,
    LearnerProfileUpdate,
    LearnerProfileResponse
)
from ..api.auth import (
    get_current_active_user,
    authenticate_user,
    create_user_token,
    Token
)


router = APIRouter(prefix="/api/v1/learners", tags=["learner-profiles"])


@router.post("/register", response_model=LearnerProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_learner(profile_data: LearnerProfileCreate):
    """
    Register a new learner profile
    
    Creates a new learner account with the provided profile information.
    The password is securely hashed before storage.
    """
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    
    try:
        # Create the learner profile
        created_profile = await repository.create_learner_profile(profile_data)
        
        # Convert to response model
        return LearnerProfileResponse(
            id=str(created_profile.id),
            email=created_profile.email,
            first_name=created_profile.first_name,
            last_name=created_profile.last_name,
            username=created_profile.username,
            demographics=created_profile.demographics,
            learning_preferences=created_profile.learning_preferences,
            programming_experience=created_profile.programming_experience,
            accessibility_settings=created_profile.accessibility_settings,
            goals=created_profile.goals,
            interests=created_profile.interests,
            is_active=created_profile.is_active,
            created_at=created_profile.created_at,
            updated_at=created_profile.updated_at,
            last_login=created_profile.last_login,
            profile_completion_percentage=created_profile.profile_completion_percentage
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create learner profile"
        )


@router.post("/login", response_model=Token)
async def login_learner(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate learner and return access token
    
    Validates learner credentials and returns a JWT token for authenticated requests.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    await repository.update_last_login(str(user.id))
    
    return await create_user_token(user)


@router.get("/me", response_model=LearnerProfileResponse)
async def get_current_learner_profile(
    current_user: LearnerProfile = Depends(get_current_active_user)
):
    """
    Get current learner's profile
    
    Returns the complete profile information for the authenticated learner.
    """
    return LearnerProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        username=current_user.username,
        demographics=current_user.demographics,
        learning_preferences=current_user.learning_preferences,
        programming_experience=current_user.programming_experience,
        accessibility_settings=current_user.accessibility_settings,
        goals=current_user.goals,
        interests=current_user.interests,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
        profile_completion_percentage=current_user.profile_completion_percentage
    )


@router.put("/me", response_model=LearnerProfileResponse)
async def update_current_learner_profile(
    update_data: LearnerProfileUpdate,
    current_user: LearnerProfile = Depends(get_current_active_user)
):
    """
    Update current learner's profile
    
    Updates the authenticated learner's profile with the provided information.
    Changes immediately influence learning path personalization.
    """
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    
    updated_profile = await repository.update_learner_profile(
        str(current_user.id), update_data
    )
    
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found or could not be updated"
        )
    
    return LearnerProfileResponse(
        id=str(updated_profile.id),
        email=updated_profile.email,
        first_name=updated_profile.first_name,
        last_name=updated_profile.last_name,
        username=updated_profile.username,
        demographics=updated_profile.demographics,
        learning_preferences=updated_profile.learning_preferences,
        programming_experience=updated_profile.programming_experience,
        accessibility_settings=updated_profile.accessibility_settings,
        goals=updated_profile.goals,
        interests=updated_profile.interests,
        is_active=updated_profile.is_active,
        created_at=updated_profile.created_at,
        updated_at=updated_profile.updated_at,
        last_login=updated_profile.last_login,
        profile_completion_percentage=updated_profile.profile_completion_percentage
    )


@router.get("/{learner_id}", response_model=LearnerProfileResponse)
async def get_learner_profile(
    learner_id: str,
    current_user: LearnerProfile = Depends(get_current_active_user)
):
    """
    Get learner profile by ID
    
    Returns profile information for the specified learner.
    Currently restricted to the learner's own profile for privacy.
    """
    # For now, only allow users to access their own profile
    if str(current_user.id) != learner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Can only access your own profile"
        )
    
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    
    profile = await repository.get_learner_by_id(learner_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found"
        )
    
    return LearnerProfileResponse(
        id=str(profile.id),
        email=profile.email,
        first_name=profile.first_name,
        last_name=profile.last_name,
        username=profile.username,
        demographics=profile.demographics,
        learning_preferences=profile.learning_preferences,
        programming_experience=profile.programming_experience,
        accessibility_settings=profile.accessibility_settings,
        goals=profile.goals,
        interests=profile.interests,
        is_active=profile.is_active,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        last_login=profile.last_login,
        profile_completion_percentage=profile.profile_completion_percentage
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_learner_profile(
    current_user: LearnerProfile = Depends(get_current_active_user)
):
    """
    Delete current learner's profile
    
    Performs a soft delete by marking the profile as inactive.
    This preserves learning history while preventing further access.
    """
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    
    success = await repository.delete_learner_profile(str(current_user.id))
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found or could not be deleted"
        )


@router.get("", response_model=List[LearnerProfileResponse])
async def search_learners(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    country: Optional[str] = Query(None, description="Filter by country"),
    education_level: Optional[str] = Query(None, description="Filter by education level"),
    experience_level: Optional[str] = Query(None, description="Filter by programming experience level"),
    search_text: Optional[str] = Query(None, description="Search in name and email"),
    current_user: LearnerProfile = Depends(get_current_active_user)
):
    """
    Search learners with filters and pagination
    
    Returns a paginated list of learner profiles matching the specified criteria.
    Currently restricted for privacy - this would typically be an admin function.
    """
    # For now, return empty list as this would be an admin function
    # In a real implementation, you'd check for admin privileges
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Insufficient privileges"
    )


@router.get("/stats/completion", response_model=Dict[str, Any])
async def get_profile_completion_stats(
    current_user: LearnerProfile = Depends(get_current_active_user)
):
    """
    Get profile completion statistics
    
    Returns detailed information about profile completion status
    and suggestions for improving the profile.
    """
    completion_percentage = current_user.profile_completion_percentage
    
    # Calculate missing fields
    missing_fields = []
    suggestions = []
    
    if not current_user.demographics.age:
        missing_fields.append("age")
        suggestions.append("Add your age to help personalize content difficulty")
    
    if not current_user.demographics.education_level:
        missing_fields.append("education_level")
        suggestions.append("Specify your education level for better content recommendations")
    
    if not current_user.learning_preferences.learning_styles:
        missing_fields.append("learning_styles")
        suggestions.append("Select your preferred learning styles to optimize content delivery")
    
    if current_user.programming_experience.overall_experience == "none":
        missing_fields.append("programming_experience")
        suggestions.append("Update your programming experience to get appropriate challenges")
    
    if not current_user.goals:
        missing_fields.append("goals")
        suggestions.append("Set learning goals to track your progress effectively")
    
    if not current_user.interests:
        missing_fields.append("interests")
        suggestions.append("Add your interests to discover relevant learning content")
    
    return {
        "completion_percentage": completion_percentage,
        "is_complete": completion_percentage >= 80.0,
        "missing_fields": missing_fields,
        "suggestions": suggestions,
        "total_fields": 8,
        "completed_fields": 8 - len(missing_fields)
    }