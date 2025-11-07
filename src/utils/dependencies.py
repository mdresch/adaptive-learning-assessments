"""
Dependency injection utilities for FastAPI.

This module provides dependency functions for injecting database connections,
engines, and other services into API endpoints.
"""

import os
import logging
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends

from ..core.bkt_engine import BKTEngine
from ..db.mastery_repository import MasteryRepository

logger = logging.getLogger(__name__)

# Global instances
_motor_client: AsyncIOMotorClient = None
_database: AsyncIOMotorDatabase = None
_bkt_engine: BKTEngine = None


async def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    global _motor_client, _database
    
    if _database is None:
        # Get MongoDB connection string from environment
        mongodb_uri = os.getenv("MONGODB_URI")
        if not mongodb_uri:
            raise ValueError("MONGODB_URI environment variable is required")
        
        # Create motor client
        _motor_client = AsyncIOMotorClient(mongodb_uri)
        
        # Get database (extract from URI or use default)
        database_name = os.getenv("MONGODB_DATABASE", "adaptive_learning")
        _database = _motor_client[database_name]
        
        logger.info(f"Connected to MongoDB database: {database_name}")
    
    return _database


async def get_mastery_repository(
    database: AsyncIOMotorDatabase = Depends(get_database)
) -> MasteryRepository:
    """Get mastery repository instance."""
    repository = MasteryRepository(database)
    
    # Ensure indexes are created (idempotent operation)
    try:
        await repository.create_indexes()
    except Exception as e:
        logger.warning(f"Could not create indexes: {str(e)}")
    
    return repository


def get_bkt_engine() -> BKTEngine:
    """Get BKT engine instance."""
    global _bkt_engine
    
    if _bkt_engine is None:
        _bkt_engine = BKTEngine()
        logger.info("Initialized BKT engine")
    
    return _bkt_engine


async def close_database_connection():
    """Close database connection (for application shutdown)."""
    global _motor_client, _database
    
    if _motor_client:
        _motor_client.close()
        _motor_client = None
        _database = None
        logger.info("Closed MongoDB connection")