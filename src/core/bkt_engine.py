"""
BKT (Bayesian Knowledge Tracing) Engine

This module implements the core BKT algorithm for tracking learner competency
and mastery levels with real-time updates and performance optimization.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
# import numpy as np  # Not needed for core BKT calculations

from ..models.bkt_models import (
    BKTParameters, LearnerCompetency, PerformanceEvent, 
    BKTUpdateResult, BKTConfiguration
)
from ..db.bkt_repository import BKTRepository
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class BKTEngine:
    """
    Core BKT algorithm implementation with real-time updates and performance optimization.
    
    The engine implements the standard 4-parameter BKT model:
    - P(L0): Initial probability of knowing the skill
    - P(T): Probability of learning (transition from not-knowing to knowing)
    - P(G): Probability of guessing correctly when not knowing
    - P(S): Probability of slipping (getting wrong when knowing)
    """
    
    def __init__(
        self, 
        repository: BKTRepository,
        cache_manager: CacheManager,
        config: BKTConfiguration,
        max_workers: int = 10
    ):
        self.repository = repository
        self.cache = cache_manager
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._skill_parameters: Dict[str, BKTParameters] = {}
        
    async def initialize(self):
        """Initialize the BKT engine by loading skill parameters"""
        try:
            # Load all skill parameters from database
            parameters = await self.repository.get_all_skill_parameters()
            self._skill_parameters = {p.skill_id: p for p in parameters}
            logger.info(f"Initialized BKT engine with {len(self._skill_parameters)} skills")
        except Exception as e:
            logger.error(f"Failed to initialize BKT engine: {e}")
            raise
    
    async def update_competency(
        self, 
        learner_id: str, 
        skill_id: str, 
        is_correct: bool,
        activity_id: str,
        response_time: Optional[float] = None,
        confidence_level: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> BKTUpdateResult:
        """
        Update learner competency based on a performance event using BKT algorithm.
        
        Args:
            learner_id: Unique identifier for the learner
            skill_id: Unique identifier for the skill
            is_correct: Whether the learner's response was correct
            activity_id: Unique identifier for the learning activity
            response_time: Time taken to respond (optional)
            confidence_level: Self-reported confidence (optional)
            metadata: Additional event metadata (optional)
            
        Returns:
            BKTUpdateResult with update details
        """
        try:
            # Get skill parameters
            parameters = await self._get_skill_parameters(skill_id)
            
            # Get current competency
            competency = await self._get_learner_competency(learner_id, skill_id)
            
            # Record performance event
            event = PerformanceEvent(
                learner_id=learner_id,
                skill_id=skill_id,
                activity_id=activity_id,
                is_correct=is_correct,
                response_time=response_time,
                confidence_level=confidence_level,
                metadata=metadata or {}
            )
            await self.repository.save_performance_event(event)
            
            # Calculate new P(Known) using BKT update rules
            previous_p_known = competency.p_known
            new_p_known = self._calculate_bkt_update(
                previous_p_known, is_correct, parameters
            )
            
            # Update competency
            competency.p_known = new_p_known
            competency.total_attempts += 1
            if is_correct:
                competency.correct_attempts += 1
            competency.last_updated = datetime.utcnow()
            
            # Check for mastery
            was_mastered = competency.is_mastered
            competency.is_mastered = self._check_mastery(competency)
            mastery_gained = competency.is_mastered and not was_mastered
            
            # Save updated competency
            await self.repository.save_competency(competency)
            
            # Update cache
            cache_key = f"competency:{learner_id}:{skill_id}"
            await self.cache.set(cache_key, competency, ttl=self.config.cache_ttl_seconds)
            
            # Create result
            result = BKTUpdateResult(
                learner_id=learner_id,
                skill_id=skill_id,
                previous_p_known=previous_p_known,
                new_p_known=new_p_known,
                is_mastered=competency.is_mastered,
                mastery_gained=mastery_gained
            )
            
            logger.info(
                f"Updated competency for learner {learner_id}, skill {skill_id}: "
                f"{previous_p_known:.3f} -> {new_p_known:.3f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to update competency: {e}")
            raise
    
    async def batch_update_competencies(
        self, 
        events: List[PerformanceEvent]
    ) -> List[BKTUpdateResult]:
        """
        Batch update multiple competencies for performance optimization.
        
        Args:
            events: List of performance events to process
            
        Returns:
            List of BKTUpdateResult objects
        """
        try:
            # Group events by learner and skill for efficient processing
            grouped_events = self._group_events(events)
            
            # Process updates in batches
            results = []
            batch_size = self.config.update_batch_size
            
            for i in range(0, len(grouped_events), batch_size):
                batch = grouped_events[i:i + batch_size]
                batch_results = await self._process_event_batch(batch)
                results.extend(batch_results)
            
            logger.info(f"Batch updated {len(events)} events, {len(results)} competencies")
            return results
            
        except Exception as e:
            logger.error(f"Failed to batch update competencies: {e}")
            raise
    
    async def get_learner_competencies(
        self, 
        learner_id: str, 
        skill_ids: Optional[List[str]] = None
    ) -> Dict[str, LearnerCompetency]:
        """
        Get current competencies for a learner.
        
        Args:
            learner_id: Unique identifier for the learner
            skill_ids: Optional list of specific skills to retrieve
            
        Returns:
            Dictionary mapping skill IDs to competency objects
        """
        try:
            # Try cache first
            if skill_ids:
                competencies = {}
                for skill_id in skill_ids:
                    cache_key = f"competency:{learner_id}:{skill_id}"
                    cached = await self.cache.get(cache_key)
                    if cached:
                        competencies[skill_id] = cached
                    else:
                        comp = await self._get_learner_competency(learner_id, skill_id)
                        competencies[skill_id] = comp
                        await self.cache.set(cache_key, comp, ttl=self.config.cache_ttl_seconds)
            else:
                # Get all competencies for learner
                competencies_list = await self.repository.get_learner_competencies(learner_id)
                competencies = {comp.skill_id: comp for comp in competencies_list}
            
            return competencies
            
        except Exception as e:
            logger.error(f"Failed to get learner competencies: {e}")
            raise
    
    async def predict_performance(
        self, 
        learner_id: str, 
        skill_id: str
    ) -> Tuple[float, float]:
        """
        Predict the probability of correct response for a learner on a skill.
        
        Args:
            learner_id: Unique identifier for the learner
            skill_id: Unique identifier for the skill
            
        Returns:
            Tuple of (probability_correct, confidence_interval)
        """
        try:
            competency = await self._get_learner_competency(learner_id, skill_id)
            parameters = await self._get_skill_parameters(skill_id)
            
            # P(Correct) = P(Known) * (1 - P(Slip)) + (1 - P(Known)) * P(Guess)
            p_correct = (
                competency.p_known * (1 - parameters.p_s) + 
                (1 - competency.p_known) * parameters.p_g
            )
            
            # Simple confidence interval based on number of attempts
            confidence = min(0.95, 0.5 + (competency.total_attempts * 0.05))
            
            return p_correct, confidence
            
        except Exception as e:
            logger.error(f"Failed to predict performance: {e}")
            raise
    
    async def get_mastery_status(
        self, 
        learner_id: str, 
        skill_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Get mastery status for learner's skills.
        
        Args:
            learner_id: Unique identifier for the learner
            skill_ids: Optional list of specific skills to check
            
        Returns:
            Dictionary mapping skill IDs to mastery status
        """
        try:
            competencies = await self.get_learner_competencies(learner_id, skill_ids)
            return {skill_id: comp.is_mastered for skill_id, comp in competencies.items()}
            
        except Exception as e:
            logger.error(f"Failed to get mastery status: {e}")
            raise
    
    def _calculate_bkt_update(
        self, 
        p_known_prev: float, 
        is_correct: bool, 
        parameters: BKTParameters
    ) -> float:
        """
        Calculate updated P(Known) using BKT update rules.
        
        Args:
            p_known_prev: Previous probability of knowing the skill
            is_correct: Whether the response was correct
            parameters: BKT parameters for the skill
            
        Returns:
            Updated probability of knowing the skill
        """
        if is_correct:
            # Correct response: update using Bayes' rule
            # P(Known|Correct) = P(Known) * (1-P(Slip)) / P(Correct)
            p_correct = p_known_prev * (1 - parameters.p_s) + (1 - p_known_prev) * parameters.p_g
            if p_correct > 0:
                p_known_new = (p_known_prev * (1 - parameters.p_s)) / p_correct
            else:
                p_known_new = p_known_prev
        else:
            # Incorrect response: update using Bayes' rule
            # P(Known|Incorrect) = P(Known) * P(Slip) / P(Incorrect)
            p_incorrect = p_known_prev * parameters.p_s + (1 - p_known_prev) * (1 - parameters.p_g)
            if p_incorrect > 0:
                p_known_new = (p_known_prev * parameters.p_s) / p_incorrect
            else:
                p_known_new = p_known_prev
        
        # Apply learning: P(Known_final) = P(Known_new) + (1 - P(Known_new)) * P(Transit)
        p_known_final = p_known_new + (1 - p_known_new) * parameters.p_t
        
        # Ensure probability bounds
        return max(0.0, min(1.0, p_known_final))
    
    def _check_mastery(self, competency: LearnerCompetency) -> bool:
        """
        Check if a skill is considered mastered based on competency and configuration.
        
        Args:
            competency: Learner competency object
            
        Returns:
            True if skill is mastered, False otherwise
        """
        return (
            competency.p_known >= competency.mastery_threshold and
            competency.total_attempts >= self.config.min_attempts_for_mastery
        )
    
    async def _get_skill_parameters(self, skill_id: str) -> BKTParameters:
        """Get BKT parameters for a skill, using defaults if not found"""
        if skill_id not in self._skill_parameters:
            # Try to load from database
            parameters = await self.repository.get_skill_parameters(skill_id)
            if parameters:
                self._skill_parameters[skill_id] = parameters
            else:
                # Use default parameters
                parameters = BKTParameters(skill_id=skill_id, **self.config.default_parameters.dict())
                self._skill_parameters[skill_id] = parameters
                # Save default parameters to database
                await self.repository.save_skill_parameters(parameters)
        
        return self._skill_parameters[skill_id]
    
    async def _get_learner_competency(self, learner_id: str, skill_id: str) -> LearnerCompetency:
        """Get or create learner competency for a skill"""
        # Try cache first
        cache_key = f"competency:{learner_id}:{skill_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Try database
        competency = await self.repository.get_competency(learner_id, skill_id)
        if not competency:
            # Create new competency with initial parameters
            parameters = await self._get_skill_parameters(skill_id)
            competency = LearnerCompetency(
                learner_id=learner_id,
                skill_id=skill_id,
                p_known=parameters.p_l0,
                mastery_threshold=self.config.mastery_threshold
            )
            await self.repository.save_competency(competency)
        
        # Cache the result
        await self.cache.set(cache_key, competency, ttl=self.config.cache_ttl_seconds)
        return competency
    
    def _group_events(self, events: List[PerformanceEvent]) -> List[List[PerformanceEvent]]:
        """Group events by learner and skill for efficient batch processing"""
        grouped = {}
        for event in events:
            key = (event.learner_id, event.skill_id)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(event)
        
        return list(grouped.values())
    
    async def _process_event_batch(self, event_groups: List[List[PerformanceEvent]]) -> List[BKTUpdateResult]:
        """Process a batch of grouped events concurrently"""
        tasks = []
        for events in event_groups:
            # Process events for the same learner/skill sequentially
            task = self._process_sequential_events(events)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and flatten results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
            else:
                valid_results.extend(result)
        
        return valid_results
    
    async def _process_sequential_events(self, events: List[PerformanceEvent]) -> List[BKTUpdateResult]:
        """Process events for the same learner/skill in chronological order"""
        if not events:
            return []
        
        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        results = []
        for event in events:
            try:
                result = await self.update_competency(
                    learner_id=event.learner_id,
                    skill_id=event.skill_id,
                    is_correct=event.is_correct,
                    activity_id=event.activity_id,
                    response_time=event.response_time,
                    confidence_level=event.confidence_level,
                    metadata=event.metadata
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process event {event.id}: {e}")
        
        return results