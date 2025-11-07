"""
Bayesian Knowledge Tracing (BKT) Engine implementation.

This module implements the core BKT algorithm for tracking learner competency
and updating mastery probabilities based on performance evidence.
"""

import math
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

from ..models.bkt_models import BKTParameters, BKTState, CompetencyUpdate, BKTDiagnostics
from ..models.competency import LearnerCompetency


logger = logging.getLogger(__name__)


class BKTEngine:
    """
    Bayesian Knowledge Tracing engine for adaptive learning.
    
    Implements the standard BKT model with four parameters:
    - P(L0): Prior knowledge probability
    - P(T): Learning rate (transition probability)
    - P(G): Guess probability
    - P(S): Slip probability
    """
    
    def __init__(self, db_client=None):
        """
        Initialize the BKT engine.
        
        Args:
            db_client: Database client for persistence (optional)
        """
        self.db_client = db_client
        self.logger = logger
        
        # Default BKT parameters
        self.default_parameters = {
            "prior_knowledge": 0.1,
            "learning_rate": 0.3,
            "guess_probability": 0.25,
            "slip_probability": 0.1
        }
        
        # Cache for BKT parameters
        self._parameter_cache = {}
        
    async def get_bkt_parameters(self, competency_id: str) -> BKTParameters:
        """
        Get BKT parameters for a specific competency.
        
        Args:
            competency_id: Competency identifier
            
        Returns:
            BKTParameters object
        """
        # Check cache first
        if competency_id in self._parameter_cache:
            return self._parameter_cache[competency_id]
        
        # Try to load from database
        if self.db_client:
            try:
                # This would be implemented with actual database query
                # For now, return default parameters
                pass
            except Exception as e:
                self.logger.warning(f"Failed to load BKT parameters for {competency_id}: {e}")
        
        # Return default parameters
        parameters = BKTParameters(
            competency_id=competency_id,
            **self.default_parameters
        )
        
        # Cache the parameters
        self._parameter_cache[competency_id] = parameters
        
        return parameters
    
    async def get_bkt_state(self, learner_id: str, competency_id: str) -> BKTState:
        """
        Get current BKT state for a learner-competency pair.
        
        Args:
            learner_id: Learner identifier
            competency_id: Competency identifier
            
        Returns:
            BKTState object
        """
        if self.db_client:
            try:
                # This would be implemented with actual database query
                # For now, create a new state with prior knowledge
                pass
            except Exception as e:
                self.logger.warning(f"Failed to load BKT state for {learner_id}/{competency_id}: {e}")
        
        # Get parameters to initialize with prior knowledge
        parameters = await self.get_bkt_parameters(competency_id)
        
        # Create new state
        state = BKTState(
            learner_id=learner_id,
            competency_id=competency_id,
            mastery_probability=parameters.prior_knowledge,
            evidence_count=0,
            total_attempts=0,
            correct_attempts=0
        )
        
        return state
    
    def calculate_mastery_update(
        self,
        current_mastery: float,
        is_correct: bool,
        parameters: BKTParameters
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate updated mastery probability using BKT.
        
        Args:
            current_mastery: Current mastery probability P(Ln)
            is_correct: Whether the response was correct
            parameters: BKT parameters
            
        Returns:
            Tuple of (new_mastery_probability, calculation_details)
        """
        # Extract parameters
        p_l = current_mastery  # P(Ln) - current mastery probability
        p_t = parameters.learning_rate  # P(T) - learning rate
        p_g = parameters.guess_probability  # P(G) - guess probability
        p_s = parameters.slip_probability  # P(S) - slip probability
        
        # Calculate P(Ln+1 | evidence)
        if is_correct:
            # Correct response: P(Ln+1 | correct) = P(correct | Ln+1) * P(Ln+1) / P(correct)
            
            # P(Ln+1) = P(Ln) + (1 - P(Ln)) * P(T)
            p_l_next = p_l + (1 - p_l) * p_t
            
            # P(correct | Ln+1) = 1 - P(S)
            p_correct_given_learned = 1 - p_s
            
            # P(correct | not Ln+1) = P(G)
            p_correct_given_not_learned = p_g
            
            # P(correct) = P(correct | Ln+1) * P(Ln+1) + P(correct | not Ln+1) * P(not Ln+1)
            p_correct = (p_correct_given_learned * p_l_next + 
                        p_correct_given_not_learned * (1 - p_l_next))
            
            # Avoid division by zero
            if p_correct == 0:
                p_correct = 1e-10
            
            # Updated mastery probability
            new_mastery = (p_correct_given_learned * p_l_next) / p_correct
            
        else:
            # Incorrect response: P(Ln+1 | incorrect) = P(incorrect | Ln+1) * P(Ln+1) / P(incorrect)
            
            # P(Ln+1) = P(Ln) + (1 - P(Ln)) * P(T)
            p_l_next = p_l + (1 - p_l) * p_t
            
            # P(incorrect | Ln+1) = P(S)
            p_incorrect_given_learned = p_s
            
            # P(incorrect | not Ln+1) = 1 - P(G)
            p_incorrect_given_not_learned = 1 - p_g
            
            # P(incorrect) = P(incorrect | Ln+1) * P(Ln+1) + P(incorrect | not Ln+1) * P(not Ln+1)
            p_incorrect = (p_incorrect_given_learned * p_l_next + 
                          p_incorrect_given_not_learned * (1 - p_l_next))
            
            # Avoid division by zero
            if p_incorrect == 0:
                p_incorrect = 1e-10
            
            # Updated mastery probability
            new_mastery = (p_incorrect_given_learned * p_l_next) / p_incorrect
        
        # Ensure probability is within bounds
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        # Calculation details for debugging/logging
        details = {
            "prior_mastery": current_mastery,
            "is_correct": is_correct,
            "parameters": {
                "learning_rate": p_t,
                "guess_probability": p_g,
                "slip_probability": p_s
            },
            "intermediate_calculations": {
                "p_l_next_before_evidence": p_l + (1 - p_l) * p_t,
                "evidence_probability": p_correct if is_correct else p_incorrect
            },
            "posterior_mastery": new_mastery,
            "mastery_change": new_mastery - current_mastery
        }
        
        return new_mastery, details
    
    async def update_mastery(
        self,
        learner_id: str,
        competency_id: str,
        is_correct: bool,
        activity_id: str,
        session_id: str,
        question_id: Optional[str] = None,
        response_time_seconds: Optional[float] = None,
        difficulty_level: Optional[str] = None
    ) -> CompetencyUpdate:
        """
        Update learner mastery probability based on new evidence.
        
        Args:
            learner_id: Learner identifier
            competency_id: Competency identifier
            is_correct: Whether the response was correct
            activity_id: Activity that generated the evidence
            session_id: Learning session identifier
            question_id: Specific question identifier (optional)
            response_time_seconds: Time taken to respond (optional)
            difficulty_level: Question difficulty level (optional)
            
        Returns:
            CompetencyUpdate record
        """
        try:
            # Get current state and parameters
            current_state = await self.get_bkt_state(learner_id, competency_id)
            parameters = await self.get_bkt_parameters(competency_id)
            
            # Calculate updated mastery probability
            new_mastery, calculation_details = self.calculate_mastery_update(
                current_state.mastery_probability,
                is_correct,
                parameters
            )
            
            # Create update record
            update = CompetencyUpdate(
                update_id=str(uuid4()),
                learner_id=learner_id,
                competency_id=competency_id,
                activity_id=activity_id,
                question_id=question_id,
                session_id=session_id,
                is_correct=is_correct,
                response_time_seconds=response_time_seconds,
                difficulty_level=difficulty_level,
                prior_mastery=current_state.mastery_probability,
                posterior_mastery=new_mastery,
                mastery_change=new_mastery - current_state.mastery_probability,
                bkt_parameters={
                    "prior_knowledge": parameters.prior_knowledge,
                    "learning_rate": parameters.learning_rate,
                    "guess_probability": parameters.guess_probability,
                    "slip_probability": parameters.slip_probability
                },
                update_method="standard_bkt",
                confidence_score=1.0  # Could be adjusted based on various factors
            )
            
            # Update the state
            await self._update_bkt_state(current_state, is_correct, new_mastery, update)
            
            # Log the update
            self.logger.info(
                f"BKT update: learner={learner_id}, competency={competency_id}, "
                f"correct={is_correct}, mastery={current_state.mastery_probability:.3f} -> {new_mastery:.3f}"
            )
            
            return update
            
        except Exception as e:
            self.logger.error(f"Failed to update mastery for {learner_id}/{competency_id}: {e}")
            raise
    
    async def _update_bkt_state(
        self,
        state: BKTState,
        is_correct: bool,
        new_mastery: float,
        update: CompetencyUpdate
    ):
        """
        Update the BKT state with new evidence.
        
        Args:
            state: Current BKT state
            is_correct: Whether the response was correct
            new_mastery: New mastery probability
            update: Update record
        """
        # Update counters
        state.total_attempts += 1
        if is_correct:
            state.correct_attempts += 1
        
        # Update mastery probability
        state.mastery_probability = new_mastery
        state.evidence_count += 1
        
        # Update recent performance (keep last 20 attempts)
        state.recent_performance.append(is_correct)
        if len(state.recent_performance) > 20:
            state.recent_performance = state.recent_performance[-20:]
        
        # Add to mastery trajectory
        trajectory_point = {
            "timestamp": update.timestamp.isoformat(),
            "mastery_probability": new_mastery,
            "evidence": is_correct,
            "activity_id": update.activity_id
        }
        state.mastery_trajectory.append(trajectory_point)
        
        # Calculate learning velocity (change over recent attempts)
        if len(state.mastery_trajectory) >= 2:
            recent_change = (state.mastery_trajectory[-1]["mastery_probability"] - 
                           state.mastery_trajectory[-2]["mastery_probability"])
            state.learning_velocity = recent_change
        
        # Update timestamps
        if state.first_attempt is None:
            state.first_attempt = update.timestamp
        state.last_update = update.timestamp
        
        # Check for mastery achievement (threshold could be configurable)
        mastery_threshold = 0.8
        if new_mastery >= mastery_threshold and state.mastery_achieved_at is None:
            state.mastery_achieved_at = update.timestamp
        
        # Update confidence interval (simplified calculation)
        # In a full implementation, this would use more sophisticated methods
        evidence_weight = min(state.evidence_count / 10.0, 1.0)  # More evidence = narrower interval
        interval_width = (1.0 - evidence_weight) * 0.5  # Start wide, narrow with evidence
        
        state.confidence_interval = {
            "lower": max(0.0, new_mastery - interval_width),
            "upper": min(1.0, new_mastery + interval_width)
        }
        
        # Save state to database if available
        if self.db_client:
            try:
                # This would be implemented with actual database save
                pass
            except Exception as e:
                self.logger.warning(f"Failed to save BKT state: {e}")
    
    def predict_performance(
        self,
        mastery_probability: float,
        parameters: BKTParameters,
        difficulty_adjustment: float = 1.0
    ) -> Dict[str, float]:
        """
        Predict performance probability given current mastery.
        
        Args:
            mastery_probability: Current mastery probability
            parameters: BKT parameters
            difficulty_adjustment: Adjustment factor for difficulty (1.0 = normal)
            
        Returns:
            Dictionary with prediction probabilities
        """
        # Adjust slip and guess probabilities based on difficulty
        adjusted_slip = min(1.0, parameters.slip_probability * difficulty_adjustment)
        adjusted_guess = max(0.0, parameters.guess_probability / difficulty_adjustment)
        
        # P(correct) = P(correct | mastered) * P(mastered) + P(correct | not mastered) * P(not mastered)
        p_correct = ((1 - adjusted_slip) * mastery_probability + 
                    adjusted_guess * (1 - mastery_probability))
        
        return {
            "correct_probability": p_correct,
            "incorrect_probability": 1 - p_correct,
            "mastery_probability": mastery_probability,
            "adjusted_slip": adjusted_slip,
            "adjusted_guess": adjusted_guess
        }
    
    async def get_competency_diagnostics(self, competency_id: str) -> Optional[BKTDiagnostics]:
        """
        Get diagnostic information for BKT model performance.
        
        Args:
            competency_id: Competency identifier
            
        Returns:
            BKTDiagnostics object or None if insufficient data
        """
        # This would be implemented with actual data analysis
        # For now, return None indicating insufficient data
        return None
    
    async def fit_parameters(
        self,
        competency_id: str,
        training_data: List[Dict[str, Any]],
        method: str = "em"
    ) -> BKTParameters:
        """
        Fit BKT parameters using training data.
        
        Args:
            competency_id: Competency identifier
            training_data: List of training observations
            method: Fitting method ("em" for Expectation-Maximization)
            
        Returns:
            Fitted BKTParameters
        """
        # This would implement parameter fitting algorithms
        # For now, return default parameters
        self.logger.info(f"Parameter fitting not yet implemented for {competency_id}")
        
        return await self.get_bkt_parameters(competency_id)
    
    def calculate_mastery_confidence(
        self,
        state: BKTState,
        parameters: BKTParameters
    ) -> float:
        """
        Calculate confidence in mastery assessment.
        
        Args:
            state: Current BKT state
            parameters: BKT parameters
            
        Returns:
            Confidence score between 0 and 1
        """
        # Confidence increases with more evidence and consistent performance
        evidence_factor = min(state.evidence_count / 20.0, 1.0)  # Max confidence at 20 attempts
        
        # Consistency factor based on recent performance
        if len(state.recent_performance) >= 3:
            recent_correct = sum(state.recent_performance[-5:])  # Last 5 attempts
            recent_total = len(state.recent_performance[-5:])
            consistency = 1.0 - abs(recent_correct / recent_total - state.mastery_probability)
        else:
            consistency = 0.5  # Neutral confidence with little data
        
        # Combine factors
        confidence = (evidence_factor * 0.6 + consistency * 0.4)
        
        return max(0.1, min(1.0, confidence))  # Keep within reasonable bounds