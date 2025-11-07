"""
Authentication dependencies for FastAPI endpoints.
"""
from typing import Dict, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# JWT configuration (these should be environment variables in production)
JWT_SECRET_KEY = "your-secret-key-here"  # Should be from environment
JWT_ALGORITHM = "HS256"


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Dict: User information from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Extract user information
        user_id = payload.get("sub")
        user_role = payload.get("role", "learner")
        username = payload.get("username")
        exp = payload.get("exp")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token expiration
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "id": user_id,
            "username": username,
            "role": user_role,
            "token_exp": exp
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_learner(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Get current user ensuring they have learner role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict: User information if they are a learner
        
    Raises:
        HTTPException: If user is not a learner
    """
    if current_user.get("role") != "learner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Learner access required"
        )
    
    return current_user


async def get_current_educator(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Get current user ensuring they have educator role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict: User information if they are an educator
        
    Raises:
        HTTPException: If user is not an educator
    """
    if current_user.get("role") not in ["educator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Educator access required"
        )
    
    return current_user


async def get_current_admin(current_user: Dict = Depends(get_current_user)) -> Dict:
    """
    Get current user ensuring they have admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict: User information if they are an admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    
    return current_user


def create_access_token(user_id: str, username: str, role: str = "learner", expires_delta: Optional[int] = None) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User identifier
        username: Username
        role: User role (learner, educator, admin)
        expires_delta: Token expiration time in seconds
        
    Returns:
        str: JWT token
    """
    try:
        # Set expiration time
        if expires_delta:
            expire = datetime.utcnow().timestamp() + expires_delta
        else:
            expire = datetime.utcnow().timestamp() + (24 * 60 * 60)  # 24 hours default
        
        # Create payload
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow().timestamp()
        }
        
        # Encode token
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
        
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify a JWT token and return payload if valid.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.JWTError:
        return None


async def require_permission(required_permissions: list):
    """
    Dependency factory for requiring specific permissions.
    
    Args:
        required_permissions: List of required permissions
        
    Returns:
        Function: Dependency function
    """
    async def permission_checker(current_user: Dict = Depends(get_current_user)) -> Dict:
        user_role = current_user.get("role", "learner")
        
        # Define role permissions
        role_permissions = {
            "learner": ["read_own_data", "update_own_profile", "submit_activities"],
            "educator": ["read_own_data", "update_own_profile", "submit_activities", 
                        "read_student_data", "create_content", "view_analytics"],
            "admin": ["read_own_data", "update_own_profile", "submit_activities",
                     "read_student_data", "create_content", "view_analytics",
                     "manage_users", "system_admin"]
        }
        
        user_permissions = role_permissions.get(user_role, [])
        
        # Check if user has all required permissions
        missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


# Rate limiting dependency (simplified implementation)
class RateLimiter:
    """Simple rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # In production, use Redis or similar
    
    async def __call__(self, current_user: Dict = Depends(get_current_user)) -> Dict:
        """Check rate limit for current user."""
        user_id = current_user["id"]
        current_time = datetime.utcnow().timestamp()
        
        # Clean old entries
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if current_time - req_time < self.window_seconds
            ]
        else:
            self.requests[user_id] = []
        
        # Check rate limit
        if len(self.requests[user_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Add current request
        self.requests[user_id].append(current_time)
        
        return current_user


# Create rate limiter instances
standard_rate_limit = RateLimiter(max_requests=100, window_seconds=3600)  # 100 requests per hour
strict_rate_limit = RateLimiter(max_requests=20, window_seconds=3600)     # 20 requests per hour