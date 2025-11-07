"""
MongoDB client and connection management for the Adaptive Learning System.
"""

import logging
import os
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError


logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    MongoDB client wrapper for the Adaptive Learning System.
    
    Provides connection management, database operations, and
    collection access for the adaptive learning data.
    """
    
    def __init__(self, connection_string: Optional[str] = None, database_name: str = "adaptive_learning"):
        """
        Initialize MongoDB client.
        
        Args:
            connection_string: MongoDB connection string (optional, uses env var if not provided)
            database_name: Database name to use
        """
        self.connection_string = connection_string or os.getenv("MONGODB_URI")
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.logger = logger
        
        if not self.connection_string:
            raise ValueError("MongoDB connection string not provided and MONGODB_URI env var not set")
    
    async def connect(self) -> bool:
        """
        Connect to MongoDB.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database
            self.database = self.client[self.database_name]
            
            self.logger.info(f"Connected to MongoDB database: {self.database_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            self.logger.info("Disconnected from MongoDB")
    
    async def ensure_connected(self) -> bool:
        """
        Ensure connection is active, reconnect if necessary.
        
        Returns:
            True if connected, False otherwise
        """
        if not self.client or not self.database:
            return await self.connect()
        
        try:
            # Test connection with a simple ping
            await self.client.admin.command('ping')
            return True
        except Exception:
            self.logger.warning("MongoDB connection lost, attempting to reconnect...")
            return await self.connect()
    
    def get_collection(self, collection_name: str):
        """
        Get a collection from the database.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
            
        Raises:
            RuntimeError: If not connected to database
        """
        if not self.database:
            raise RuntimeError("Not connected to MongoDB database")
        
        return self.database[collection_name]
    
    async def create_indexes(self):
        """Create necessary indexes for optimal performance."""
        if not await self.ensure_connected():
            raise RuntimeError("Cannot create indexes: not connected to database")
        
        try:
            # Learner profiles indexes
            learner_profiles = self.get_collection("learner_profiles")
            await learner_profiles.create_index("learner_id", unique=True)
            await learner_profiles.create_index("email", unique=True)
            await learner_profiles.create_index("username")
            await learner_profiles.create_index("created_at")
            
            # Competencies indexes
            competencies = self.get_collection("competencies")
            await competencies.create_index("competency_id", unique=True)
            await competencies.create_index("category")
            await competencies.create_index("difficulty_level")
            await competencies.create_index([("category", 1), ("subcategory", 1)])
            
            # Learner competencies indexes
            learner_competencies = self.get_collection("learner_competencies")
            await learner_competencies.create_index([("learner_id", 1), ("competency_id", 1)], unique=True)
            await learner_competencies.create_index("learner_id")
            await learner_competencies.create_index("competency_id")
            await learner_competencies.create_index("mastery_probability")
            await learner_competencies.create_index("updated_at")
            
            # Performance records indexes
            performance_records = self.get_collection("performance_records")
            await performance_records.create_index([("learner_id", 1), ("timestamp", -1)])
            await performance_records.create_index("session_id")
            await performance_records.create_index("activity_id")
            await performance_records.create_index("competency_id")
            await performance_records.create_index("interaction_type")
            
            # Activity results indexes
            activity_results = self.get_collection("activity_results")
            await activity_results.create_index([("learner_id", 1), ("start_time", -1)])
            await activity_results.create_index("activity_id")
            await activity_results.create_index("session_id")
            await activity_results.create_index([("learner_id", 1), ("activity_id", 1), ("attempt_number", 1)])
            
            # Learning sessions indexes
            learning_sessions = self.get_collection("learning_sessions")
            await learning_sessions.create_index("session_id", unique=True)
            await learning_sessions.create_index([("learner_id", 1), ("start_time", -1)])
            
            # BKT states indexes
            bkt_states = self.get_collection("bkt_states")
            await bkt_states.create_index([("learner_id", 1), ("competency_id", 1)], unique=True)
            await bkt_states.create_index("learner_id")
            await bkt_states.create_index("competency_id")
            await bkt_states.create_index("mastery_probability")
            await bkt_states.create_index("last_update")
            
            # BKT parameters indexes
            bkt_parameters = self.get_collection("bkt_parameters")
            await bkt_parameters.create_index("competency_id", unique=True)
            
            # Competency updates indexes
            competency_updates = self.get_collection("competency_updates")
            await competency_updates.create_index([("learner_id", 1), ("timestamp", -1)])
            await competency_updates.create_index("competency_id")
            await competency_updates.create_index("activity_id")
            await competency_updates.create_index("session_id")
            
            # Learning activities indexes
            learning_activities = self.get_collection("learning_activities")
            await learning_activities.create_index("activity_id", unique=True)
            await learning_activities.create_index("activity_type")
            await learning_activities.create_index("difficulty_level")
            await learning_activities.create_index("target_competencies")
            await learning_activities.create_index("is_active")
            
            self.logger.info("Successfully created MongoDB indexes")
            
        except Exception as e:
            self.logger.error(f"Failed to create MongoDB indexes: {e}")
            raise
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        if not await self.ensure_connected():
            raise RuntimeError("Cannot get stats: not connected to database")
        
        try:
            stats = await self.database.command("dbStats")
            
            # Get collection counts
            collection_stats = {}
            collection_names = [
                "learner_profiles", "competencies", "learner_competencies",
                "performance_records", "activity_results", "learning_sessions",
                "bkt_states", "bkt_parameters", "competency_updates", "learning_activities"
            ]
            
            for collection_name in collection_names:
                try:
                    collection = self.get_collection(collection_name)
                    count = await collection.count_documents({})
                    collection_stats[collection_name] = count
                except Exception as e:
                    self.logger.warning(f"Failed to get count for {collection_name}: {e}")
                    collection_stats[collection_name] = "error"
            
            return {
                "database_name": self.database_name,
                "collections": len(stats.get("collections", 0)),
                "data_size_mb": stats.get("dataSize", 0) / (1024 * 1024),
                "storage_size_mb": stats.get("storageSize", 0) / (1024 * 1024),
                "index_size_mb": stats.get("indexSize", 0) / (1024 * 1024),
                "collection_counts": collection_stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.
        
        Returns:
            Dictionary with health check results
        """
        health_status = {
            "status": "unknown",
            "connected": False,
            "response_time_ms": None,
            "error": None
        }
        
        try:
            import time
            start_time = time.time()
            
            # Test connection
            if await self.ensure_connected():
                # Perform a simple operation
                await self.client.admin.command('ping')
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                
                health_status.update({
                    "status": "healthy",
                    "connected": True,
                    "response_time_ms": round(response_time, 2)
                })
            else:
                health_status.update({
                    "status": "unhealthy",
                    "connected": False,
                    "error": "Failed to connect to database"
                })
                
        except Exception as e:
            health_status.update({
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            })
        
        return health_status