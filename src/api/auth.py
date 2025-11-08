"""
Authentication dependencies and utilities

This module provides authentication dependencies for FastAPI endpoints
and user session management.
"""

from datetime import timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..db.database import get_learner_collection
from ..db.learner_repository import LearnerRepository
from ..models.learner_profile import LearnerProfile
from ..utils.security import verify_token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES


# Security scheme
security = HTTPBearer()


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Token data model"""
    email: Optional[str] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> LearnerProfile:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email)
    except Exception:
        raise credentials_exception
    
    # Get user from database
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    user = await repository.get_learner_by_email(email=token_data.email)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: LearnerProfile = Depends(get_current_user)
) -> LearnerProfile:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def authenticate_user(email: str, password: str) -> Optional[LearnerProfile]:
    """Authenticate user with email and password"""
    collection = await get_learner_collection()
    repository = LearnerRepository(collection)
    return await repository.authenticate_learner(email, password)


async def create_user_token(user: LearnerProfile) -> Token:
    """Create access token for user"""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )