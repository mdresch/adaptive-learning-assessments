"""
FastAPI Dependencies

Dependency injection for BKT engine, database connections, authentication, etc.
"""

import os
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import jwt

from ..core.bkt_engine import BKTEngine
from ..db.bkt_repository import BKTRepository
from ..utils.cache_manager import CacheManager, InMemoryCache
from ..models.bkt_models import BKTConfiguration, BKTParameters

logger = logging.getLogger(__name__)

# Global instances (initialized at startup)
_database: Optional[AsyncIOMotorDatabase] = None
_bkt_repository: Optional[BKTRepository] = None
_cache_manager: Optional[CacheManager] = None
_bkt_engine: Optional[BKTEngine] = None

# Security
security = HTTPBearer()


async def initialize_dependencies():
    """Initialize all dependencies at application startup"""
    global _database, _bkt_repository, _cache_manager, _bkt_engine
    
    try:
        # Initialize database connection
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("DATABASE_NAME", "adaptive_learning")
        
        client = AsyncIOMotorClient(mongodb_uri)
        _database = client[database_name]
        
        # Initialize repository
        _bkt_repository = BKTRepository(_database)
        await _bkt_repository.initialize_indexes()
        
        # Initialize cache manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        use_redis = os.getenv("USE_REDIS", "true").lower() == "true"
        
        if use_redis:
            _cache_manager = CacheManager(redis_url=redis_url)
            try:
                await _cache_manager.initialize()
            except Exception as e:
                logger.warning(f"Redis unavailable, falling back to in-memory cache: {e}")
                _cache_manager = InMemoryCache()
                await _cache_manager.initialize()
        else:
            _cache_manager = InMemoryCache()
            await _cache_manager.initialize()
        
        # Initialize BKT configuration
        config = BKTConfiguration(
            default_parameters=BKTParameters(
                skill_id="default",
                p_l0=float(os.getenv("BKT_DEFAULT_P_L0", "0.1")),
                p_t=float(os.getenv("BKT_DEFAULT_P_T", "0.1")),
                p_g=float(os.getenv("BKT_DEFAULT_P_G", "0.2")),
                p_s=float(os.getenv("BKT_DEFAULT_P_S", "0.1"))
            ),
            mastery_threshold=float(os.getenv("BKT_MASTERY_THRESHOLD", "0.8")),
            min_attempts_for_mastery=int(os.getenv("BKT_MIN_ATTEMPTS", "3")),
            cache_ttl_seconds=int(os.getenv("BKT_CACHE_TTL", "300")),
            update_batch_size=int(os.getenv("BKT_BATCH_SIZE", "100"))
        )
        
        # Initialize BKT engine
        max_workers = int(os.getenv("BKT_MAX_WORKERS", "10"))
        _bkt_engine = BKTEngine(_bkt_repository, _cache_manager, config, max_workers)
        await _bkt_engine.initialize()
        
        logger.info("All dependencies initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize dependencies: {e}")
        raise


async def cleanup_dependencies():
    """Cleanup dependencies at application shutdown"""
    global _cache_manager, _bkt_engine
    
    try:
        if _cache_manager:
            await _cache_manager.close()
        
        if _bkt_engine and _bkt_engine.executor:
            _bkt_engine.executor.shutdown(wait=True)
        
        logger.info("Dependencies cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Failed to cleanup dependencies: {e}")


def get_database() -> AsyncIOMotorDatabase:
    """Get database dependency"""
    if _database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized"
        )
    return _database


def get_bkt_repository() -> BKTRepository:
    """Get BKT repository dependency"""
    if _bkt_repository is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BKT repository not initialized"
        )
    return _bkt_repository


def get_cache_manager() -> CacheManager:
    """Get cache manager dependency"""
    if _cache_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache manager not initialized"
        )
    return _cache_manager


def get_bkt_engine() -> BKTEngine:
    """Get BKT engine dependency"""
    if _bkt_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BKT engine not initialized"
        )
    return _bkt_engine


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token.
    
    This is a simplified implementation. In production, you would:
    1. Validate JWT signature
    2. Check token expiration
    3. Verify user exists in database
    4. Handle refresh tokens
    """
    try:
        # Get JWT secret from environment
        jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
        # Decode token
        payload = jwt.decode(
            credentials.credentials,
            jwt_secret,
            algorithms=[jwt_algorithm]
        )
        
        # Extract user information
        user_id = payload.get("sub")
        role = payload.get("role", "learner")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        return {
            "id": user_id,
            "role": role,
            "token_payload": payload
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_learner(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user if they have learner role"""
    if current_user.get("role") != "learner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Learner role required"
        )
    return current_user


async def get_current_educator(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user if they have educator role"""
    if current_user.get("role") not in ["educator", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Educator or admin role required"
        )
    return current_user


async def get_current_admin(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Get current user if they have admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


# Optional dependencies for testing
class TestDependencies:
    """Test dependency overrides for unit testing"""
    
    @staticmethod
    def get_test_user(role: str = "learner", user_id: str = "test_user"):
        """Create a test user dependency"""
        async def _get_test_user():
            return {"id": user_id, "role": role}
        return _get_test_user
    
    @staticmethod
    def get_mock_bkt_engine():
        """Create a mock BKT engine for testing"""
        from unittest.mock import AsyncMock
        
        async def _get_mock_engine():
            mock_engine = AsyncMock()
            # Configure mock methods as needed for tests
            return mock_engine
        
        return _get_mock_engine