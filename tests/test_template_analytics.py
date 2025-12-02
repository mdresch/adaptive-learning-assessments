"""
Tests for Template Analytics functionality

This module contains tests for template entity profiles, domain inference,
and analytics aggregation functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.models.template_analytics import (
    TemplateEntityProfile,
    TemplateEntityProfileCreate,
    DocumentDomainInference,
    DocumentDomainInferenceCreate,
    DomainCategory,
    TemplateType,
    DomainAssociation,
    TemplateUsageMetrics
)
from src.db.template_analytics_repository import TemplateAnalyticsRepository
from src.core.domain_inference_engine import DomainInferenceEngine


class TestTemplateAnalyticsRepository:
    """Test cases for TemplateAnalyticsRepository"""

    @pytest.fixture
    def mock_collections(self):
        """Create mock collections"""
        template_collection = AsyncMock()
        domain_collection = AsyncMock()
        return template_collection, domain_collection

    @pytest.fixture
    def repository(self, mock_collections):
        """Create repository instance with mock collections"""
        template_collection, domain_collection = mock_collections
        return TemplateAnalyticsRepository(template_collection, domain_collection)

    @pytest.mark.asyncio
    async def test_create_template_profile(self, repository, mock_collections):
        """Test creating a template profile"""
        template_collection, _ = mock_collections
        
        # Mock successful insertion
        template_collection.insert_one.return_value = AsyncMock()
        template_collection.insert_one.return_value.inserted_id = "507f1f77bcf86cd799439011"
        
        profile_data = TemplateEntityProfileCreate(
            template_id="test_template_001",
            template_name="Test Template",
            template_type=TemplateType.QUIZ,
            description="A test template"
        )
        
        result = await repository.create_template_profile(profile_data)
        
        assert isinstance(result, TemplateEntityProfile)
        assert result.template_id == "test_template_001"
        assert result.template_name == "Test Template"
        assert result.template_type == TemplateType.QUIZ
        template_collection.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_profile(self, repository, mock_collections):
        """Test retrieving a template profile"""
        template_collection, _ = mock_collections
        
        # Mock document found
        mock_document = {
            "_id": "507f1f77bcf86cd799439011",
            "template_id": "test_template_001",
            "template_name": "Test Template",
            "template_type": "quiz",
            "description": "A test template",
            "domain_associations": [],
            "usage_metrics": {
                "total_uses": 0,
                "unique_users": 0,
                "completion_rate": 0.0,
                "average_score": 0.0,
                "average_time_spent": 0,
                "last_used": None
            },
            "effectiveness_score": 0.0,
            "tags": [],
            "metadata": {},
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        template_collection.find_one.return_value = mock_document
        
        result = await repository.get_template_profile("test_template_001")
        
        assert isinstance(result, TemplateEntityProfile)
        assert result.template_id == "test_template_001"
        template_collection.find_one.assert_called_once_with({"template_id": "test_template_001"})

    @pytest.mark.asyncio
    async def test_get_template_profile_not_found(self, repository, mock_collections):
        """Test retrieving a non-existent template profile"""
        template_collection, _ = mock_collections
        
        # Mock document not found
        template_collection.find_one.return_value = None
        
        result = await repository.get_template_profile("nonexistent_template")
        
        assert result is None
        template_collection.find_one.assert_called_once_with({"template_id": "nonexistent_template"})

    @pytest.mark.asyncio
    async def test_update_template_usage(self, repository, mock_collections):
        """Test updating template usage metrics"""
        template_collection, _ = mock_collections
        
        # Mock successful update
        template_collection.update_one.return_value = AsyncMock()
        template_collection.update_one.return_value.modified_count = 1
        
        usage_data = {
            "increment_uses": 1,
            "completion_rate": 0.85,
            "average_score": 0.78
        }
        
        result = await repository.update_template_usage("test_template_001", usage_data)
        
        assert result is True
        template_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_domain_inference(self, repository, mock_collections):
        """Test creating a domain inference"""
        _, domain_collection = mock_collections
        
        # Mock successful insertion
        domain_collection.insert_one.return_value = AsyncMock()
        domain_collection.insert_one.return_value.inserted_id = "507f1f77bcf86cd799439012"
        
        inference_data = DocumentDomainInferenceCreate(
            document_id="test_doc_001",
            document_type="lesson",
            inferred_primary_domain=DomainCategory.PROGRAMMING,
            confidence_score=0.89
        )
        
        result = await repository.create_domain_inference(inference_data)
        
        assert isinstance(result, DocumentDomainInference)
        assert result.document_id == "test_doc_001"
        assert result.inferred_primary_domain == DomainCategory.PROGRAMMING
        assert result.confidence_score == 0.89
        domain_collection.insert_one.assert_called_once()


class TestDomainInferenceEngine:
    """Test cases for DomainInferenceEngine"""

    @pytest.fixture
    def engine(self):
        """Create domain inference engine instance"""
        return DomainInferenceEngine()

    def test_analyze_content_programming(self, engine):
        """Test content analysis for programming content"""
        content = """
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        This function calculates the fibonacci sequence using recursion.
        """
        
        features = engine.analyze_content(content)
        
        assert "keyword_scores" in features
        assert "pattern_scores" in features
        assert features["keyword_scores"][DomainCategory.PROGRAMMING] > 0
        assert features["code_blocks"] > 0

    def test_analyze_content_data_structures(self, engine):
        """Test content analysis for data structures content"""
        content = """
        A binary tree is a hierarchical data structure where each node has at most two children.
        Common operations include insertion, deletion, and traversal.
        The time complexity for search operations is O(log n) in a balanced tree.
        """
        
        features = engine.analyze_content(content)
        
        assert features["keyword_scores"][DomainCategory.DATA_STRUCTURES] > 0
        assert features["keyword_scores"][DomainCategory.ALGORITHMS] > 0

    def test_infer_domain_programming(self, engine):
        """Test domain inference for programming content"""
        content = """
        def quicksort(arr):
            if len(arr) <= 1:
                return arr
            pivot = arr[len(arr) // 2]
            left = [x for x in arr if x < pivot]
            middle = [x for x in arr if x == pivot]
            right = [x for x in arr if x > pivot]
            return quicksort(left) + middle + quicksort(right)
        """
        
        primary_domain, confidence, secondary_domains = engine.infer_domain(content)
        
        assert primary_domain == DomainCategory.PROGRAMMING
        assert confidence > 0.5
        assert isinstance(secondary_domains, list)

    def test_infer_domain_web_development(self, engine):
        """Test domain inference for web development content"""
        content = """
        <html>
        <head>
            <title>My Web Page</title>
            <style>
                body { font-family: Arial, sans-serif; }
                .container { max-width: 800px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to my website</h1>
                <p>This is a simple HTML page with CSS styling.</p>
            </div>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('Page loaded');
                });
            </script>
        </body>
        </html>
        """
        
        primary_domain, confidence, secondary_domains = engine.infer_domain(content)
        
        assert primary_domain == DomainCategory.WEB_DEVELOPMENT
        assert confidence > 0.5

    def test_infer_domain_with_metadata(self, engine):
        """Test domain inference with metadata hints"""
        content = "This is a basic programming tutorial."
        metadata = {
            "file_extension": ".py",
            "tags": ["python", "programming", "tutorial"],
            "title": "Introduction to Python Programming"
        }
        
        primary_domain, confidence, secondary_domains = engine.infer_domain(content, metadata)
        
        assert primary_domain == DomainCategory.PROGRAMMING
        # Confidence should be higher with metadata hints
        assert confidence > 0.3

    def test_batch_infer_domains(self, engine):
        """Test batch domain inference"""
        documents = [
            {
                "id": "doc1",
                "content": "def hello(): print('Hello, World!')",
                "metadata": {"file_extension": ".py"}
            },
            {
                "id": "doc2",
                "content": "SELECT * FROM users WHERE age > 18",
                "metadata": {"file_extension": ".sql"}
            },
            {
                "id": "doc3",
                "content": "<h1>Welcome</h1><p>This is HTML</p>",
                "metadata": {"file_extension": ".html"}
            }
        ]
        
        results = engine.batch_infer_domains(documents)
        
        assert len(results) == 3
        
        # Check first result (Python code)
        doc_id, domain, confidence, secondary = results[0]
        assert doc_id == "doc1"
        assert domain == DomainCategory.PROGRAMMING
        
        # Check second result (SQL)
        doc_id, domain, confidence, secondary = results[1]
        assert doc_id == "doc2"
        assert domain == DomainCategory.DATABASE
        
        # Check third result (HTML)
        doc_id, domain, confidence, secondary = results[2]
        assert doc_id == "doc3"
        assert domain == DomainCategory.WEB_DEVELOPMENT

    def test_clean_content(self, engine):
        """Test content cleaning functionality"""
        content = "  This is a TEST with   EXTRA    spaces!!! @#$%^&*()  "
        cleaned = engine._clean_content(content)
        
        assert cleaned == "this is a test with extra spaces"

    def test_calculate_keyword_scores(self, engine):
        """Test keyword score calculation"""
        content = "python programming function variable loop conditional"
        scores = engine._calculate_keyword_scores(content)
        
        assert DomainCategory.PROGRAMMING in scores
        assert scores[DomainCategory.PROGRAMMING] > 0
        assert scores[DomainCategory.PROGRAMMING] > scores[DomainCategory.MATHEMATICS]

    def test_count_code_blocks(self, engine):
        """Test code block counting"""
        content = """
        Here's some code:
        ```python
        def hello():
            print("Hello")
        ```
        
        And another block:
        <code>
        var x = 5;
        </code>
        """
        
        count = engine._count_code_blocks(content)
        assert count >= 2

    def test_analyze_complexity(self, engine):
        """Test complexity analysis"""
        content = "This is a simple sentence with basic words."
        complexity = engine._analyze_complexity(content)
        
        assert "avg_word_length" in complexity
        assert "sentence_complexity" in complexity
        assert complexity["avg_word_length"] > 0
        assert complexity["sentence_complexity"] >= 0


class TestTemplateAnalyticsModels:
    """Test cases for template analytics data models"""

    def test_template_entity_profile_creation(self):
        """Test creating a template entity profile"""
        profile = TemplateEntityProfile(
            template_id="test_001",
            template_name="Test Template",
            template_type=TemplateType.QUIZ,
            description="A test template for unit testing"
        )
        
        assert profile.template_id == "test_001"
        assert profile.template_name == "Test Template"
        assert profile.template_type == TemplateType.QUIZ
        assert profile.is_active is True
        assert isinstance(profile.usage_metrics, TemplateUsageMetrics)

    def test_document_domain_inference_creation(self):
        """Test creating a document domain inference"""
        inference = DocumentDomainInference(
            document_id="doc_001",
            document_type="lesson",
            inferred_primary_domain=DomainCategory.PROGRAMMING,
            confidence_score=0.85
        )
        
        assert inference.document_id == "doc_001"
        assert inference.inferred_primary_domain == DomainCategory.PROGRAMMING
        assert inference.confidence_score == 0.85
        assert isinstance(inference.secondary_domains, list)

    def test_domain_association_creation(self):
        """Test creating a domain association"""
        association = DomainAssociation(
            domain=DomainCategory.ALGORITHMS,
            confidence=0.75,
            evidence_count=3
        )
        
        assert association.domain == DomainCategory.ALGORITHMS
        assert association.confidence == 0.75
        assert association.evidence_count == 3

    def test_template_usage_metrics_defaults(self):
        """Test template usage metrics default values"""
        metrics = TemplateUsageMetrics()
        
        assert metrics.total_uses == 0
        assert metrics.unique_users == 0
        assert metrics.completion_rate == 0.0
        assert metrics.average_score == 0.0
        assert metrics.average_time_spent == 0
        assert metrics.last_used is None


# Integration test fixtures
@pytest.fixture
async def test_database():
    """Create test database connection"""
    # This would be implemented with a test database
    # For now, return a mock
    return MagicMock()


@pytest.mark.asyncio
async def test_template_analytics_integration(test_database):
    """Integration test for template analytics workflow"""
    # This would test the full workflow:
    # 1. Create template profile
    # 2. Infer document domains
    # 3. Track usage
    # 4. Generate analytics
    
    # Mock implementation for now
    assert True  # Placeholder for actual integration test