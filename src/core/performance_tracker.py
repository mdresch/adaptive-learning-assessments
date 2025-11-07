"""
Performance Tracking System for the Adaptive Learning System.

This module handles comprehensive tracking of learner interactions,
performance metrics, and learning analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from collections import defaultdict

from ..models.performance import (
    PerformanceRecord, ActivityResult, LearningSession,
    InteractionType, ActivityStatus, ActivityType
)
from ..models.competency import LearnerCompetency, CompetencyLevel
from ..models.bkt_models import BKTState, CompetencyUpdate


logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    Comprehensive performance tracking and analytics system.
    
    Tracks learner interactions, calculates performance metrics,
    and provides insights for adaptive learning algorithms.
    """
    
    def __init__(self, db_client=None, bkt_engine=None):
        """
        Initialize the performance tracker.
        
        Args:
            db_client: Database client for persistence (optional)
            bkt_engine: BKT engine for competency updates (optional)
        """
        self.db_client = db_client
        self.bkt_engine = bkt_engine
        self.logger = logger
        
        # Performance calculation parameters
        self.session_timeout_minutes = 30
        self.mastery_threshold = 0.8
        self.improvement_window_days = 7
        
        # Analytics cache
        self._analytics_cache = {}
        self._cache_timeout = timedelta(minutes=15)
    
    async def record_interaction(
        self,
        learner_id: str,
        activity_id: str,
        interaction_type: InteractionType,
        session_id: str,
        competency_id: Optional[str] = None,
        question_id: Optional[str] = None,
        response: Optional[Any] = None,
        is_correct: Optional[bool] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> PerformanceRecord:
        """
        Record a learner interaction.
        
        Args:
            learner_id: Learner identifier
            activity_id: Activity identifier
            interaction_type: Type of interaction
            session_id: Learning session identifier
            competency_id: Related competency (optional)
            question_id: Specific question ID (optional)
            response: Learner response (optional)
            is_correct: Whether response was correct (optional)
            data: Additional interaction data (optional)
            
        Returns:
            Created PerformanceRecord
        """
        try:
            # Create performance record
            record = PerformanceRecord(
                record_id=str(uuid4()),
                learner_id=learner_id,
                activity_id=activity_id,
                interaction_type=interaction_type,
                session_id=session_id,
                competency_id=competency_id,
                question_id=question_id,
                response=response,
                is_correct=is_correct,
                data=data or {}
            )
            
            # Calculate time since session start
            session_start = await self._get_session_start_time(session_id)
            if session_start:
                record.time_since_start = (record.timestamp - session_start).total_seconds() / 60
            
            # Get BKT state before interaction (if applicable)
            if competency_id and self.bkt_engine:
                bkt_state = await self.bkt_engine.get_bkt_state(learner_id, competency_id)
                record.bkt_state_before = {
                    "mastery_probability": bkt_state.mastery_probability,
                    "evidence_count": bkt_state.evidence_count
                }
            
            # Save to database
            if self.db_client:
                try:
                    # This would be implemented with actual database save
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to save performance record: {e}")
            
            # Update BKT if this is a response with correctness
            if (competency_id and is_correct is not None and 
                self.bkt_engine and interaction_type == InteractionType.SUBMIT_ANSWER):
                
                try:
                    update = await self.bkt_engine.update_mastery(
                        learner_id=learner_id,
                        competency_id=competency_id,
                        is_correct=is_correct,
                        activity_id=activity_id,
                        session_id=session_id,
                        question_id=question_id
                    )
                    
                    # Update BKT state after interaction
                    bkt_state_after = await self.bkt_engine.get_bkt_state(learner_id, competency_id)
                    record.bkt_state_after = {
                        "mastery_probability": bkt_state_after.mastery_probability,
                        "evidence_count": bkt_state_after.evidence_count
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Failed to update BKT: {e}")
            
            # Update session tracking
            await self._update_session_tracking(session_id, learner_id, activity_id, record)
            
            # Clear relevant analytics cache
            self._clear_analytics_cache(learner_id)
            
            self.logger.debug(
                f"Recorded interaction: {learner_id} - {interaction_type} - {activity_id}"
            )
            
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to record interaction: {e}")
            raise
    
    async def record_activity_result(
        self,
        learner_id: str,
        activity_id: str,
        session_id: str,
        status: ActivityStatus,
        score: float,
        max_possible_score: float,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        responses: Optional[List[Dict[str, Any]]] = None,
        competency_updates: Optional[List[Dict[str, Any]]] = None
    ) -> ActivityResult:
        """
        Record the result of a completed activity.
        
        Args:
            learner_id: Learner identifier
            activity_id: Activity identifier
            session_id: Learning session identifier
            status: Completion status
            score: Achieved score
            max_possible_score: Maximum possible score
            start_time: Activity start time
            end_time: Activity end time (optional)
            responses: Individual question responses (optional)
            competency_updates: Competency updates from this activity (optional)
            
        Returns:
            Created ActivityResult
        """
        try:
            # Get attempt number for this activity
            attempt_number = await self._get_next_attempt_number(learner_id, activity_id)
            
            # Create activity result
            result = ActivityResult(
                result_id=str(uuid4()),
                learner_id=learner_id,
                activity_id=activity_id,
                attempt_number=attempt_number,
                status=status,
                score=score,
                max_possible_score=max_possible_score,
                start_time=start_time,
                end_time=end_time or datetime.utcnow(),
                responses=responses or [],
                competency_updates=competency_updates or []
            )
            
            # Calculate derived metrics
            if responses:
                result.total_questions = len(responses)
                result.correct_answers = sum(1 for r in responses if r.get('is_correct', False))
                
                # Calculate time per question
                if result.duration_minutes and result.total_questions > 0:
                    avg_time = result.duration_minutes / result.total_questions
                    result.time_per_question = [avg_time] * result.total_questions  # Simplified
            
            # Save to database
            if self.db_client:
                try:
                    # This would be implemented with actual database save
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to save activity result: {e}")
            
            # Update session tracking
            await self._update_session_with_result(session_id, result)
            
            # Clear analytics cache
            self._clear_analytics_cache(learner_id)
            
            self.logger.info(
                f"Recorded activity result: {learner_id} - {activity_id} - "
                f"Score: {score}/{max_possible_score} ({result.percentage_score:.1f}%)"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to record activity result: {e}")
            raise
    
    async def start_learning_session(
        self,
        learner_id: str,
        session_id: Optional[str] = None
    ) -> LearningSession:
        """
        Start a new learning session.
        
        Args:
            learner_id: Learner identifier
            session_id: Session identifier (optional, will generate if not provided)
            
        Returns:
            Created LearningSession
        """
        try:
            session = LearningSession(
                session_id=session_id or str(uuid4()),
                learner_id=learner_id
            )
            
            # Save to database
            if self.db_client:
                try:
                    # This would be implemented with actual database save
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to save learning session: {e}")
            
            self.logger.info(f"Started learning session: {session.session_id} for {learner_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to start learning session: {e}")
            raise
    
    async def end_learning_session(self, session_id: str) -> Optional[LearningSession]:
        """
        End a learning session and calculate final metrics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Updated LearningSession or None if not found
        """
        try:
            session = await self._get_learning_session(session_id)
            if not session:
                self.logger.warning(f"Session not found: {session_id}")
                return None
            
            # Set end time and calculate duration
            session.end_time = datetime.utcnow()
            if session.start_time:
                duration = session.end_time - session.start_time
                session.duration_minutes = duration.total_seconds() / 60
            
            # Calculate final session metrics
            await self._calculate_session_metrics(session)
            
            # Save updated session
            if self.db_client:
                try:
                    # This would be implemented with actual database save
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to save updated session: {e}")
            
            self.logger.info(
                f"Ended learning session: {session_id} - "
                f"Duration: {session.duration_minutes:.1f} minutes"
            )
            
            return session
            
        except Exception as e:
            self.logger.error(f"Failed to end learning session: {e}")
            raise
    
    async def get_performance_analytics(
        self,
        learner_id: str,
        time_period_days: int = 30,
        competency_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance analytics for a learner.
        
        Args:
            learner_id: Learner identifier
            time_period_days: Analysis time period in days
            competency_id: Specific competency to analyze (optional)
            
        Returns:
            Dictionary with performance analytics
        """
        try:
            # Check cache first
            cache_key = f"{learner_id}_{time_period_days}_{competency_id or 'all'}"
            if cache_key in self._analytics_cache:
                cached_data, timestamp = self._analytics_cache[cache_key]
                if datetime.utcnow() - timestamp < self._cache_timeout:
                    return cached_data
            
            # Calculate analytics
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=time_period_days)
            
            analytics = {
                "learner_id": learner_id,
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_period_days
                },
                "competency_filter": competency_id,
                "overall_performance": {},
                "competency_progress": {},
                "learning_patterns": {},
                "engagement_metrics": {},
                "improvement_trends": {}
            }
            
            # Get performance data
            performance_records = await self._get_performance_records(
                learner_id, start_date, end_date, competency_id
            )
            activity_results = await self._get_activity_results(
                learner_id, start_date, end_date, competency_id
            )
            learning_sessions = await self._get_learning_sessions(
                learner_id, start_date, end_date
            )
            
            # Calculate overall performance metrics
            analytics["overall_performance"] = self._calculate_overall_performance(
                activity_results, learning_sessions
            )
            
            # Calculate competency progress
            analytics["competency_progress"] = await self._calculate_competency_progress(
                learner_id, competency_id
            )
            
            # Analyze learning patterns
            analytics["learning_patterns"] = self._analyze_learning_patterns(
                performance_records, activity_results
            )
            
            # Calculate engagement metrics
            analytics["engagement_metrics"] = self._calculate_engagement_metrics(
                performance_records, learning_sessions
            )
            
            # Calculate improvement trends
            analytics["improvement_trends"] = self._calculate_improvement_trends(
                activity_results, time_period_days
            )
            
            # Cache the results
            self._analytics_cache[cache_key] = (analytics, datetime.utcnow())
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Failed to get performance analytics for {learner_id}: {e}")
            raise
    
    def _calculate_overall_performance(
        self,
        activity_results: List[ActivityResult],
        learning_sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Calculate overall performance metrics."""
        if not activity_results:
            return {"status": "no_data"}
        
        # Basic metrics
        total_activities = len(activity_results)
        completed_activities = len([r for r in activity_results if r.status == ActivityStatus.COMPLETED])
        total_score = sum(r.score for r in activity_results)
        total_possible = sum(r.max_possible_score for r in activity_results)
        
        # Calculate averages
        avg_score = total_score / total_possible if total_possible > 0 else 0
        completion_rate = completed_activities / total_activities if total_activities > 0 else 0
        
        # Time metrics
        total_time = sum(r.duration_minutes or 0 for r in activity_results)
        avg_session_time = sum(s.duration_minutes or 0 for s in learning_sessions) / len(learning_sessions) if learning_sessions else 0
        
        # Recent performance (last 7 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        recent_results = [r for r in activity_results if r.start_time >= recent_cutoff]
        recent_avg = (sum(r.percentage_score for r in recent_results) / len(recent_results)) if recent_results else 0
        
        return {
            "total_activities": total_activities,
            "completed_activities": completed_activities,
            "completion_rate": completion_rate,
            "average_score_percentage": avg_score * 100,
            "total_time_hours": total_time / 60,
            "average_session_time_minutes": avg_session_time,
            "recent_performance_percentage": recent_avg,
            "total_sessions": len(learning_sessions)
        }
    
    async def _calculate_competency_progress(
        self,
        learner_id: str,
        competency_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate competency-specific progress metrics."""
        try:
            # Get competency states
            competency_states = await self._get_learner_competencies(learner_id, competency_filter)
            
            if not competency_states:
                return {"status": "no_competencies"}
            
            # Group by mastery level
            mastery_distribution = {
                "not_started": 0,
                "learning": 0,
                "practicing": 0,
                "mastered": 0
            }
            
            total_mastery = 0
            competency_details = []
            
            for comp in competency_states:
                total_mastery += comp.mastery_probability
                
                # Categorize mastery level
                if comp.mastery_probability < 0.3:
                    mastery_distribution["not_started"] += 1
                    level = "not_started"
                elif comp.mastery_probability < 0.6:
                    mastery_distribution["learning"] += 1
                    level = "learning"
                elif comp.mastery_probability < self.mastery_threshold:
                    mastery_distribution["practicing"] += 1
                    level = "practicing"
                else:
                    mastery_distribution["mastered"] += 1
                    level = "mastered"
                
                competency_details.append({
                    "competency_id": comp.competency_id,
                    "mastery_probability": comp.mastery_probability,
                    "level": level,
                    "attempts": comp.attempts_count,
                    "success_rate": comp.successful_attempts / comp.attempts_count if comp.attempts_count > 0 else 0
                })
            
            avg_mastery = total_mastery / len(competency_states)
            
            return {
                "total_competencies": len(competency_states),
                "average_mastery": avg_mastery,
                "mastery_distribution": mastery_distribution,
                "competency_details": competency_details,
                "mastered_count": mastery_distribution["mastered"],
                "in_progress_count": mastery_distribution["learning"] + mastery_distribution["practicing"]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate competency progress: {e}")
            return {"status": "error", "message": str(e)}
    
    # Additional helper methods would be implemented here...
    
    async def _get_session_start_time(self, session_id: str) -> Optional[datetime]:
        """Get session start time from database."""
        # This would be implemented with actual database query
        return None
    
    async def _get_next_attempt_number(self, learner_id: str, activity_id: str) -> int:
        """Get next attempt number for an activity."""
        # This would be implemented with actual database query
        return 1
    
    async def _get_learning_session(self, session_id: str) -> Optional[LearningSession]:
        """Get learning session from database."""
        # This would be implemented with actual database query
        return None
    
    async def _get_performance_records(
        self, learner_id: str, start_date: datetime, end_date: datetime, competency_id: Optional[str]
    ) -> List[PerformanceRecord]:
        """Get performance records from database."""
        # This would be implemented with actual database query
        return []
    
    async def _get_activity_results(
        self, learner_id: str, start_date: datetime, end_date: datetime, competency_id: Optional[str]
    ) -> List[ActivityResult]:
        """Get activity results from database."""
        # This would be implemented with actual database query
        return []
    
    async def _get_learning_sessions(
        self, learner_id: str, start_date: datetime, end_date: datetime
    ) -> List[LearningSession]:
        """Get learning sessions from database."""
        # This would be implemented with actual database query
        return []
    
    async def _get_learner_competencies(
        self, learner_id: str, competency_filter: Optional[str]
    ) -> List[LearnerCompetency]:
        """Get learner competencies from database."""
        # This would be implemented with actual database query
        return []
    
    def _clear_analytics_cache(self, learner_id: str):
        """Clear analytics cache for a learner."""
        keys_to_remove = [key for key in self._analytics_cache.keys() if key.startswith(learner_id)]
        for key in keys_to_remove:
            del self._analytics_cache[key]