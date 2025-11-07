"""
Database repository for adaptive learning system.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from src.models.adaptive_models import (
    CompetencyLevel, ChallengeMetadata, AdaptiveRecommendation,
    ActivityResult, DifficultyFeedback, BKTParameters
)

logger = logging.getLogger(__name__)


class AdaptiveRepository:
    """Repository for adaptive learning data operations."""
    
    def __init__(self, database: AsyncIOMotorDatabase = None):
        self.db = database
        # Collections
        self.learners = None
        self.competencies = None
        self.challenges = None
        self.learner_competencies = None
        self.learner_progress = None
        self.learner_activity_logs = None
        self.difficulty_feedback = None
        self.recommendation_history = None
        
        if database:
            self._initialize_collections()
    
    def set_database(self, database: AsyncIOMotorDatabase):
        """Set the database instance and initialize collections."""
        self.db = database
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize collection references."""
        self.learners = self.db.learners
        self.competencies = self.db.competencies
        self.challenges = self.db.challenges
        self.learner_competencies = self.db.learner_competencies
        self.learner_progress = self.db.learner_progress
        self.learner_activity_logs = self.db.learner_activity_logs
        self.difficulty_feedback = self.db.difficulty_feedback
        self.recommendation_history = self.db.recommendation_history
    
    async def get_learner_competencies(self, learner_id: str) -> List[CompetencyLevel]:
        """Get all competency levels for a learner."""
        try:
            cursor = self.learner_competencies.find({"learner_id": ObjectId(learner_id)})
            competency_docs = await cursor.to_list(length=None)
            
            competencies = []
            for doc in competency_docs:
                # Get competency metadata
                comp_meta = await self.competencies.find_one({"_id": doc["competency_id"]})
                if not comp_meta:
                    continue
                
                # Create BKT parameters
                bkt_params = BKTParameters(**doc.get("bkt_parameters", {}))
                
                # Create competency level
                competency = CompetencyLevel(
                    _id=doc["competency_id"],
                    competency_name=comp_meta["name"],
                    mastery_probability=doc["mastery_level"],
                    confidence_level=doc.get("confidence_level", 0.5),
                    last_updated=doc["last_updated"],
                    bkt_parameters=bkt_params
                )
                competencies.append(competency)
            
            return competencies
            
        except Exception as e:
            logger.error(f"Error retrieving learner competencies: {str(e)}")
            raise
    
    async def update_learner_competencies(
        self, 
        learner_id: str, 
        competencies: List[CompetencyLevel]
    ) -> bool:
        """Update learner competency levels."""
        try:
            operations = []
            
            for competency in competencies:
                filter_doc = {
                    "learner_id": ObjectId(learner_id),
                    "competency_id": competency.competency_id
                }
                
                update_doc = {
                    "$set": {
                        "mastery_level": competency.mastery_probability,
                        "confidence_level": competency.confidence_level,
                        "last_updated": competency.last_updated,
                        "bkt_parameters": competency.bkt_parameters.dict()
                    }
                }
                
                operations.append({
                    "update_one": {
                        "filter": filter_doc,
                        "update": update_doc,
                        "upsert": True
                    }
                })
            
            if operations:
                result = await self.learner_competencies.bulk_write(operations)
                logger.info(f"Updated {result.modified_count} competencies for learner {learner_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating learner competencies: {str(e)}")
            raise
    
    async def get_available_challenges(
        self,
        competency_ids: List[str] = None,
        challenge_types: List[str] = None,
        max_difficulty: float = 1.0,
        exclude_completed: bool = True,
        learner_id: str = None
    ) -> List[ChallengeMetadata]:
        """Get available challenges based on criteria."""
        try:
            # Build query filter
            query_filter = {}
            
            if competency_ids:
                query_filter["competencies"] = {"$in": [ObjectId(cid) for cid in competency_ids]}
            
            if challenge_types:
                query_filter["challenge_type"] = {"$in": challenge_types}
            
            if max_difficulty < 1.0:
                query_filter["difficulty_level"] = {"$lte": max_difficulty}
            
            # Get challenges
            cursor = self.challenges.find(query_filter)
            challenge_docs = await cursor.to_list(length=None)
            
            challenges = []
            for doc in challenge_docs:
                # Skip completed challenges if requested
                if exclude_completed and learner_id:
                    completed = await self._is_challenge_completed(learner_id, str(doc["_id"]))
                    if completed:
                        continue
                
                challenge = ChallengeMetadata(
                    _id=doc["_id"],
                    title=doc["title"],
                    description=doc["description"],
                    competencies=doc["competencies"],
                    difficulty_level=doc["difficulty_level"],
                    estimated_duration=doc.get("estimated_duration", 30),
                    challenge_type=doc["challenge_type"],
                    prerequisites=doc.get("prerequisites", [])
                )
                challenges.append(challenge)
            
            return challenges
            
        except Exception as e:
            logger.error(f"Error retrieving available challenges: {str(e)}")
            raise
    
    async def get_challenge_metadata(self, challenge_id: str) -> Optional[ChallengeMetadata]:
        """Get metadata for a specific challenge."""
        try:
            doc = await self.challenges.find_one({"_id": ObjectId(challenge_id)})
            if not doc:
                return None
            
            return ChallengeMetadata(
                _id=doc["_id"],
                title=doc["title"],
                description=doc["description"],
                competencies=doc["competencies"],
                difficulty_level=doc["difficulty_level"],
                estimated_duration=doc.get("estimated_duration", 30),
                challenge_type=doc["challenge_type"],
                prerequisites=doc.get("prerequisites", [])
            )
            
        except Exception as e:
            logger.error(f"Error retrieving challenge metadata: {str(e)}")
            raise
    
    async def store_activity_log(self, activity_result: ActivityResult) -> bool:
        """Store activity completion log."""
        try:
            log_doc = {
                "learner_id": activity_result.learner_id,
                "challenge_id": activity_result.challenge_id,
                "activity_type": "challenge_attempt",
                "timestamp": activity_result.completed_at,
                "details": {
                    "competencies_addressed": activity_result.competencies_addressed,
                    "success": activity_result.success,
                    "score": activity_result.score,
                    "attempts": activity_result.attempts,
                    "time_spent": activity_result.time_spent
                }
            }
            
            result = await self.learner_activity_logs.insert_one(log_doc)
            logger.info(f"Stored activity log for learner {activity_result.learner_id}")
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing activity log: {str(e)}")
            raise
    
    async def store_difficulty_feedback(self, feedback: DifficultyFeedback) -> bool:
        """Store difficulty feedback from learner."""
        try:
            feedback_doc = {
                "challenge_id": feedback.challenge_id,
                "learner_id": feedback.learner_id,
                "perceived_difficulty": feedback.perceived_difficulty,
                "actual_difficulty": feedback.actual_difficulty,
                "completion_time": feedback.completion_time,
                "success_rate": feedback.success_rate,
                "feedback_text": feedback.feedback_text,
                "submitted_at": feedback.submitted_at
            }
            
            result = await self.difficulty_feedback.insert_one(feedback_doc)
            logger.info(f"Stored difficulty feedback for challenge {feedback.challenge_id}")
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing difficulty feedback: {str(e)}")
            raise
    
    async def store_recommendation_history(
        self,
        learner_id: str,
        recommendations: List[AdaptiveRecommendation],
        context: Dict[str, Any]
    ) -> bool:
        """Store recommendation history for analysis."""
        try:
            history_doc = {
                "learner_id": ObjectId(learner_id),
                "timestamp": datetime.utcnow(),
                "recommendations": [
                    {
                        "challenge_id": rec.challenge.challenge_id,
                        "recommendation_score": rec.recommendation_score,
                        "optimal_difficulty": rec.optimal_difficulty,
                        "reasoning": rec.reasoning
                    }
                    for rec in recommendations
                ],
                "context": context
            }
            
            result = await self.recommendation_history.insert_one(history_doc)
            return bool(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing recommendation history: {str(e)}")
            raise
    
    async def get_all_competencies(self) -> List[Dict[str, Any]]:
        """Get all available competencies."""
        try:
            cursor = self.competencies.find({})
            competencies = await cursor.to_list(length=None)
            return competencies
            
        except Exception as e:
            logger.error(f"Error retrieving all competencies: {str(e)}")
            raise
    
    async def get_recent_activity_summary(
        self, 
        learner_id: str, 
        days: int = 7
    ) -> Dict[str, Any]:
        """Get summary of recent learner activity."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent activity logs
            cursor = self.learner_activity_logs.find({
                "learner_id": ObjectId(learner_id),
                "timestamp": {"$gte": start_date}
            }).sort("timestamp", -1)
            
            activities = await cursor.to_list(length=None)
            
            # Calculate summary statistics
            total_activities = len(activities)
            successful_activities = sum(1 for a in activities if a["details"].get("success", False))
            total_time = sum(a["details"].get("time_spent", 0) for a in activities)
            avg_score = sum(a["details"].get("score", 0) for a in activities) / max(total_activities, 1)
            
            return {
                "period_days": days,
                "total_activities": total_activities,
                "successful_activities": successful_activities,
                "success_rate": successful_activities / max(total_activities, 1),
                "total_time_minutes": total_time,
                "average_score": avg_score,
                "activities_per_day": total_activities / days
            }
            
        except Exception as e:
            logger.error(f"Error retrieving recent activity summary: {str(e)}")
            raise
    
    async def _is_challenge_completed(self, learner_id: str, challenge_id: str) -> bool:
        """Check if a challenge has been completed by the learner."""
        try:
            # Check in progress collection
            progress = await self.learner_progress.find_one({
                "learner_id": ObjectId(learner_id),
                "content_item_id": ObjectId(challenge_id),
                "status": "completed"
            })
            
            return progress is not None
            
        except Exception as e:
            logger.error(f"Error checking challenge completion: {str(e)}")
            return False
    
    async def get_learner_performance_trends(
        self, 
        learner_id: str, 
        competency_id: str = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance trends for analysis."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query_filter = {
                "learner_id": ObjectId(learner_id),
                "timestamp": {"$gte": start_date}
            }
            
            if competency_id:
                query_filter["details.competencies_addressed"] = ObjectId(competency_id)
            
            cursor = self.learner_activity_logs.find(query_filter).sort("timestamp", 1)
            activities = await cursor.to_list(length=None)
            
            # Group by day and calculate daily performance
            daily_performance = {}
            for activity in activities:
                day = activity["timestamp"].date()
                if day not in daily_performance:
                    daily_performance[day] = {
                        "date": day,
                        "activities": 0,
                        "successes": 0,
                        "total_score": 0,
                        "total_time": 0
                    }
                
                daily_performance[day]["activities"] += 1
                if activity["details"].get("success", False):
                    daily_performance[day]["successes"] += 1
                daily_performance[day]["total_score"] += activity["details"].get("score", 0)
                daily_performance[day]["total_time"] += activity["details"].get("time_spent", 0)
            
            # Calculate averages
            trends = []
            for day_data in daily_performance.values():
                trends.append({
                    "date": day_data["date"].isoformat(),
                    "activities": day_data["activities"],
                    "success_rate": day_data["successes"] / max(day_data["activities"], 1),
                    "average_score": day_data["total_score"] / max(day_data["activities"], 1),
                    "total_time": day_data["total_time"]
                })
            
            return sorted(trends, key=lambda x: x["date"])
            
        except Exception as e:
            logger.error(f"Error retrieving performance trends: {str(e)}")
            raise
    
    async def get_competency_correlations(self, learner_id: str) -> Dict[str, Any]:
        """Get correlations between competency performance."""
        try:
            # This would implement correlation analysis between competencies
            # For now, return a placeholder
            return {
                "message": "Competency correlation analysis not yet implemented",
                "learner_id": learner_id
            }
            
        except Exception as e:
            logger.error(f"Error calculating competency correlations: {str(e)}")
            raise