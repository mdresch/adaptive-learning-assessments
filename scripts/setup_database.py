#!/usr/bin/env python3
"""
Database setup script for the Adaptive Learning System.

This script initializes the MongoDB database with required collections,
indexes, and sample data for development and testing.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.db.mongodb_client import MongoDBClient
from src.models.competency import Competency, CompetencyType, DifficultyLevel
from src.models.performance import LearningActivity, ActivityType
from src.models.bkt_models import BKTParameters


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_database():
    """Set up the database with collections, indexes, and sample data."""
    try:
        # Initialize database client
        db_client = MongoDBClient()
        
        if not await db_client.connect():
            logger.error("Failed to connect to database")
            return False
        
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        logger.info("Creating database indexes...")
        await db_client.create_indexes()
        
        # Insert sample competencies
        logger.info("Inserting sample competencies...")
        await insert_sample_competencies(db_client)
        
        # Insert sample activities
        logger.info("Inserting sample activities...")
        await insert_sample_activities(db_client)
        
        # Insert default BKT parameters
        logger.info("Inserting default BKT parameters...")
        await insert_default_bkt_parameters(db_client)
        
        # Get database stats
        stats = await db_client.get_database_stats()
        logger.info(f"Database setup complete. Collections: {stats['collection_counts']}")
        
        await db_client.disconnect()
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False


async def insert_sample_competencies(db_client: MongoDBClient):
    """Insert sample competencies for development and testing."""
    competencies_collection = db_client.get_collection("competencies")
    
    sample_competencies = [
        {
            "competency_id": "arrays_basic",
            "name": "Basic Array Operations",
            "description": "Understanding array creation, access, and basic operations",
            "category": "data_structures",
            "subcategory": "arrays",
            "competency_type": CompetencyType.SKILL,
            "difficulty_level": DifficultyLevel.BEGINNER,
            "learning_objectives": [
                "Create arrays in programming language",
                "Access array elements by index",
                "Perform basic array operations (insert, delete, search)"
            ],
            "assessment_criteria": [
                "Can create arrays correctly",
                "Can access elements without errors",
                "Can perform basic operations efficiently"
            ],
            "prerequisites": [],
            "related_competencies": ["arrays_advanced", "loops_basic"],
            "tags": ["arrays", "data-structures", "beginner"],
            "estimated_hours": 2.5,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "competency_id": "arrays_advanced",
            "name": "Advanced Array Algorithms",
            "description": "Complex array algorithms and optimization techniques",
            "category": "data_structures",
            "subcategory": "arrays",
            "competency_type": CompetencyType.SKILL,
            "difficulty_level": DifficultyLevel.INTERMEDIATE,
            "learning_objectives": [
                "Implement sorting algorithms on arrays",
                "Solve two-pointer problems",
                "Optimize array operations for performance"
            ],
            "assessment_criteria": [
                "Can implement efficient sorting algorithms",
                "Can solve complex array problems",
                "Understands time and space complexity"
            ],
            "prerequisites": ["arrays_basic", "algorithms_basic"],
            "related_competencies": ["sorting_algorithms", "complexity_analysis"],
            "tags": ["arrays", "algorithms", "intermediate"],
            "estimated_hours": 5.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "competency_id": "linked_lists_basic",
            "name": "Basic Linked Lists",
            "description": "Understanding linked list structure and basic operations",
            "category": "data_structures",
            "subcategory": "linked_lists",
            "competency_type": CompetencyType.CONCEPT,
            "difficulty_level": DifficultyLevel.BEGINNER,
            "learning_objectives": [
                "Understand linked list structure",
                "Implement basic linked list operations",
                "Compare arrays vs linked lists"
            ],
            "assessment_criteria": [
                "Can explain linked list structure",
                "Can implement insertion and deletion",
                "Understands trade-offs vs arrays"
            ],
            "prerequisites": ["pointers_basic"],
            "related_competencies": ["arrays_basic", "memory_management"],
            "tags": ["linked-lists", "data-structures", "pointers"],
            "estimated_hours": 3.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "competency_id": "recursion_basic",
            "name": "Basic Recursion",
            "description": "Understanding recursive thinking and basic recursive algorithms",
            "category": "algorithms",
            "subcategory": "recursion",
            "competency_type": CompetencyType.CONCEPT,
            "difficulty_level": DifficultyLevel.INTERMEDIATE,
            "learning_objectives": [
                "Understand recursive problem solving",
                "Implement basic recursive functions",
                "Analyze recursive complexity"
            ],
            "assessment_criteria": [
                "Can identify recursive problems",
                "Can implement base cases correctly",
                "Understands call stack behavior"
            ],
            "prerequisites": ["functions_basic"],
            "related_competencies": ["dynamic_programming", "tree_traversal"],
            "tags": ["recursion", "algorithms", "problem-solving"],
            "estimated_hours": 4.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "competency_id": "sorting_algorithms",
            "name": "Sorting Algorithms",
            "description": "Implementation and analysis of various sorting algorithms",
            "category": "algorithms",
            "subcategory": "sorting",
            "competency_type": CompetencyType.SKILL,
            "difficulty_level": DifficultyLevel.INTERMEDIATE,
            "learning_objectives": [
                "Implement bubble, selection, insertion sort",
                "Implement merge sort and quicksort",
                "Compare algorithm performance"
            ],
            "assessment_criteria": [
                "Can implement multiple sorting algorithms",
                "Understands time/space complexity",
                "Can choose appropriate algorithm for use case"
            ],
            "prerequisites": ["arrays_basic", "complexity_analysis"],
            "related_competencies": ["recursion_basic", "divide_conquer"],
            "tags": ["sorting", "algorithms", "complexity"],
            "estimated_hours": 6.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
    ]
    
    # Insert competencies
    for comp_data in sample_competencies:
        try:
            await competencies_collection.update_one(
                {"competency_id": comp_data["competency_id"]},
                {"$set": comp_data},
                upsert=True
            )
            logger.info(f"Inserted/updated competency: {comp_data['competency_id']}")
        except Exception as e:
            logger.error(f"Failed to insert competency {comp_data['competency_id']}: {e}")


async def insert_sample_activities(db_client: MongoDBClient):
    """Insert sample learning activities."""
    activities_collection = db_client.get_collection("learning_activities")
    
    sample_activities = [
        {
            "activity_id": "arrays_intro_video",
            "name": "Introduction to Arrays",
            "description": "Video tutorial covering array basics and common operations",
            "activity_type": ActivityType.VIDEO,
            "difficulty_level": "beginner",
            "estimated_duration_minutes": 15,
            "content": {
                "video_url": "https://example.com/arrays-intro",
                "transcript_available": True,
                "subtitles": ["en", "es"]
            },
            "target_competencies": ["arrays_basic"],
            "prerequisite_competencies": [],
            "max_score": 100.0,
            "passing_score": 70.0,
            "scoring_method": "completion",
            "adaptive_difficulty": False,
            "hints_available": False,
            "tags": ["video", "introduction", "arrays"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "activity_id": "arrays_basic_quiz",
            "name": "Arrays Basic Knowledge Quiz",
            "description": "Quiz testing fundamental array concepts and operations",
            "activity_type": ActivityType.QUIZ,
            "difficulty_level": "beginner",
            "estimated_duration_minutes": 20,
            "content": {
                "question_count": 10,
                "question_types": ["multiple_choice", "true_false"],
                "randomize_questions": True
            },
            "questions": [
                {
                    "question_id": "q1",
                    "text": "What is the time complexity of accessing an element in an array by index?",
                    "type": "multiple_choice",
                    "options": ["O(1)", "O(n)", "O(log n)", "O(n²)"],
                    "correct_answer": "O(1)",
                    "explanation": "Array access by index is constant time O(1) operation."
                }
            ],
            "target_competencies": ["arrays_basic"],
            "prerequisite_competencies": [],
            "max_score": 100.0,
            "passing_score": 70.0,
            "scoring_method": "percentage",
            "adaptive_difficulty": True,
            "hints_available": True,
            "max_attempts": 3,
            "tags": ["quiz", "assessment", "arrays"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "activity_id": "arrays_coding_challenge",
            "name": "Array Manipulation Challenge",
            "description": "Coding challenge to implement basic array operations",
            "activity_type": ActivityType.CODING_CHALLENGE,
            "difficulty_level": "beginner",
            "estimated_duration_minutes": 30,
            "content": {
                "programming_language": "python",
                "starter_code": "def array_operations(arr):\n    # Implement your solution here\n    pass",
                "test_cases": [
                    {"input": "[1, 2, 3]", "expected_output": "[3, 2, 1]"},
                    {"input": "[5, 1, 9, 3]", "expected_output": "[9, 3, 1, 5]"}
                ]
            },
            "target_competencies": ["arrays_basic"],
            "prerequisite_competencies": [],
            "max_score": 100.0,
            "passing_score": 60.0,
            "scoring_method": "test_cases",
            "adaptive_difficulty": True,
            "hints_available": True,
            "max_attempts": 5,
            "tags": ["coding", "practice", "arrays"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "activity_id": "recursion_interactive",
            "name": "Interactive Recursion Explorer",
            "description": "Interactive exercise to understand recursive function calls",
            "activity_type": ActivityType.INTERACTIVE_EXERCISE,
            "difficulty_level": "intermediate",
            "estimated_duration_minutes": 25,
            "content": {
                "exercise_type": "step_through",
                "visualization": True,
                "interactive_elements": ["call_stack", "variable_tracker"]
            },
            "target_competencies": ["recursion_basic"],
            "prerequisite_competencies": ["functions_basic"],
            "max_score": 100.0,
            "passing_score": 75.0,
            "scoring_method": "completion_quality",
            "adaptive_difficulty": True,
            "hints_available": True,
            "tags": ["interactive", "recursion", "visualization"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
    ]
    
    # Insert activities
    for activity_data in sample_activities:
        try:
            await activities_collection.update_one(
                {"activity_id": activity_data["activity_id"]},
                {"$set": activity_data},
                upsert=True
            )
            logger.info(f"Inserted/updated activity: {activity_data['activity_id']}")
        except Exception as e:
            logger.error(f"Failed to insert activity {activity_data['activity_id']}: {e}")


async def insert_default_bkt_parameters(db_client: MongoDBClient):
    """Insert default BKT parameters for competencies."""
    bkt_params_collection = db_client.get_collection("bkt_parameters")
    
    competency_ids = [
        "arrays_basic", "arrays_advanced", "linked_lists_basic", 
        "recursion_basic", "sorting_algorithms"
    ]
    
    for competency_id in competency_ids:
        bkt_params = {
            "competency_id": competency_id,
            "prior_knowledge": 0.1,
            "learning_rate": 0.3,
            "guess_probability": 0.25,
            "slip_probability": 0.1,
            "parameter_source": "default",
            "confidence_level": 0.5,
            "sample_size": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            await bkt_params_collection.update_one(
                {"competency_id": competency_id},
                {"$set": bkt_params},
                upsert=True
            )
            logger.info(f"Inserted/updated BKT parameters for: {competency_id}")
        except Exception as e:
            logger.error(f"Failed to insert BKT parameters for {competency_id}: {e}")


if __name__ == "__main__":
    success = asyncio.run(setup_database())
    if success:
        logger.info("Database setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("Database setup failed!")
        sys.exit(1)