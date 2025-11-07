"""
Main FastAPI application for the Adaptive Learning System

This module sets up the FastAPI application with all routes, middleware,
and database connections for the learner profile management system.
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db.database import startup_database, shutdown_database
from .api.learner_routes import router as learner_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    try:
        await startup_database()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await shutdown_database()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Adaptive Learning System API",
    description="""
    API for the Adaptive Learning System focusing on personalized learning experiences
    for programming and data structures education.
    
    ## Features
    
    * **Learner Profile Management**: Create and manage comprehensive learner profiles
    * **Personalization Engine**: Adaptive content delivery based on learner characteristics
    * **Accessibility Support**: Comprehensive accessibility features and adaptations
    * **Privacy Compliance**: GDPR and FERPA compliant data handling
    
    ## Learner Profile Management
    
    The learner profile system captures:
    - Demographics (age, education level, location)
    - Learning preferences (style, accessibility needs, session preferences)
    - Programming experience (languages, data structures, algorithms)
    - Self-reported data (confidence, goals, motivation)
    
    Profile changes immediately influence learning path personalization to provide
    the most effective and engaging learning experience.
    """,
    version="1.0.0",
    contact={
        "name": "Adaptive Learning System Team",
        "email": "support@adaptivelearning.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_server_error"
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    
    Returns the current status of the application and its dependencies.
    """
    return {
        "status": "healthy",
        "service": "Adaptive Learning System API",
        "version": "1.0.0",
        "timestamp": "2025-01-01T00:00:00Z"
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Welcome to the Adaptive Learning System API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }


# Include routers
app.include_router(learner_router)


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )