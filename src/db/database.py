"""
Database connection and configuration for MongoDB Atlas

This module handles the database connection, configuration, and provides
database access methods for the Adaptive Learning System.
"""

import os
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB Atlas database connections and operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.database_name = os.getenv("DATABASE_NAME", "adaptive_learning_system")
        
    async def connect_to_database(self) -> None:
        """Establish connection to MongoDB Atlas"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable is not set")
            
            self.client = AsyncIOMotorClient(
                mongodb_uri,
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=45000,
                serverSelectionTimeoutMS=5000,
                socketTimeoutMS=20000,
                connectTimeoutMS=10000,
            )
            
            # Test the connection
            await self.client.admin.command('ping')
            
            self.database = self.client[self.database_name]
            logger.info(f"Successfully connected to MongoDB database: {self.database_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {e}")
            raise
    
    async def close_database_connection(self) -> None:
        """Close the database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get the database instance"""
        if not self.database:
            raise RuntimeError("Database not connected. Call connect_to_database() first.")
        return self.database
    
    async def create_indexes(self) -> None:
        """Create necessary database indexes for optimal performance"""
        if not self.database:
            raise RuntimeError("Database not connected")
        
        try:
            # Learners collection indexes
            learners_collection = self.database.learners
            
            # Unique indexes
            await learners_collection.create_index("username", unique=True)
            await learners_collection.create_index("email", unique=True)
            
            # Performance indexes
            await learners_collection.create_index("is_active")
            await learners_collection.create_index("created_at")
            await learners_collection.create_index("updated_at")
            await learners_collection.create_index("last_login")
            
            # Compound indexes for common queries
            await learners_collection.create_index([
                ("is_active", 1),
                ("updated_at", -1)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {e}")
            raise


# Global database manager instance
database_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency function to get database instance"""
    return database_manager.get_database()


async def startup_database():
    """Startup function to initialize database connection"""
    await database_manager.connect_to_database()
    await database_manager.create_indexes()


async def shutdown_database():
    """Shutdown function to close database connection"""
    await database_manager.close_database_connection()