# Dashboard API Implementation Guide

**Document Version:** 1.0  
**Date:** January 2025  
**Status:** Implementation Ready  
**Related Epic:** EPIC-004 - Data-Driven Insights Dashboard  

---

## Overview

This document provides detailed implementation guidance for the Analytics API endpoints that power the Data-Driven Insights Dashboard. It includes FastAPI route definitions, service layer implementations, and database query optimizations.

---

## FastAPI Route Implementations

### 1. Analytics Router Setup

```python
# src/api/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from src.core.analytics import AnalyticsService
from src.core.auth import get_current_user, verify_learner_access
from src.models.analytics import (
    DashboardResponse,
    PerformanceTrendResponse,
    MasteryAnalysisResponse,
    TimeRange
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/dashboard/{learner_id}", response_model=DashboardResponse)
async def get_learner_dashboard(
    learner_id: str,
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y|all)$"),
    competencies: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends()
):
    """
    Get comprehensive dashboard data for a learner
    """
    # Verify access permissions
    await verify_learner_access(current_user, learner_id)
    
    # Parse competency filter
    competency_list = competencies.split(",") if competencies else None
    
    try:
        dashboard_data = await analytics_service.get_dashboard_data(
            learner_id=learner_id,
            time_range=time_range,
            competency_filter=competency_list
        )
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")

@router.get("/performance-trends/{learner_id}", response_model=PerformanceTrendResponse)
async def get_performance_trends(
    learner_id: str,
    competency_ids: Optional[str] = Query(None),
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends()
):
    """
    Get detailed performance trends for specific competencies
    """
    await verify_learner_access(current_user, learner_id)
    
    competency_list = competency_ids.split(",") if competency_ids else None
    
    trends = await analytics_service.get_performance_trends(
        learner_id=learner_id,
        competency_ids=competency_list,
        granularity=granularity,
        start_date=start_date,
        end_date=end_date
    )
    return trends

@router.get("/mastery-analysis/{learner_id}", response_model=MasteryAnalysisResponse)
async def get_mastery_analysis(
    learner_id: str,
    include_mistakes: bool = Query(True),
    current_user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends()
):
    """
    Get detailed mastery analysis with mistake patterns
    """
    await verify_learner_access(current_user, learner_id)
    
    analysis = await analytics_service.get_mastery_analysis(
        learner_id=learner_id,
        include_mistake_patterns=include_mistakes
    )
    return analysis

@router.post("/refresh/{learner_id}")
async def refresh_analytics_cache(
    learner_id: str,
    current_user = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends()
):
    """
    Force refresh of analytics cache for a learner
    """
    await verify_learner_access(current_user, learner_id)
    
    await analytics_service.refresh_cache(learner_id)
    return {"message": "Analytics cache refreshed successfully"}
```

---

## Service Layer Implementation

### 2. Analytics Service

```python
# src/core/analytics/analytics_service.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from src.db.mongodb import get_database
from src.core.analytics.engines import (
    PerformanceTrendCalculator,
    MasteryAnalysisEngine,
    ConfidenceCorrelationAnalyzer,
    InsightGenerationService
)
from src.core.cache import AnalyticsCache
from src.models.analytics import *

class AnalyticsService:
    def __init__(self):
        self.db = get_database()
        self.cache = AnalyticsCache()
        self.trend_calculator = PerformanceTrendCalculator(self.db)
        self.mastery_engine = MasteryAnalysisEngine(self.db)
        self.confidence_analyzer = ConfidenceCorrelationAnalyzer(self.db)
        self.insight_generator = InsightGenerationService()
    
    async def get_dashboard_data(
        self,
        learner_id: str,
        time_range: str,
        competency_filter: Optional[List[str]] = None
    ) -> DashboardResponse:
        """
        Generate comprehensive dashboard data
        """
        # Check cache first
        cache_key = f"dashboard:{learner_id}:{time_range}:{','.join(competency_filter or [])}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return DashboardResponse.parse_obj(cached_data)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = self._calculate_start_date(time_range, end_date)
        
        # Gather analytics data in parallel
        performance_trends = await self.trend_calculator.calculate_trends(
            learner_id, start_date, end_date, competency_filter
        )
        
        mastery_analysis = await self.mastery_engine.analyze_mastery_levels(
            learner_id, competency_filter
        )
        
        confidence_correlations = await self.confidence_analyzer.analyze_confidence_accuracy(
            learner_id, start_date, end_date
        )
        
        insights = await self.insight_generator.generate_insights(
            learner_id, performance_trends, mastery_analysis, confidence_correlations
        )
        
        # Construct response
        dashboard_data = DashboardResponse(
            learner_id=learner_id,
            time_range=time_range,
            generated_at=datetime.utcnow(),
            performance_trends=performance_trends,
            mastery_analysis=mastery_analysis,
            confidence_correlations=confidence_correlations,
            insights=insights
        )
        
        # Cache the result
        await self.cache.set(cache_key, dashboard_data.dict(), ttl=3600)  # 1 hour
        
        return dashboard_data
    
    async def get_performance_trends(
        self,
        learner_id: str,
        competency_ids: Optional[List[str]] = None,
        granularity: str = "daily",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceTrendResponse:
        """
        Get detailed performance trends
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        trends = await self.trend_calculator.calculate_detailed_trends(
            learner_id, start_date, end_date, competency_ids, granularity
        )
        
        return PerformanceTrendResponse(
            learner_id=learner_id,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            trends=trends
        )
    
    async def get_mastery_analysis(
        self,
        learner_id: str,
        include_mistake_patterns: bool = True
    ) -> MasteryAnalysisResponse:
        """
        Get detailed mastery analysis
        """
        analysis = await self.mastery_engine.analyze_mastery_levels(learner_id)
        
        if include_mistake_patterns:
            mistake_patterns = await self.mastery_engine.identify_mistake_patterns(learner_id)
            analysis.mistake_patterns = mistake_patterns
        
        return MasteryAnalysisResponse(
            learner_id=learner_id,
            analysis=analysis,
            generated_at=datetime.utcnow()
        )
    
    async def refresh_cache(self, learner_id: str):
        """
        Clear and refresh analytics cache for a learner
        """
        await self.cache.delete_pattern(f"*:{learner_id}:*")
        
        # Pre-generate common dashboard views
        for time_range in ["7d", "30d", "90d"]:
            await self.get_dashboard_data(learner_id, time_range)
    
    def _calculate_start_date(self, time_range: str, end_date: datetime) -> datetime:
        """
        Calculate start date based on time range
        """
        if time_range == "7d":
            return end_date - timedelta(days=7)
        elif time_range == "30d":
            return end_date - timedelta(days=30)
        elif time_range == "90d":
            return end_date - timedelta(days=90)
        elif time_range == "1y":
            return end_date - timedelta(days=365)
        else:  # "all"
            return datetime(2020, 1, 1)  # System start date
```

---

## Analytics Engine Implementations

### 3. Performance Trend Calculator

```python
# src/core/analytics/engines/performance_trend_calculator.py
import numpy as np
from scipy import stats
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.models.analytics import PerformanceTrend, PerformancePoint

class PerformanceTrendCalculator:
    def __init__(self, db):
        self.db = db
    
    async def calculate_trends(
        self,
        learner_id: str,
        start_date: datetime,
        end_date: datetime,
        competency_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate performance trends for a learner
        """
        # Get activity data
        activity_data = await self._get_activity_data(
            learner_id, start_date, end_date, competency_filter
        )
        
        # Get competency mastery data
        mastery_data = await self._get_mastery_data(
            learner_id, start_date, end_date, competency_filter
        )
        
        # Calculate overall progress
        overall_progress = await self._calculate_overall_progress(
            activity_data, mastery_data
        )
        
        # Calculate competency-specific trends
        competency_trends = await self._calculate_competency_trends(
            mastery_data, competency_filter
        )
        
        return {
            "overall_progress": overall_progress,
            "competency_trends": competency_trends
        }
    
    async def _get_activity_data(
        self,
        learner_id: str,
        start_date: datetime,
        end_date: datetime,
        competency_filter: Optional[List[str]]
    ) -> List[Dict]:
        """
        Retrieve learner activity data from database
        """
        pipeline = [
            {
                "$match": {
                    "learner_id": learner_id,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            }
        ]
        
        if competency_filter:
            pipeline[0]["$match"]["competency_id"] = {"$in": competency_filter}
        
        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                        "competency_id": "$competency_id"
                    },
                    "activity_count": {"$sum": 1},
                    "total_score": {"$sum": "$score"},
                    "success_count": {"$sum": {"$cond": [{"$gte": ["$score", 0.7]}, 1, 0]}}
                }
            },
            {
                "$addFields": {
                    "success_rate": {"$divide": ["$success_count", "$activity_count"]},
                    "average_score": {"$divide": ["$total_score", "$activity_count"]}
                }
            },
            {"$sort": {"_id.date": 1}}
        ])
        
        return await self.db.learner_activity_logs.aggregate(pipeline).to_list(None)
    
    async def _get_mastery_data(
        self,
        learner_id: str,
        start_date: datetime,
        end_date: datetime,
        competency_filter: Optional[List[str]]
    ) -> List[Dict]:
        """
        Retrieve mastery progression data
        """
        match_filter = {
            "learner_id": learner_id,
            "updated_at": {"$gte": start_date, "$lte": end_date}
        }
        
        if competency_filter:
            match_filter["competency_id"] = {"$in": competency_filter}
        
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$updated_at"}},
                        "competency_id": "$competency_id"
                    },
                    "mastery_score": {"$last": "$mastery_probability"}
                }
            },
            {"$sort": {"_id.date": 1}}
        ]
        
        return await self.db.learner_competencies.aggregate(pipeline).to_list(None)
    
    async def _calculate_overall_progress(
        self,
        activity_data: List[Dict],
        mastery_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate overall progress metrics
        """
        if not mastery_data:
            return {
                "current_score": 0.0,
                "change_percentage": 0.0,
                "trend_direction": "STABLE"
            }
        
        # Calculate current average mastery
        current_scores = [item["mastery_score"] for item in mastery_data[-10:]]  # Last 10 data points
        current_score = np.mean(current_scores)
        
        # Calculate trend direction using linear regression
        if len(mastery_data) >= 5:
            dates = [datetime.strptime(item["_id"]["date"], "%Y-%m-%d") for item in mastery_data]
            scores = [item["mastery_score"] for item in mastery_data]
            
            # Convert dates to numeric values for regression
            date_nums = [(d - dates[0]).days for d in dates]
            slope, _, _, p_value, _ = stats.linregress(date_nums, scores)
            
            if p_value < 0.05:  # Statistically significant
                if slope > 0.01:
                    trend_direction = "IMPROVING"
                elif slope < -0.01:
                    trend_direction = "DECLINING"
                else:
                    trend_direction = "STABLE"
            else:
                trend_direction = "STABLE"
            
            # Calculate percentage change
            if len(mastery_data) >= 2:
                old_score = mastery_data[0]["mastery_score"]
                change_percentage = ((current_score - old_score) / old_score) * 100 if old_score > 0 else 0
            else:
                change_percentage = 0.0
        else:
            trend_direction = "STABLE"
            change_percentage = 0.0
        
        return {
            "current_score": round(current_score, 3),
            "change_percentage": round(change_percentage, 1),
            "trend_direction": trend_direction
        }
    
    async def _calculate_competency_trends(
        self,
        mastery_data: List[Dict],
        competency_filter: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Calculate trends for individual competencies
        """
        # Group data by competency
        competency_groups = {}
        for item in mastery_data:
            comp_id = item["_id"]["competency_id"]
            if comp_id not in competency_groups:
                competency_groups[comp_id] = []
            competency_groups[comp_id].append(item)
        
        trends = []
        for competency_id, data_points in competency_groups.items():
            # Get competency name (would need to join with competencies collection)
            competency_name = await self._get_competency_name(competency_id)
            
            # Calculate current mastery
            current_mastery = data_points[-1]["mastery_score"] if data_points else 0.0
            
            # Format trend data
            trend_data = [
                {
                    "date": item["_id"]["date"],
                    "mastery_score": item["mastery_score"],
                    "confidence_level": None  # Would be populated if confidence data available
                }
                for item in data_points
            ]
            
            trends.append({
                "competency_id": competency_id,
                "competency_name": competency_name,
                "current_mastery": round(current_mastery, 3),
                "trend_data": trend_data
            })
        
        return trends
    
    async def _get_competency_name(self, competency_id: str) -> str:
        """
        Get competency name from competencies collection
        """
        competency = await self.db.competencies.find_one({"_id": competency_id})
        return competency["name"] if competency else competency_id
```

### 4. Mastery Analysis Engine

```python
# src/core/analytics/engines/mastery_analysis_engine.py
from typing import List, Dict, Any
from collections import Counter
from datetime import datetime, timedelta

class MasteryAnalysisEngine:
    def __init__(self, db):
        self.db = db
    
    async def analyze_mastery_levels(
        self,
        learner_id: str,
        competency_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze current mastery levels and identify areas for improvement
        """
        # Get current mastery levels
        mastery_data = await self._get_current_mastery_levels(learner_id, competency_filter)
        
        # Categorize competencies by mastery level
        low_mastery_areas = []
        strong_areas = []
        
        for item in mastery_data:
            competency_info = {
                "competency_id": item["competency_id"],
                "competency_name": await self._get_competency_name(item["competency_id"]),
                "mastery_score": round(item["mastery_probability"], 3)
            }
            
            if item["mastery_probability"] < 0.5:
                # Add frequent mistakes for low mastery areas
                mistakes = await self._get_frequent_mistakes(learner_id, item["competency_id"])
                competency_info["frequent_mistakes"] = mistakes
                low_mastery_areas.append(competency_info)
            elif item["mastery_probability"] > 0.8:
                strong_areas.append(competency_info)
        
        return {
            "low_mastery_areas": low_mastery_areas,
            "strong_areas": strong_areas
        }
    
    async def identify_mistake_patterns(
        self,
        learner_id: str,
        competency_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Identify recurring mistake patterns
        """
        # Get recent activity logs with mistakes
        match_filter = {
            "learner_id": learner_id,
            "score": {"$lt": 0.7},  # Consider scores below 70% as mistakes
            "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
        }
        
        if competency_id:
            match_filter["competency_id"] = competency_id
        
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": {
                        "competency_id": "$competency_id",
                        "mistake_type": "$mistake_category"  # Assuming this field exists
                    },
                    "frequency": {"$sum": 1},
                    "last_occurrence": {"$max": "$timestamp"},
                    "related_activities": {"$addToSet": "$activity_id"}
                }
            },
            {"$sort": {"frequency": -1}}
        ]
        
        mistake_data = await self.db.learner_activity_logs.aggregate(pipeline).to_list(None)
        
        patterns = []
        for item in mistake_data:
            if item["frequency"] >= 3:  # Only include patterns with 3+ occurrences
                suggestion = await self._generate_mistake_suggestion(
                    item["_id"]["competency_id"],
                    item["_id"]["mistake_type"]
                )
                
                patterns.append({
                    "mistake_type": item["_id"]["mistake_type"],
                    "frequency": item["frequency"],
                    "last_occurrence": item["last_occurrence"],
                    "suggestion": suggestion
                })
        
        return patterns
    
    async def _get_current_mastery_levels(
        self,
        learner_id: str,
        competency_filter: Optional[List[str]]
    ) -> List[Dict]:
        """
        Get current mastery levels for all competencies
        """
        match_filter = {"learner_id": learner_id}
        if competency_filter:
            match_filter["competency_id"] = {"$in": competency_filter}
        
        return await self.db.learner_competencies.find(match_filter).to_list(None)
    
    async def _get_frequent_mistakes(
        self,
        learner_id: str,
        competency_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get frequent mistakes for a specific competency
        """
        pipeline = [
            {
                "$match": {
                    "learner_id": learner_id,
                    "competency_id": competency_id,
                    "score": {"$lt": 0.7},
                    "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
                }
            },
            {
                "$group": {
                    "_id": "$mistake_category",
                    "frequency": {"$sum": 1}
                }
            },
            {"$sort": {"frequency": -1}},
            {"$limit": 3}
        ]
        
        mistakes = await self.db.learner_activity_logs.aggregate(pipeline).to_list(None)
        
        return [
            {
                "mistake_type": item["_id"],
                "frequency": item["frequency"],
                "suggestion": await self._generate_mistake_suggestion(competency_id, item["_id"])
            }
            for item in mistakes
        ]
    
    async def _generate_mistake_suggestion(
        self,
        competency_id: str,
        mistake_type: str
    ) -> str:
        """
        Generate improvement suggestions based on mistake patterns
        """
        # This would be enhanced with a more sophisticated recommendation engine
        suggestions = {
            "pointer_manipulation": "Practice pointer traversal exercises",
            "array_bounds": "Review array indexing and boundary conditions",
            "recursion_base_case": "Focus on identifying proper base cases",
            "loop_termination": "Practice loop condition analysis",
            "memory_management": "Study memory allocation and deallocation patterns"
        }
        
        return suggestions.get(mistake_type, "Review fundamental concepts and practice more exercises")
    
    async def _get_competency_name(self, competency_id: str) -> str:
        """
        Get competency name from competencies collection
        """
        competency = await self.db.competencies.find_one({"_id": competency_id})
        return competency["name"] if competency else competency_id
```

---

## Database Optimization

### 5. Index Creation Script

```python
# scripts/create_analytics_indexes.py
from src.db.mongodb import get_database

async def create_analytics_indexes():
    """
    Create optimized indexes for analytics queries
    """
    db = get_database()
    
    # Learner activity logs indexes
    await db.learner_activity_logs.create_index([
        ("learner_id", 1),
        ("timestamp", -1)
    ])
    
    await db.learner_activity_logs.create_index([
        ("learner_id", 1),
        ("competency_id", 1),
        ("timestamp", -1)
    ])
    
    await db.learner_activity_logs.create_index([
        ("learner_id", 1),
        ("score", 1),
        ("timestamp", -1)
    ])
    
    # Learner competencies indexes
    await db.learner_competencies.create_index([
        ("learner_id", 1),
        ("competency_id", 1)
    ])
    
    await db.learner_competencies.create_index([
        ("learner_id", 1),
        ("updated_at", -1)
    ])
    
    # Analytics cache indexes
    await db.analytics_cache.create_index([
        ("learner_id", 1),
        ("cache_type", 1)
    ])
    
    await db.analytics_cache.create_index([
        ("expires_at", 1)
    ], expireAfterSeconds=0)  # TTL index
    
    print("Analytics indexes created successfully")

if __name__ == "__main__":
    import asyncio
    asyncio.run(create_analytics_indexes())
```

---

## Caching Implementation

### 6. Analytics Cache Service

```python
# src/core/cache/analytics_cache.py
import json
import redis
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

class AnalyticsCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host="localhost",  # Configure from environment
            port=6379,
            decode_responses=True
        )
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached analytics data
        """
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        data: Dict[str, Any],
        ttl: int = 3600
    ):
        """
        Cache analytics data with TTL
        """
        try:
            serialized_data = json.dumps(data, default=str)
            self.redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            print(f"Cache set error: {e}")
    
    async def delete_pattern(self, pattern: str):
        """
        Delete all keys matching a pattern
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Cache delete error: {e}")
    
    async def invalidate_learner_cache(self, learner_id: str):
        """
        Invalidate all cache entries for a specific learner
        """
        await self.delete_pattern(f"*:{learner_id}:*")
```

---

## Testing Implementation

### 7. Analytics API Tests

```python
# tests/test_analytics_api.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from src.main import app

client = TestClient(app)

class TestAnalyticsAPI:
    
    @pytest.fixture
    def auth_headers(self):
        # Mock authentication headers
        return {"Authorization": "Bearer test_token"}
    
    def test_get_dashboard_success(self, auth_headers):
        """Test successful dashboard data retrieval"""
        response = client.get(
            "/api/v1/analytics/dashboard/test_learner_123",
            headers=auth_headers,
            params={"time_range": "30d"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "learner_id" in data
        assert "performance_trends" in data
        assert "mastery_analysis" in data
        assert "insights" in data
    
    def test_get_dashboard_invalid_time_range(self, auth_headers):
        """Test dashboard with invalid time range"""
        response = client.get(
            "/api/v1/analytics/dashboard/test_learner_123",
            headers=auth_headers,
            params={"time_range": "invalid"}
        )
        
        assert response.status_code == 422
    
    def test_get_performance_trends(self, auth_headers):
        """Test performance trends endpoint"""
        response = client.get(
            "/api/v1/analytics/performance-trends/test_learner_123",
            headers=auth_headers,
            params={
                "granularity": "daily",
                "competency_ids": "arrays_basics,linked_lists"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert "granularity" in data
    
    def test_refresh_cache(self, auth_headers):
        """Test cache refresh endpoint"""
        response = client.post(
            "/api/v1/analytics/refresh/test_learner_123",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_unauthorized_access(self):
        """Test unauthorized access to analytics"""
        response = client.get("/api/v1/analytics/dashboard/test_learner_123")
        assert response.status_code == 401
```

---

## Conclusion

This implementation guide provides a comprehensive foundation for building the Analytics API that powers the Data-Driven Insights Dashboard. The modular design allows for easy testing, maintenance, and future enhancements while ensuring optimal performance through caching and database optimization strategies.