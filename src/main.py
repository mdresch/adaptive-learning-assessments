"""
Main FastAPI application for the Adaptive Learning System

This module sets up the FastAPI application with all routes, middleware,
and database connections for the learner profile management system.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from .db.database import db
from .db.learner_repository import LearnerRepository
from .api.learner_profile_routes import router as learner_router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting up Adaptive Learning System...")
    
    try:
        # Connect to database
        await db.connect_to_mongo()
        
        # Create indexes
        collection = await db.get_collection("learner_profiles")
        repository = LearnerRepository(collection)
        await repository.create_indexes()
        
        logger.info("Database connected and indexes created")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Adaptive Learning System...")
    await db.close_mongo_connection()


# Create FastAPI application
app = FastAPI(
    title="Adaptive Learning System",
    description="A personalized learning platform that adapts to individual learner needs and preferences",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.database.command("ping")
        return {
            "status": "healthy",
            "service": "Adaptive Learning System",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Adaptive Learning System",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(learner_router)


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )