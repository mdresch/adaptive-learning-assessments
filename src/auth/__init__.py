"""
Authentication and authorization for the Adaptive Learning System.
"""

from .dependencies import (
    get_current_user,
    get_current_learner,
    get_current_educator,
    get_current_admin,
    create_access_token,
    verify_token
)

__all__ = [
    "get_current_user",
    "get_current_learner", 
    "get_current_educator",
    "get_current_admin",
    "create_access_token",
    "verify_token"
]