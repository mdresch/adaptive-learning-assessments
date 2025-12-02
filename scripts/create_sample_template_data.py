"""
Sample Template Analytics Data Generator

This script creates sample template entity profiles and document domain inferences
for testing and demonstration purposes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

from src.db.database import db
from src.db.template_analytics_repository import TemplateAnalyticsRepository
from src.core.domain_inference_engine import DomainInferenceEngine
from src.models.template_analytics import (
    TemplateEntityProfileCreate,
    DocumentDomainInferenceCreate,
    DomainCategory,
    TemplateType,
    DomainAssociation,
    TemplateUsageMetrics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """Generator for sample template analytics data"""

    def __init__(self):
        self.domain_inference_engine = DomainInferenceEngine()

    def generate_sample_templates(self) -> List[TemplateEntityProfileCreate]:
        """Generate sample template entity profiles"""
        templates = [
            # Programming Templates
            TemplateEntityProfileCreate(
                template_id="python_basics_quiz_001",
                template_name="Python Basics Quiz",
                template_type=TemplateType.QUIZ,
                description="A comprehensive quiz covering Python fundamentals including variables, data types, and basic operations.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.PROGRAMMING, confidence=0.95, evidence_count=10)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=150,
                    unique_users=75,
                    completion_rate=0.85,
                    average_score=0.78,
                    average_time_spent=1200,
                    last_used=datetime.utcnow() - timedelta(hours=2)
                ),
                effectiveness_score=0.82,
                tags=["python", "basics", "programming", "quiz"],
                metadata={"difficulty": "beginner", "estimated_time": 20}
            ),
            
            TemplateEntityProfileCreate(
                template_id="javascript_functions_exercise_001",
                template_name="JavaScript Functions Exercise",
                template_type=TemplateType.EXERCISE,
                description="Interactive exercise for learning JavaScript function syntax, parameters, and return values.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.PROGRAMMING, confidence=0.90, evidence_count=8),
                    DomainAssociation(domain=DomainCategory.WEB_DEVELOPMENT, confidence=0.75, evidence_count=5)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=89,
                    unique_users=67,
                    completion_rate=0.92,
                    average_score=0.84,
                    average_time_spent=1800,
                    last_used=datetime.utcnow() - timedelta(hours=5)
                ),
                effectiveness_score=0.88,
                tags=["javascript", "functions", "programming", "web"],
                metadata={"difficulty": "intermediate", "estimated_time": 30}
            ),

            # Data Structures Templates
            TemplateEntityProfileCreate(
                template_id="binary_trees_lesson_001",
                template_name="Binary Trees Fundamentals",
                template_type=TemplateType.LESSON,
                description="Comprehensive lesson on binary tree data structures, including traversal algorithms and implementation.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.DATA_STRUCTURES, confidence=0.95, evidence_count=12),
                    DomainAssociation(domain=DomainCategory.ALGORITHMS, confidence=0.80, evidence_count=6)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=234,
                    unique_users=156,
                    completion_rate=0.76,
                    average_score=0.71,
                    average_time_spent=2400,
                    last_used=datetime.utcnow() - timedelta(hours=1)
                ),
                effectiveness_score=0.74,
                tags=["binary-trees", "data-structures", "algorithms", "trees"],
                metadata={"difficulty": "intermediate", "estimated_time": 40}
            ),

            TemplateEntityProfileCreate(
                template_id="array_sorting_quiz_001",
                template_name="Array Sorting Algorithms Quiz",
                template_type=TemplateType.QUIZ,
                description="Quiz covering various array sorting algorithms including bubble sort, merge sort, and quicksort.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.ALGORITHMS, confidence=0.92, evidence_count=15),
                    DomainAssociation(domain=DomainCategory.DATA_STRUCTURES, confidence=0.85, evidence_count=8)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=178,
                    unique_users=134,
                    completion_rate=0.68,
                    average_score=0.65,
                    average_time_spent=1500,
                    last_used=datetime.utcnow() - timedelta(hours=3)
                ),
                effectiveness_score=0.67,
                tags=["sorting", "algorithms", "arrays", "complexity"],
                metadata={"difficulty": "advanced", "estimated_time": 25}
            ),

            # Web Development Templates
            TemplateEntityProfileCreate(
                template_id="html_css_basics_001",
                template_name="HTML & CSS Fundamentals",
                template_type=TemplateType.INTERACTIVE,
                description="Interactive tutorial covering HTML structure and CSS styling basics for web development.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.WEB_DEVELOPMENT, confidence=0.98, evidence_count=20)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=312,
                    unique_users=298,
                    completion_rate=0.94,
                    average_score=0.89,
                    average_time_spent=3600,
                    last_used=datetime.utcnow() - timedelta(minutes=30)
                ),
                effectiveness_score=0.91,
                tags=["html", "css", "web-development", "frontend"],
                metadata={"difficulty": "beginner", "estimated_time": 60}
            ),

            # Database Templates
            TemplateEntityProfileCreate(
                template_id="sql_queries_exercise_001",
                template_name="SQL Query Practice",
                template_type=TemplateType.EXERCISE,
                description="Hands-on exercise for practicing SQL SELECT, JOIN, and aggregate functions.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.DATABASE, confidence=0.96, evidence_count=18)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=145,
                    unique_users=98,
                    completion_rate=0.81,
                    average_score=0.76,
                    average_time_spent=2100,
                    last_used=datetime.utcnow() - timedelta(hours=4)
                ),
                effectiveness_score=0.79,
                tags=["sql", "database", "queries", "joins"],
                metadata={"difficulty": "intermediate", "estimated_time": 35}
            ),

            # Machine Learning Templates
            TemplateEntityProfileCreate(
                template_id="ml_intro_assessment_001",
                template_name="Introduction to Machine Learning Assessment",
                template_type=TemplateType.ASSESSMENT,
                description="Comprehensive assessment covering basic machine learning concepts, algorithms, and applications.",
                domain_associations=[
                    DomainAssociation(domain=DomainCategory.MACHINE_LEARNING, confidence=0.94, evidence_count=16),
                    DomainAssociation(domain=DomainCategory.MATHEMATICS, confidence=0.70, evidence_count=4)
                ],
                usage_metrics=TemplateUsageMetrics(
                    total_uses=67,
                    unique_users=54,
                    completion_rate=0.72,
                    average_score=0.69,
                    average_time_spent=4200,
                    last_used=datetime.utcnow() - timedelta(hours=6)
                ),
                effectiveness_score=0.71,
                tags=["machine-learning", "ai", "algorithms", "assessment"],
                metadata={"difficulty": "advanced", "estimated_time": 70}
            )
        ]
        
        return templates

    def generate_sample_documents(self) -> List[Dict[str, Any]]:
        """Generate sample documents for domain inference"""
        documents = [
            {
                "document_id": "python_tutorial_001",
                "document_type": "tutorial",
                "content": """
                # Python Variables and Data Types
                
                In Python, variables are used to store data values. Unlike other programming languages,
                Python has no command for declaring a variable. A variable is created the moment you
                first assign a value to it.
                
                ```python
                x = 5
                y = "Hello, World!"
                z = 3.14
                ```
                
                Python has the following data types built-in by default:
                - Text Type: str
                - Numeric Types: int, float, complex
                - Sequence Types: list, tuple, range
                - Mapping Type: dict
                - Set Types: set, frozenset
                - Boolean Type: bool
                """,
                "metadata": {
                    "title": "Python Variables and Data Types",
                    "tags": ["python", "variables", "data-types"],
                    "file_extension": ".md"
                }
            },
            
            {
                "document_id": "binary_search_algorithm_001",
                "document_type": "algorithm_explanation",
                "content": """
                # Binary Search Algorithm
                
                Binary search is an efficient algorithm for finding an item from a sorted list of items.
                It works by repeatedly dividing in half the portion of the list that could contain the item,
                until you've narrowed down the possible locations to just one.
                
                ## Time Complexity
                - Best Case: O(1)
                - Average Case: O(log n)
                - Worst Case: O(log n)
                
                ## Implementation
                ```python
                def binary_search(arr, target):
                    left, right = 0, len(arr) - 1
                    
                    while left <= right:
                        mid = (left + right) // 2
                        if arr[mid] == target:
                            return mid
                        elif arr[mid] < target:
                            left = mid + 1
                        else:
                            right = mid - 1
                    
                    return -1
                ```
                """,
                "metadata": {
                    "title": "Binary Search Algorithm",
                    "tags": ["algorithms", "search", "binary-search", "complexity"],
                    "file_extension": ".md"
                }
            },
            
            {
                "document_id": "html_structure_guide_001",
                "document_type": "guide",
                "content": """
                # HTML Document Structure
                
                HTML (HyperText Markup Language) is the standard markup language for creating web pages.
                An HTML document has a specific structure that browsers understand.
                
                ## Basic HTML Structure
                ```html
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Page Title</title>
                </head>
                <body>
                    <h1>Main Heading</h1>
                    <p>This is a paragraph.</p>
                </body>
                </html>
                ```
                
                ## Key Elements
                - `<!DOCTYPE html>`: Declares the document type
                - `<html>`: Root element
                - `<head>`: Contains metadata
                - `<body>`: Contains visible content
                """,
                "metadata": {
                    "title": "HTML Document Structure",
                    "tags": ["html", "web-development", "structure"],
                    "file_extension": ".html"
                }
            },
            
            {
                "document_id": "sql_joins_tutorial_001",
                "document_type": "tutorial",
                "content": """
                # SQL Joins Tutorial
                
                SQL joins are used to combine rows from two or more tables based on a related column.
                There are several types of joins in SQL.
                
                ## Types of Joins
                
                ### INNER JOIN
                Returns records that have matching values in both tables.
                ```sql
                SELECT customers.name, orders.order_date
                FROM customers
                INNER JOIN orders ON customers.id = orders.customer_id;
                ```
                
                ### LEFT JOIN
                Returns all records from the left table and matched records from the right table.
                ```sql
                SELECT customers.name, orders.order_date
                FROM customers
                LEFT JOIN orders ON customers.id = orders.customer_id;
                ```
                
                ### RIGHT JOIN
                Returns all records from the right table and matched records from the left table.
                
                ### FULL OUTER JOIN
                Returns all records when there is a match in either left or right table.
                """,
                "metadata": {
                    "title": "SQL Joins Tutorial",
                    "tags": ["sql", "database", "joins", "queries"],
                    "file_extension": ".sql"
                }
            },
            
            {
                "document_id": "machine_learning_intro_001",
                "document_type": "lesson",
                "content": """
                # Introduction to Machine Learning
                
                Machine Learning (ML) is a subset of artificial intelligence that enables computers
                to learn and make decisions from data without being explicitly programmed.
                
                ## Types of Machine Learning
                
                ### Supervised Learning
                - Uses labeled training data
                - Examples: Classification, Regression
                - Algorithms: Linear Regression, Decision Trees, SVM
                
                ### Unsupervised Learning
                - Uses unlabeled data
                - Examples: Clustering, Association
                - Algorithms: K-Means, Hierarchical Clustering
                
                ### Reinforcement Learning
                - Learns through interaction with environment
                - Uses rewards and penalties
                - Examples: Game playing, Robotics
                
                ## Common Applications
                - Image Recognition
                - Natural Language Processing
                - Recommendation Systems
                - Fraud Detection
                - Autonomous Vehicles
                """,
                "metadata": {
                    "title": "Introduction to Machine Learning",
                    "tags": ["machine-learning", "ai", "supervised", "unsupervised"],
                    "file_extension": ".md"
                }
            }
        ]
        
        return documents

    async def create_sample_data(self):
        """Create all sample data in the database"""
        try:
            # Connect to database
            await db.connect_to_mongo()
            
            # Get collections
            template_collection = db.get_collection("template_entity_profiles")
            domain_collection = db.get_collection("document_domain_inferences")
            
            # Create repository
            repository = TemplateAnalyticsRepository(template_collection, domain_collection)
            await repository.create_indexes()
            
            # Generate and create template profiles
            logger.info("Creating sample template profiles...")
            templates = self.generate_sample_templates()
            
            for template_data in templates:
                try:
                    await repository.create_template_profile(template_data)
                    logger.info(f"Created template profile: {template_data.template_id}")
                except Exception as e:
                    logger.warning(f"Template {template_data.template_id} might already exist: {e}")
            
            # Generate and create document domain inferences
            logger.info("Creating sample document domain inferences...")
            documents = self.generate_sample_documents()
            
            for doc_data in documents:
                try:
                    # Infer domain using the engine
                    primary_domain, confidence, secondary_domains = self.domain_inference_engine.infer_domain(
                        doc_data["content"], 
                        doc_data["metadata"]
                    )
                    
                    # Create inference record
                    inference_data = DocumentDomainInferenceCreate(
                        document_id=doc_data["document_id"],
                        document_type=doc_data["document_type"],
                        inferred_primary_domain=primary_domain,
                        confidence_score=confidence,
                        secondary_domains=secondary_domains,
                        analysis_metadata={
                            "engine_version": "1.0",
                            "content_length": len(doc_data["content"]),
                            "sample_data": True
                        },
                        content_features=self.domain_inference_engine.analyze_content(
                            doc_data["content"], 
                            doc_data["metadata"]
                        )
                    )
                    
                    await repository.create_domain_inference(inference_data)
                    logger.info(f"Created domain inference for document: {doc_data['document_id']} -> {primary_domain.value}")
                    
                except Exception as e:
                    logger.warning(f"Document {doc_data['document_id']} might already exist: {e}")
            
            logger.info("Sample data creation completed successfully!")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            raise
        finally:
            await db.close_mongo_connection()


async def main():
    """Main function to run the sample data generator"""
    generator = SampleDataGenerator()
    await generator.create_sample_data()


if __name__ == "__main__":
    asyncio.run(main())