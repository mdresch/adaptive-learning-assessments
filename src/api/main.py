"""
Main FastAPI application for the Adaptive Learning System.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..db.mongodb_client import MongoDBClient
from ..core.bkt_engine import BKTEngine
from ..core.learner_profiler import LearnerProfiler
from ..core.adaptive_selector import AdaptiveContentSelector
from ..core.performance_tracker import PerformanceTracker

from .routes import learner_routes, competency_routes, performance_routes, adaptive_routes


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Global application state
app_state = {
    "db_client": None,
    "bkt_engine": None,
    "learner_profiler": None,
    "adaptive_selector": None,
    "performance_tracker": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Adaptive Learning System API...")
    
    try:
        # Initialize database client
        db_client = MongoDBClient()
        if await db_client.connect():
            app_state["db_client"] = db_client
            
            # Create database indexes
            await db_client.create_indexes()
            
            # Initialize core components
            app_state["bkt_engine"] = BKTEngine(db_client)
            app_state["learner_profiler"] = LearnerProfiler(db_client)
            app_state["performance_tracker"] = PerformanceTracker(
                db_client, app_state["bkt_engine"]
            )
            app_state["adaptive_selector"] = AdaptiveContentSelector(db_client)
            
            logger.info("Successfully initialized all components")
        else:
            logger.error("Failed to connect to database")
            raise RuntimeError("Database connection failed")
            
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Adaptive Learning System API...")
    
    if app_state["db_client"]:
        await app_state["db_client"].disconnect()
    
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Adaptive Learning System API",
        description="API for the Adaptive Learning System with BKT engine and personalized content delivery",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        try:
            db_health = {"status": "unknown"}
            if app_state["db_client"]:
                db_health = await app_state["db_client"].health_check()
            
            return {
                "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
                "version": "1.0.0",
                "database": db_health,
                "components": {
                    "bkt_engine": app_state["bkt_engine"] is not None,
                    "learner_profiler": app_state["learner_profiler"] is not None,
                    "adaptive_selector": app_state["adaptive_selector"] is not None,
                    "performance_tracker": app_state["performance_tracker"] is not None
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": str(e)}
            )
    
    # Database stats endpoint
    @app.get("/stats")
    async def database_stats():
        """Get database statistics."""
        try:
            if not app_state["db_client"]:
                raise HTTPException(status_code=503, detail="Database not available")
            
            stats = await app_state["db_client"].get_database_stats()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
    
    # Include routers
    app.include_router(
        learner_routes.router,
        prefix="/api/v1/learners",
        tags=["learners"]
    )
    
    app.include_router(
        competency_routes.router,
        prefix="/api/v1/competencies",
        tags=["competencies"]
    )
    
    app.include_router(
        performance_routes.router,
        prefix="/api/v1/performance",
        tags=["performance"]
    )
    
    app.include_router(
        adaptive_routes.router,
        prefix="/api/v1/adaptive",
        tags=["adaptive"]
    )
    
    return app


def get_app_state():
    """Get the current application state."""
    return app_state