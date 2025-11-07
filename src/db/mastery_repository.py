"""
Database repository for mastery tracking data.

This module provides database operations for learner interactions,
mastery levels, and competency data using MongoDB.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from ..models.mastery import (
    LearnerInteraction,
    MasteryLevel,
    MicroCompetency,
    ProgressReport,
    BKTParameters
)

logger = logging.getLogger(__name__)


class MasteryRepository:
    """Repository for mastery tracking data operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize the repository with a database connection.
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.interactions_collection = database.learner_interactions
        self.mastery_collection = database.mastery_levels
        self.competencies_collection = database.micro_competencies
    
    async def create_indexes(self):
        """Create necessary database indexes for optimal performance."""
        try:
            # Indexes for learner_interactions collection
            await self.interactions_collection.create_index([
                ("learner_id", ASCENDING),
                ("completed_at", DESCENDING)
            ])
            await self.interactions_collection.create_index([
                ("competency_ids", ASCENDING),
                ("completed_at", DESCENDING)
            ])
            await self.interactions_collection.create_index([
                ("activity_id", ASCENDING)
            ])
            await self.interactions_collection.create_index([
                ("session_id", ASCENDING)
            ])
            
            # Indexes for mastery_levels collection
            await self.mastery_collection.create_index([
                ("learner_id", ASCENDING),
                ("competency_id", ASCENDING)
            ], unique=True)
            await self.mastery_collection.create_index([
                ("learner_id", ASCENDING),
                ("current_mastery", DESCENDING)
            ])
            await self.mastery_collection.create_index([
                ("competency_id", ASCENDING),
                ("current_mastery", DESCENDING)
            ])
            
            # Indexes for micro_competencies collection
            await self.competencies_collection.create_index([
                ("competency_id", ASCENDING)
            ], unique=True)
            await self.competencies_collection.create_index([
                ("category", ASCENDING),
                ("subcategory", ASCENDING)
            ])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")
            raise
    
    # Learner Interaction Operations
    
    async def save_interaction(self, interaction: LearnerInteraction) -> str:
        """
        Save a learner interaction to the database.
        
        Args:
            interaction: Learner interaction to save
            
        Returns:
            ID of the saved interaction
        """
        try:
            interaction_dict = interaction.dict(by_alias=True, exclude_unset=True)
            if "_id" in interaction_dict and interaction_dict["_id"] is None:
                del interaction_dict["_id"]
            
            result = await self.interactions_collection.insert_one(interaction_dict)
            logger.info(f"Saved interaction {result.inserted_id} for learner {interaction.learner_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error saving interaction: {str(e)}")
            raise
    
    async def get_interactions_by_learner(
        self, 
        learner_id: str, 
        limit: Optional[int] = None,
        since: Optional[datetime] = None
    ) -> List[LearnerInteraction]:
        """
        Get interactions for a specific learner.
        
        Args:
            learner_id: Learner identifier
            limit: Maximum number of interactions to return
            since: Only return interactions after this timestamp
            
        Returns:
            List of learner interactions
        """
        try:
            query = {"learner_id": learner_id}
            if since:
                query["completed_at"] = {"$gte": since}
            
            cursor = self.interactions_collection.find(query).sort("completed_at", DESCENDING)
            if limit:
                cursor = cursor.limit(limit)
            
            interactions = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                interactions.append(LearnerInteraction(**doc))
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error getting interactions for learner {learner_id}: {str(e)}")
            raise
    
    async def get_interactions_by_competency(
        self, 
        competency_id: str, 
        limit: Optional[int] = None
    ) -> List[LearnerInteraction]:
        """
        Get interactions for a specific competency.
        
        Args:
            competency_id: Competency identifier
            limit: Maximum number of interactions to return
            
        Returns:
            List of learner interactions
        """
        try:
            query = {"competency_ids": competency_id}
            cursor = self.interactions_collection.find(query).sort("completed_at", DESCENDING)
            if limit:
                cursor = cursor.limit(limit)
            
            interactions = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                interactions.append(LearnerInteraction(**doc))
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error getting interactions for competency {competency_id}: {str(e)}")
            raise
    
    async def get_recent_interactions(
        self, 
        hours: int = 24, 
        limit: Optional[int] = None
    ) -> List[LearnerInteraction]:
        """
        Get recent interactions across all learners.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of interactions to return
            
        Returns:
            List of recent learner interactions
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = {"completed_at": {"$gte": since}}
            
            cursor = self.interactions_collection.find(query).sort("completed_at", DESCENDING)
            if limit:
                cursor = cursor.limit(limit)
            
            interactions = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                interactions.append(LearnerInteraction(**doc))
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error getting recent interactions: {str(e)}")
            raise
    
    # Mastery Level Operations
    
    async def save_mastery_level(self, mastery_level: MasteryLevel) -> str:
        """
        Save or update a mastery level.
        
        Args:
            mastery_level: Mastery level to save
            
        Returns:
            ID of the saved mastery level
        """
        try:
            mastery_dict = mastery_level.dict(by_alias=True, exclude_unset=True)
            
            # Use upsert to update existing or create new
            filter_query = {
                "learner_id": mastery_level.learner_id,
                "competency_id": mastery_level.competency_id
            }
            
            if "_id" in mastery_dict:
                del mastery_dict["_id"]
            
            result = await self.mastery_collection.replace_one(
                filter_query, 
                mastery_dict, 
                upsert=True
            )
            
            if result.upserted_id:
                mastery_id = str(result.upserted_id)
                logger.info(f"Created new mastery level {mastery_id}")
            else:
                # Find the existing document to get its ID
                existing = await self.mastery_collection.find_one(filter_query)
                mastery_id = str(existing["_id"]) if existing else None
                logger.info(f"Updated existing mastery level {mastery_id}")
            
            return mastery_id
            
        except Exception as e:
            logger.error(f"Error saving mastery level: {str(e)}")
            raise
    
    async def get_mastery_level(
        self, 
        learner_id: str, 
        competency_id: str
    ) -> Optional[MasteryLevel]:
        """
        Get mastery level for a specific learner and competency.
        
        Args:
            learner_id: Learner identifier
            competency_id: Competency identifier
            
        Returns:
            Mastery level or None if not found
        """
        try:
            doc = await self.mastery_collection.find_one({
                "learner_id": learner_id,
                "competency_id": competency_id
            })
            
            if doc:
                doc["_id"] = str(doc["_id"])
                return MasteryLevel(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting mastery level: {str(e)}")
            raise
    
    async def get_mastery_levels_by_learner(
        self, 
        learner_id: str
    ) -> List[MasteryLevel]:
        """
        Get all mastery levels for a specific learner.
        
        Args:
            learner_id: Learner identifier
            
        Returns:
            List of mastery levels
        """
        try:
            cursor = self.mastery_collection.find({"learner_id": learner_id})
            
            mastery_levels = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                mastery_levels.append(MasteryLevel(**doc))
            
            return mastery_levels
            
        except Exception as e:
            logger.error(f"Error getting mastery levels for learner {learner_id}: {str(e)}")
            raise
    
    async def create_initial_mastery_level(
        self, 
        learner_id: str, 
        competency_id: str,
        initial_parameters: Optional[BKTParameters] = None
    ) -> MasteryLevel:
        """
        Create an initial mastery level for a learner-competency pair.
        
        Args:
            learner_id: Learner identifier
            competency_id: Competency identifier
            initial_parameters: Optional custom BKT parameters
            
        Returns:
            Created mastery level
        """
        try:
            # Check if mastery level already exists
            existing = await self.get_mastery_level(learner_id, competency_id)
            if existing:
                return existing
            
            # Create new mastery level with default values
            mastery_level = MasteryLevel(
                learner_id=learner_id,
                competency_id=competency_id,
                current_mastery=initial_parameters.prior_knowledge if initial_parameters else 0.1,
                bkt_parameters=initial_parameters or BKTParameters()
            )
            
            await self.save_mastery_level(mastery_level)
            return mastery_level
            
        except Exception as e:
            logger.error(f"Error creating initial mastery level: {str(e)}")
            raise
    
    # Competency Operations
    
    async def save_competency(self, competency: MicroCompetency) -> str:
        """
        Save a micro-competency definition.
        
        Args:
            competency: Competency to save
            
        Returns:
            ID of the saved competency
        """
        try:
            competency_dict = competency.dict(by_alias=True, exclude_unset=True)
            
            # Use upsert based on competency_id
            filter_query = {"competency_id": competency.competency_id}
            
            if "_id" in competency_dict:
                del competency_dict["_id"]
            
            result = await self.competencies_collection.replace_one(
                filter_query,
                competency_dict,
                upsert=True
            )
            
            if result.upserted_id:
                competency_id = str(result.upserted_id)
                logger.info(f"Created new competency {competency_id}")
            else:
                existing = await self.competencies_collection.find_one(filter_query)
                competency_id = str(existing["_id"]) if existing else None
                logger.info(f"Updated existing competency {competency_id}")
            
            return competency_id
            
        except Exception as e:
            logger.error(f"Error saving competency: {str(e)}")
            raise
    
    async def get_competency(self, competency_id: str) -> Optional[MicroCompetency]:
        """
        Get a competency by ID.
        
        Args:
            competency_id: Competency identifier
            
        Returns:
            Competency or None if not found
        """
        try:
            doc = await self.competencies_collection.find_one({"competency_id": competency_id})
            
            if doc:
                doc["_id"] = str(doc["_id"])
                return MicroCompetency(**doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting competency {competency_id}: {str(e)}")
            raise
    
    async def get_competencies_by_category(
        self, 
        category: str, 
        subcategory: Optional[str] = None
    ) -> List[MicroCompetency]:
        """
        Get competencies by category and optional subcategory.
        
        Args:
            category: Competency category
            subcategory: Optional subcategory filter
            
        Returns:
            List of competencies
        """
        try:
            query = {"category": category}
            if subcategory:
                query["subcategory"] = subcategory
            
            cursor = self.competencies_collection.find(query)
            
            competencies = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                competencies.append(MicroCompetency(**doc))
            
            return competencies
            
        except Exception as e:
            logger.error(f"Error getting competencies by category: {str(e)}")
            raise
    
    # Analytics and Reporting
    
    async def get_learner_progress_summary(self, learner_id: str) -> Dict[str, Any]:
        """
        Get a summary of learner progress across all competencies.
        
        Args:
            learner_id: Learner identifier
            
        Returns:
            Progress summary dictionary
        """
        try:
            # Aggregate mastery data
            pipeline = [
                {"$match": {"learner_id": learner_id}},
                {"$group": {
                    "_id": None,
                    "total_competencies": {"$sum": 1},
                    "mastered_competencies": {
                        "$sum": {"$cond": [{"$eq": ["$is_mastered", True]}, 1, 0]}
                    },
                    "average_mastery": {"$avg": "$current_mastery"},
                    "total_interactions": {"$sum": "$total_interactions"},
                    "total_correct": {"$sum": "$correct_interactions"}
                }}
            ]
            
            result = await self.mastery_collection.aggregate(pipeline).to_list(1)
            
            if result:
                summary = result[0]
                summary["mastery_percentage"] = (
                    summary["mastered_competencies"] / summary["total_competencies"] * 100
                    if summary["total_competencies"] > 0 else 0
                )
                summary["overall_accuracy"] = (
                    summary["total_correct"] / summary["total_interactions"] * 100
                    if summary["total_interactions"] > 0 else 0
                )
                del summary["_id"]
                return summary
            else:
                return {
                    "total_competencies": 0,
                    "mastered_competencies": 0,
                    "average_mastery": 0.0,
                    "mastery_percentage": 0.0,
                    "total_interactions": 0,
                    "total_correct": 0,
                    "overall_accuracy": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting progress summary for learner {learner_id}: {str(e)}")
            raise
    
    async def get_competency_performance_stats(self, competency_id: str) -> Dict[str, Any]:
        """
        Get performance statistics for a specific competency across all learners.
        
        Args:
            competency_id: Competency identifier
            
        Returns:
            Performance statistics dictionary
        """
        try:
            # Aggregate performance data
            pipeline = [
                {"$match": {"competency_id": competency_id}},
                {"$group": {
                    "_id": None,
                    "total_learners": {"$sum": 1},
                    "mastered_learners": {
                        "$sum": {"$cond": [{"$eq": ["$is_mastered", True]}, 1, 0]}
                    },
                    "average_mastery": {"$avg": "$current_mastery"},
                    "min_mastery": {"$min": "$current_mastery"},
                    "max_mastery": {"$max": "$current_mastery"},
                    "total_interactions": {"$sum": "$total_interactions"},
                    "average_interactions": {"$avg": "$total_interactions"}
                }}
            ]
            
            result = await self.mastery_collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                stats["mastery_rate"] = (
                    stats["mastered_learners"] / stats["total_learners"] * 100
                    if stats["total_learners"] > 0 else 0
                )
                del stats["_id"]
                return stats
            else:
                return {
                    "total_learners": 0,
                    "mastered_learners": 0,
                    "average_mastery": 0.0,
                    "min_mastery": 0.0,
                    "max_mastery": 0.0,
                    "mastery_rate": 0.0,
                    "total_interactions": 0,
                    "average_interactions": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting performance stats for competency {competency_id}: {str(e)}")
            raise