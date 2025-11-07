"""
Main FastAPI application for Adaptive Learning System.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
import os
from motor.motor_asyncio import AsyncIOMotorClient

from src.api.adaptive_endpoints import router as adaptive_router
from src.database.adaptive_repository import AdaptiveRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables for database connection
mongodb_client = None
database = None
adaptive_repository = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting Adaptive Learning System...")
    
    # Initialize database connection
    await startup_db_client()
    
    # Initialize repository
    global adaptive_repository
    adaptive_repository = AdaptiveRepository(database)
    
    # Set repository in endpoints
    adaptive_router.adaptive_repository = adaptive_repository
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Adaptive Learning System...")
    await shutdown_db_client()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Adaptive Learning System",
    description="Personalized learning platform with Bayesian Knowledge Tracing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Include routers
app.include_router(adaptive_router)


async def startup_db_client():
    """Initialize MongoDB connection."""
    global mongodb_client, database
    
    try:
        # Get MongoDB URL from environment
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "adaptive_learning")
        
        # Create MongoDB client
        mongodb_client = AsyncIOMotorClient(mongodb_url)
        
        # Test connection
        await mongodb_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Get database
        database = mongodb_client[database_name]
        
        # Create indexes
        await create_database_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


async def shutdown_db_client():
    """Close MongoDB connection."""
    global mongodb_client
    
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")


async def create_database_indexes():
    """Create necessary database indexes."""
    try:
        # Learner competencies indexes
        await database.learner_competencies.create_index([
            ("learner_id", 1), ("competency_id", 1)
        ], unique=True)
        await database.learner_competencies.create_index([
            ("learner_id", 1), ("mastery_level", -1)
        ])
        
        # Activity logs indexes
        await database.learner_activity_logs.create_index([
            ("learner_id", 1), ("timestamp", -1)
        ])
        await database.learner_activity_logs.create_index([
            ("activity_type", 1), ("timestamp", -1)
        ])
        
        # Challenges indexes
        await database.challenges.create_index([
            ("competencies", 1), ("difficulty_level", 1)
        ])
        await database.challenges.create_index([
            ("challenge_type", 1)
        ])
        
        # Learner progress indexes
        await database.learner_progress.create_index([
            ("learner_id", 1), ("content_item_id", 1)
        ], unique=True)
        
        # Difficulty feedback indexes
        await database.difficulty_feedback.create_index([
            ("learner_id", 1), ("challenge_id", 1), ("submitted_at", -1)
        ])
        
        # Recommendation history indexes
        await database.recommendation_history.create_index([
            ("learner_id", 1), ("timestamp", -1)
        ])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {str(e)}")
        # Don't raise - indexes might already exist


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Adaptive Learning System API",
        "version": "1.0.0",
        "description": "Personalized learning platform with Bayesian Knowledge Tracing",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "adaptive": "/api/v1/adaptive"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        if mongodb_client:
            await mongodb_client.admin.command('ping')
            db_status = "healthy"
        else:
            db_status = "disconnected"
        
        return {
            "status": "healthy" if db_status == "healthy" else "degraded",
            "database": db_status,
            "timestamp": "2025-01-27T10:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "error",
                "error": str(e),
                "timestamp": "2025-01-27T10:00:00Z"
            }
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )