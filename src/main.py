"""
Main FastAPI Application

Entry point for the Adaptive Learning System with BKT algorithm implementation.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .api.bkt_endpoints import router as bkt_router
from .utils.dependencies import initialize_dependencies, cleanup_dependencies
from .utils.config import get_settings, validate_configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    
    # Startup
    logger.info("Starting Adaptive Learning System...")
    
    try:
        # Validate configuration
        validation_results = validate_configuration()
        if not validation_results["valid"]:
            logger.error(f"Configuration validation failed: {validation_results['errors']}")
            raise RuntimeError("Invalid configuration")
        
        if validation_results["warnings"]:
            for warning in validation_results["warnings"]:
                logger.warning(f"Configuration warning: {warning}")
        
        # Initialize dependencies
        await initialize_dependencies()
        
        logger.info("Adaptive Learning System started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Adaptive Learning System...")
    
    try:
        await cleanup_dependencies()
        logger.info("Adaptive Learning System shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    settings = get_settings()
    
    # Create FastAPI app with lifespan manager
    app = FastAPI(
        title="Adaptive Learning System",
        description="BKT-based adaptive learning system for personalized education",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app, settings)
    
    # Add routers
    app.include_router(bkt_router)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Add health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "service": "adaptive-learning-system",
            "version": "1.0.0"
        }
    
    @app.get("/")
    async def root():
        """Root endpoint with basic information"""
        return {
            "message": "Adaptive Learning System API",
            "version": "1.0.0",
            "docs_url": "/docs" if not settings.is_production else "Documentation disabled in production"
        }
    
    return app


def setup_middleware(app: FastAPI, settings):
    """Configure application middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=settings.api.cors_methods,
        allow_headers=["*"],
    )
    
    # Trusted host middleware for production
    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure with actual allowed hosts in production
        )


def setup_exception_handlers(app: FastAPI):
    """Configure global exception handlers"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Handle general exceptions"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "status_code": 500
            }
        )


# Create the app instance
app = create_app()


def main():
    """Main entry point for running the application"""
    settings = get_settings()
    
    uvicorn.run(
        "src.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload and settings.is_development,
        log_level=settings.logging.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()