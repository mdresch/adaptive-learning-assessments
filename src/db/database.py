"""
Database connection and configuration module

This module handles MongoDB connection setup and provides database instances
for the adaptive learning system.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database = None
        
    async def connect_to_mongo(self):
        """Create database connection"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            self.client = AsyncIOMotorClient(mongodb_uri)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database name from URI or use default
            database_name = os.getenv("DATABASE_NAME", "adaptive_learning_system")
            self.database = self.client[database_name]
            
            logger.info(f"Connected to MongoDB database: {database_name}")
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    async def close_mongo_connection(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if not self.database:
            raise RuntimeError("Database not connected")
        return self.database[collection_name]


# Global database instance
db = Database()


async def get_database():
    """Dependency to get database instance"""
    return db.database


async def get_learner_collection():
    """Get the learner profiles collection"""
    return db.get_collection("learner_profiles")