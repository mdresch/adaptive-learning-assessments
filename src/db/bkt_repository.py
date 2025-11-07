"""
BKT Repository

Database access layer for BKT-related data operations with MongoDB.
Provides optimized queries and connection management for concurrent users.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from ..models.bkt_models import (
    BKTParameters, LearnerCompetency, PerformanceEvent, 
    SkillHierarchy, LearnerProfile
)

logger = logging.getLogger(__name__)


class BKTRepository:
    """
    Repository class for BKT data operations with MongoDB.
    Optimized for concurrent access and performance.
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.competencies: AsyncIOMotorCollection = database.competencies
        self.performance_events: AsyncIOMotorCollection = database.performance_events
        self.skill_parameters: AsyncIOMotorCollection = database.skill_parameters
        self.skill_hierarchies: AsyncIOMotorCollection = database.skill_hierarchies
        self.learner_profiles: AsyncIOMotorCollection = database.learner_profiles
        
    async def initialize_indexes(self):
        """Create database indexes for optimal query performance"""
        try:
            # Competencies indexes
            competency_indexes = [
                IndexModel([("learner_id", ASCENDING), ("skill_id", ASCENDING)], unique=True),
                IndexModel([("learner_id", ASCENDING)]),
                IndexModel([("skill_id", ASCENDING)]),
                IndexModel([("is_mastered", ASCENDING)]),
                IndexModel([("last_updated", DESCENDING)]),
                IndexModel([("p_known", DESCENDING)])
            ]
            await self.competencies.create_indexes(competency_indexes)
            
            # Performance events indexes
            event_indexes = [
                IndexModel([("learner_id", ASCENDING), ("skill_id", ASCENDING)]),
                IndexModel([("learner_id", ASCENDING), ("timestamp", DESCENDING)]),
                IndexModel([("skill_id", ASCENDING), ("timestamp", DESCENDING)]),
                IndexModel([("activity_id", ASCENDING)]),
                IndexModel([("timestamp", DESCENDING)])
            ]
            await self.performance_events.create_indexes(event_indexes)
            
            # Skill parameters indexes
            param_indexes = [
                IndexModel([("skill_id", ASCENDING)], unique=True)
            ]
            await self.skill_parameters.create_indexes(param_indexes)
            
            # Skill hierarchies indexes
            hierarchy_indexes = [
                IndexModel([("skill_id", ASCENDING)], unique=True),
                IndexModel([("domain", ASCENDING)]),
                IndexModel([("difficulty_level", ASCENDING)])
            ]
            await self.skill_hierarchies.create_indexes(hierarchy_indexes)
            
            # Learner profiles indexes
            profile_indexes = [
                IndexModel([("learner_id", ASCENDING)], unique=True),
                IndexModel([("updated_at", DESCENDING)])
            ]
            await self.learner_profiles.create_indexes(profile_indexes)
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            raise
    
    # Competency operations
    async def get_competency(self, learner_id: str, skill_id: str) -> Optional[LearnerCompetency]:
        """Get learner competency for a specific skill"""
        try:
            doc = await self.competencies.find_one({
                "learner_id": learner_id,
                "skill_id": skill_id
            })
            return LearnerCompetency(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get competency: {e}")
            raise
    
    async def save_competency(self, competency: LearnerCompetency) -> LearnerCompetency:
        """Save or update learner competency"""
        try:
            doc = competency.dict(by_alias=True, exclude_unset=True)
            doc["last_updated"] = datetime.utcnow()
            
            result = await self.competencies.replace_one(
                {"learner_id": competency.learner_id, "skill_id": competency.skill_id},
                doc,
                upsert=True
            )
            
            if result.upserted_id:
                competency.id = result.upserted_id
            
            return competency
        except Exception as e:
            logger.error(f"Failed to save competency: {e}")
            raise
    
    async def get_learner_competencies(self, learner_id: str) -> List[LearnerCompetency]:
        """Get all competencies for a learner"""
        try:
            cursor = self.competencies.find({"learner_id": learner_id})
            docs = await cursor.to_list(length=None)
            return [LearnerCompetency(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get learner competencies: {e}")
            raise
    
    async def get_skill_competencies(self, skill_id: str, limit: int = 1000) -> List[LearnerCompetency]:
        """Get competencies for a specific skill across all learners"""
        try:
            cursor = self.competencies.find({"skill_id": skill_id}).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [LearnerCompetency(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get skill competencies: {e}")
            raise
    
    async def get_mastered_skills(self, learner_id: str) -> List[str]:
        """Get list of mastered skill IDs for a learner"""
        try:
            cursor = self.competencies.find(
                {"learner_id": learner_id, "is_mastered": True},
                {"skill_id": 1}
            )
            docs = await cursor.to_list(length=None)
            return [doc["skill_id"] for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get mastered skills: {e}")
            raise
    
    # Performance event operations
    async def save_performance_event(self, event: PerformanceEvent) -> PerformanceEvent:
        """Save a performance event"""
        try:
            doc = event.dict(by_alias=True, exclude_unset=True)
            result = await self.performance_events.insert_one(doc)
            event.id = result.inserted_id
            return event
        except Exception as e:
            logger.error(f"Failed to save performance event: {e}")
            raise
    
    async def get_performance_events(
        self, 
        learner_id: str, 
        skill_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[PerformanceEvent]:
        """Get performance events for a learner"""
        try:
            query = {"learner_id": learner_id}
            if skill_id:
                query["skill_id"] = skill_id
            
            cursor = self.performance_events.find(query).sort("timestamp", DESCENDING).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [PerformanceEvent(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get performance events: {e}")
            raise
    
    async def get_recent_events(
        self, 
        since: datetime, 
        limit: int = 1000
    ) -> List[PerformanceEvent]:
        """Get recent performance events across all learners"""
        try:
            cursor = self.performance_events.find(
                {"timestamp": {"$gte": since}}
            ).sort("timestamp", DESCENDING).limit(limit)
            docs = await cursor.to_list(length=limit)
            return [PerformanceEvent(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            raise
    
    # Skill parameter operations
    async def get_skill_parameters(self, skill_id: str) -> Optional[BKTParameters]:
        """Get BKT parameters for a skill"""
        try:
            doc = await self.skill_parameters.find_one({"skill_id": skill_id})
            return BKTParameters(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get skill parameters: {e}")
            raise
    
    async def save_skill_parameters(self, parameters: BKTParameters) -> BKTParameters:
        """Save BKT parameters for a skill"""
        try:
            doc = parameters.dict(exclude_unset=True)
            await self.skill_parameters.replace_one(
                {"skill_id": parameters.skill_id},
                doc,
                upsert=True
            )
            return parameters
        except Exception as e:
            logger.error(f"Failed to save skill parameters: {e}")
            raise
    
    async def get_all_skill_parameters(self) -> List[BKTParameters]:
        """Get all skill parameters"""
        try:
            cursor = self.skill_parameters.find({})
            docs = await cursor.to_list(length=None)
            return [BKTParameters(**doc) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to get all skill parameters: {e}")
            raise
    
    # Skill hierarchy operations
    async def get_skill_hierarchy(self, skill_id: str) -> Optional[SkillHierarchy]:
        """Get skill hierarchy information"""
        try:
            doc = await self.skill_hierarchies.find_one({"skill_id": skill_id})
            return SkillHierarchy(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get skill hierarchy: {e}")
            raise
    
    async def save_skill_hierarchy(self, hierarchy: SkillHierarchy) -> SkillHierarchy:
        """Save skill hierarchy information"""
        try:
            doc = hierarchy.dict(by_alias=True, exclude_unset=True)
            await self.skill_hierarchies.replace_one(
                {"skill_id": hierarchy.skill_id},
                doc,
                upsert=True
            )
            return hierarchy
        except Exception as e:
            logger.error(f"Failed to save skill hierarchy: {e}")
            raise
    
    async def get_prerequisite_skills(self, skill_id: str) -> List[str]:
        """Get prerequisite skills for a given skill"""
        try:
            doc = await self.skill_hierarchies.find_one(
                {"skill_id": skill_id},
                {"parent_skills": 1}
            )
            return doc.get("parent_skills", []) if doc else []
        except Exception as e:
            logger.error(f"Failed to get prerequisite skills: {e}")
            raise
    
    async def get_dependent_skills(self, skill_id: str) -> List[str]:
        """Get skills that depend on the given skill"""
        try:
            doc = await self.skill_hierarchies.find_one(
                {"skill_id": skill_id},
                {"child_skills": 1}
            )
            return doc.get("child_skills", []) if doc else []
        except Exception as e:
            logger.error(f"Failed to get dependent skills: {e}")
            raise
    
    # Learner profile operations
    async def get_learner_profile(self, learner_id: str) -> Optional[LearnerProfile]:
        """Get learner profile"""
        try:
            doc = await self.learner_profiles.find_one({"learner_id": learner_id})
            return LearnerProfile(**doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to get learner profile: {e}")
            raise
    
    async def save_learner_profile(self, profile: LearnerProfile) -> LearnerProfile:
        """Save learner profile"""
        try:
            doc = profile.dict(by_alias=True, exclude_unset=True)
            doc["updated_at"] = datetime.utcnow()
            
            result = await self.learner_profiles.replace_one(
                {"learner_id": profile.learner_id},
                doc,
                upsert=True
            )
            
            if result.upserted_id:
                profile.id = result.upserted_id
            
            return profile
        except Exception as e:
            logger.error(f"Failed to save learner profile: {e}")
            raise
    
    # Analytics and reporting operations
    async def get_competency_statistics(self, skill_id: str) -> Dict[str, Any]:
        """Get statistical summary of competencies for a skill"""
        try:
            pipeline = [
                {"$match": {"skill_id": skill_id}},
                {"$group": {
                    "_id": None,
                    "total_learners": {"$sum": 1},
                    "mastered_count": {"$sum": {"$cond": ["$is_mastered", 1, 0]}},
                    "avg_p_known": {"$avg": "$p_known"},
                    "min_p_known": {"$min": "$p_known"},
                    "max_p_known": {"$max": "$p_known"},
                    "avg_attempts": {"$avg": "$total_attempts"}
                }}
            ]
            
            cursor = self.competencies.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                stats = result[0]
                stats["mastery_rate"] = stats["mastered_count"] / stats["total_learners"] if stats["total_learners"] > 0 else 0
                return stats
            else:
                return {
                    "total_learners": 0,
                    "mastered_count": 0,
                    "mastery_rate": 0,
                    "avg_p_known": 0,
                    "min_p_known": 0,
                    "max_p_known": 0,
                    "avg_attempts": 0
                }
        except Exception as e:
            logger.error(f"Failed to get competency statistics: {e}")
            raise
    
    async def get_learner_progress_summary(self, learner_id: str) -> Dict[str, Any]:
        """Get progress summary for a learner"""
        try:
            pipeline = [
                {"$match": {"learner_id": learner_id}},
                {"$group": {
                    "_id": None,
                    "total_skills": {"$sum": 1},
                    "mastered_skills": {"$sum": {"$cond": ["$is_mastered", 1, 0]}},
                    "avg_competency": {"$avg": "$p_known"},
                    "total_attempts": {"$sum": "$total_attempts"},
                    "total_correct": {"$sum": "$correct_attempts"}
                }}
            ]
            
            cursor = self.competencies.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                summary = result[0]
                summary["mastery_rate"] = summary["mastered_skills"] / summary["total_skills"] if summary["total_skills"] > 0 else 0
                summary["accuracy_rate"] = summary["total_correct"] / summary["total_attempts"] if summary["total_attempts"] > 0 else 0
                return summary
            else:
                return {
                    "total_skills": 0,
                    "mastered_skills": 0,
                    "mastery_rate": 0,
                    "avg_competency": 0,
                    "total_attempts": 0,
                    "total_correct": 0,
                    "accuracy_rate": 0
                }
        except Exception as e:
            logger.error(f"Failed to get learner progress summary: {e}")
            raise