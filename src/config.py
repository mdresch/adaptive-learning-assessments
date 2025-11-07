"""
Configuration settings for the Adaptive Learning System.
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    app_name: str = "Adaptive Learning System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    
    # Database settings
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "adaptive_learning"
    mongodb_min_pool_size: int = 10
    mongodb_max_pool_size: int = 100
    
    # Authentication settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # BKT Algorithm settings
    bkt_default_prior_knowledge: float = 0.1
    bkt_default_learning_rate: float = 0.3
    bkt_default_slip_probability: float = 0.1
    bkt_default_guess_probability: float = 0.2
    
    # Adaptive Engine settings
    max_recommendations: int = 10
    recommendation_cache_ttl: int = 3600  # seconds
    default_target_success_rate: float = 0.7
    
    # Rate limiting settings
    rate_limit_requests_per_hour: int = 1000
    rate_limit_burst_size: int = 100
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS settings
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]
    
    # Security settings
    trusted_hosts: list = ["*"]
    max_request_size: int = 16 * 1024 * 1024  # 16MB
    
    # Performance settings
    worker_processes: int = 1
    worker_connections: int = 1000
    keepalive_timeout: int = 65
    
    # Feature flags
    enable_difficulty_feedback: bool = True
    enable_recommendation_caching: bool = True
    enable_performance_analytics: bool = True
    enable_transfer_learning: bool = True
    
    # External services (for future integrations)
    talentq_api_url: Optional[str] = None
    talentq_api_key: Optional[str] = None
    
    # Monitoring and observability
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_health_checks: bool = True
    
    @validator("mongodb_url")
    def validate_mongodb_url(cls, v):
        """Validate MongoDB URL format."""
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        return v
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v, values):
        """Validate JWT secret key in production."""
        if values.get("environment") == "production" and v == "your-secret-key-change-in-production":
            raise ValueError("JWT secret key must be changed in production")
        return v
    
    @validator("bkt_default_prior_knowledge", "bkt_default_learning_rate", 
              "bkt_default_slip_probability", "bkt_default_guess_probability")
    def validate_bkt_probabilities(cls, v):
        """Validate BKT probability parameters are between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("BKT probability parameters must be between 0 and 1")
        return v
    
    @validator("default_target_success_rate")
    def validate_target_success_rate(cls, v):
        """Validate target success rate is reasonable."""
        if not 0.3 <= v <= 0.9:
            raise ValueError("Target success rate should be between 0.3 and 0.9")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class DevelopmentSettings(Settings):
    """Development environment settings."""
    
    debug: bool = True
    environment: str = "development"
    log_level: str = "DEBUG"
    
    # More permissive settings for development
    cors_origins: list = ["http://localhost:3000", "http://localhost:8080"]
    enable_metrics: bool = False


class ProductionSettings(Settings):
    """Production environment settings."""
    
    debug: bool = False
    environment: str = "production"
    log_level: str = "INFO"
    
    # Stricter settings for production
    cors_origins: list = []  # Should be configured explicitly
    trusted_hosts: list = []  # Should be configured explicitly
    rate_limit_requests_per_hour: int = 500  # More conservative
    
    # Performance optimizations
    worker_processes: int = 4
    worker_connections: int = 2000


class TestSettings(Settings):
    """Test environment settings."""
    
    debug: bool = True
    environment: str = "test"
    log_level: str = "WARNING"
    
    # Test database
    mongodb_database: str = "adaptive_learning_test"
    
    # Disable external services
    enable_metrics: bool = False
    enable_performance_analytics: bool = False


def get_settings() -> Settings:
    """Get settings based on environment."""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()