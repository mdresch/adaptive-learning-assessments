#!/usr/bin/env python3
"""
Sample data generator for testing the mastery tracking system.

This script generates realistic sample data including learner interactions
and initial mastery levels for testing and demonstration purposes.
"""

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta
from typing import List
import uuid

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from motor.motor_asyncio import AsyncIOMotorClient
from src.models.mastery import (
    LearnerInteraction,
    MasteryLevel,
    MicroCompetency,
    ActivityType,
    InteractionType,
    DifficultyLevel,
    BKTParameters
)
from src.db.mastery_repository import MasteryRepository
from src.core.bkt_engine import BKTEngine


class SampleDataGenerator:
    """Generates realistic sample data for testing."""
    
    def __init__(self, repository: MasteryRepository, bkt_engine: BKTEngine):
        self.repository = repository
        self.bkt_engine = bkt_engine
        
        # Sample learner IDs
        self.learner_ids = [f"learner_{i:03d}" for i in range(1, 21)]  # 20 learners
        
        # Sample activity IDs
        self.activity_ids = [f"activity_{i:03d}" for i in range(1, 101)]  # 100 activities
        
        # Competency IDs (these should match the ones in init-mongo.js)
        self.competency_ids = [
            'arrays_basic',
            'arrays_traversal',
            'sorting_bubble',
            'binary_search',
            'linked_lists_basic'
        ]
    
    async def generate_sample_data(self, num_interactions: int = 500):
        """Generate comprehensive sample data."""
        print(f"Generating {num_interactions} sample interactions...")
        
        # Generate interactions
        interactions = await self.generate_interactions(num_interactions)
        print(f"Generated {len(interactions)} interactions")
        
        # Process interactions to update mastery levels
        await self.process_interactions(interactions)
        print("Processed all interactions and updated mastery levels")
        
        # Generate some additional mastery levels for learners without interactions
        await self.generate_initial_mastery_levels()
        print("Generated initial mastery levels")
        
        print("Sample data generation complete!")
    
    async def generate_interactions(self, num_interactions: int) -> List[LearnerInteraction]:
        """Generate realistic learner interactions."""
        interactions = []
        
        for i in range(num_interactions):
            # Random learner and activity
            learner_id = random.choice(self.learner_ids)
            activity_id = random.choice(self.activity_ids)
            
            # Random competencies (1-3 per interaction)
            num_competencies = random.randint(1, 3)
            competency_ids = random.sample(self.competency_ids, num_competencies)
            
            # Random activity type
            activity_type = random.choice(list(ActivityType))
            interaction_type = random.choice(list(InteractionType))
            
            # Generate realistic performance data
            # Simulate learning progression - later interactions tend to be better
            base_performance = min(0.9, 0.3 + (i / num_interactions) * 0.6)
            noise = random.uniform(-0.2, 0.2)
            score = max(0.0, min(1.0, base_performance + noise))
            
            is_correct = score >= 0.7
            attempts = random.randint(1, 3) if not is_correct else 1
            time_spent = random.uniform(30, 600)  # 30 seconds to 10 minutes
            hints_used = random.randint(0, 3) if score < 0.6 else 0
            
            # Random timestamps over the last 30 days
            days_ago = random.uniform(0, 30)
            completed_at = datetime.utcnow() - timedelta(days=days_ago)
            started_at = completed_at - timedelta(seconds=time_spent)
            
            interaction = LearnerInteraction(
                learner_id=learner_id,
                activity_id=activity_id,
                activity_type=activity_type,
                interaction_type=interaction_type,
                competency_ids=competency_ids,
                score=score,
                is_correct=is_correct,
                attempts=attempts,
                time_spent=time_spent,
                hints_used=hints_used,
                difficulty_level=random.choice(list(DifficultyLevel)),
                session_id=f"session_{uuid.uuid4().hex[:8]}",
                metadata={
                    "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                    "device": random.choice(["desktop", "tablet", "mobile"])
                },
                started_at=started_at,
                completed_at=completed_at
            )
            
            interactions.append(interaction)
        
        # Sort by completion time to simulate realistic progression
        interactions.sort(key=lambda x: x.completed_at)
        
        return interactions
    
    async def process_interactions(self, interactions: List[LearnerInteraction]):
        """Process interactions and update mastery levels."""
        mastery_cache = {}  # Cache mastery levels to avoid repeated DB queries
        
        for interaction in interactions:
            # Save the interaction
            await self.repository.save_interaction(interaction)
            
            # Update mastery for each competency
            for competency_id in interaction.competency_ids:
                cache_key = (interaction.learner_id, competency_id)
                
                # Get or create mastery level
                if cache_key not in mastery_cache:
                    mastery_level = await self.repository.get_mastery_level(
                        interaction.learner_id, 
                        competency_id
                    )
                    
                    if mastery_level is None:
                        mastery_level = await self.repository.create_initial_mastery_level(
                            interaction.learner_id, 
                            competency_id
                        )
                    
                    mastery_cache[cache_key] = mastery_level
                
                # Update mastery using BKT
                current_mastery = mastery_cache[cache_key]
                updated_mastery = self.bkt_engine.update_mastery(current_mastery, interaction)
                
                # Save updated mastery
                await self.repository.save_mastery_level(updated_mastery)
                mastery_cache[cache_key] = updated_mastery
    
    async def generate_initial_mastery_levels(self):
        """Generate initial mastery levels for learners without interactions."""
        for learner_id in self.learner_ids:
            for competency_id in self.competency_ids:
                # Check if mastery level already exists
                existing = await self.repository.get_mastery_level(learner_id, competency_id)
                
                if existing is None:
                    # Create initial mastery level with some variation
                    initial_mastery = random.uniform(0.05, 0.25)
                    
                    mastery_level = MasteryLevel(
                        learner_id=learner_id,
                        competency_id=competency_id,
                        current_mastery=initial_mastery,
                        bkt_parameters=BKTParameters(
                            prior_knowledge=initial_mastery,
                            learning_rate=random.uniform(0.2, 0.4),
                            slip_probability=random.uniform(0.05, 0.15),
                            guess_probability=random.uniform(0.2, 0.3)
                        )
                    )
                    
                    await self.repository.save_mastery_level(mastery_level)


async def main():
    """Main function to run the sample data generator."""
    # Get MongoDB connection string
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DATABASE", "adaptive_learning")
    
    # Connect to database
    client = AsyncIOMotorClient(mongodb_uri)
    database = client[database_name]
    
    # Create repository and engine
    repository = MasteryRepository(database)
    bkt_engine = BKTEngine()
    
    # Ensure indexes are created
    await repository.create_indexes()
    
    # Generate sample data
    generator = SampleDataGenerator(repository, bkt_engine)
    await generator.generate_sample_data(num_interactions=1000)
    
    # Close connection
    client.close()
    print("Sample data generation completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())