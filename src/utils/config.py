"""
Configuration Management

Centralized configuration for the BKT algorithm and adaptive learning system.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        env="MONGODB_URI",
        description="MongoDB connection URI"
    )
    database_name: str = Field(
        default="adaptive_learning",
        env="DATABASE_NAME",
        description="Database name"
    )
    connection_timeout: int = Field(
        default=10000,
        env="DB_CONNECTION_TIMEOUT",
        description="Database connection timeout in milliseconds"
    )
    max_pool_size: int = Field(
        default=100,
        env="DB_MAX_POOL_SIZE",
        description="Maximum database connection pool size"
    )
    
    class Config:
        env_file = ".env"


class CacheConfig(BaseSettings):
    """Cache configuration settings"""
    
    use_redis: bool = Field(
        default=True,
        env="USE_REDIS",
        description="Whether to use Redis for caching"
    )
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL",
        description="Redis connection URL"
    )
    default_ttl: int = Field(
        default=300,
        env="CACHE_DEFAULT_TTL",
        description="Default cache TTL in seconds"
    )
    key_prefix: str = Field(
        default="bkt:",
        env="CACHE_KEY_PREFIX",
        description="Cache key prefix"
    )
    
    class Config:
        env_file = ".env"


class BKTConfig(BaseSettings):
    """BKT algorithm configuration settings"""
    
    # Default BKT parameters
    default_p_l0: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        env="BKT_DEFAULT_P_L0",
        description="Default initial probability of knowing skill"
    )
    default_p_t: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        env="BKT_DEFAULT_P_T",
        description="Default probability of learning transition"
    )
    default_p_g: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        env="BKT_DEFAULT_P_G",
        description="Default probability of guessing correctly"
    )
    default_p_s: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        env="BKT_DEFAULT_P_S",
        description="Default probability of slipping"
    )
    
    # Mastery settings
    mastery_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        env="BKT_MASTERY_THRESHOLD",
        description="Threshold for considering skill mastered"
    )
    min_attempts_for_mastery: int = Field(
        default=3,
        ge=1,
        env="BKT_MIN_ATTEMPTS",
        description="Minimum attempts required before mastery can be achieved"
    )
    
    # Performance settings
    cache_ttl_seconds: int = Field(
        default=300,
        ge=0,
        env="BKT_CACHE_TTL",
        description="Cache TTL for competency data in seconds"
    )
    update_batch_size: int = Field(
        default=100,
        ge=1,
        env="BKT_BATCH_SIZE",
        description="Batch size for bulk competency updates"
    )
    max_workers: int = Field(
        default=10,
        ge=1,
        env="BKT_MAX_WORKERS",
        description="Maximum worker threads for concurrent processing"
    )
    
    # Advanced features
    enable_forgetting: bool = Field(
        default=False,
        env="BKT_ENABLE_FORGETTING",
        description="Whether to model skill forgetting over time"
    )
    forgetting_rate: float = Field(
        default=0.01,
        ge=0.0,
        le=1.0,
        env="BKT_FORGETTING_RATE",
        description="Daily forgetting rate if forgetting is enabled"
    )
    
    @validator('default_p_g', 'default_p_s')
    def validate_guess_slip_sum(cls, v, values):
        """Ensure P(G) + P(S) <= 1 for mathematical consistency"""
        if 'default_p_g' in values:
            p_g = values['default_p_g'] if v != values.get('default_p_g') else v
            p_s = v if v != values.get('default_p_g') else values.get('default_p_s', 0)
            if p_g + p_s > 1.0:
                raise ValueError("P(G) + P(S) must be <= 1.0")
        return v
    
    class Config:
        env_file = ".env"


class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    
    jwt_secret: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET",
        description="JWT signing secret"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM",
        description="JWT signing algorithm"
    )
    jwt_expiration_hours: int = Field(
        default=24,
        env="JWT_EXPIRATION_HOURS",
        description="JWT token expiration time in hours"
    )
    
    # API rate limiting
    rate_limit_requests: int = Field(
        default=1000,
        env="RATE_LIMIT_REQUESTS",
        description="Number of requests per time window"
    )
    rate_limit_window: int = Field(
        default=3600,
        env="RATE_LIMIT_WINDOW",
        description="Rate limit time window in seconds"
    )
    
    class Config:
        env_file = ".env"


class LoggingConfig(BaseSettings):
    """Logging configuration settings"""
    
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log message format"
    )
    log_file: Optional[str] = Field(
        default=None,
        env="LOG_FILE",
        description="Log file path (optional)"
    )
    
    class Config:
        env_file = ".env"


class APIConfig(BaseSettings):
    """API configuration settings"""
    
    host: str = Field(
        default="0.0.0.0",
        env="API_HOST",
        description="API host address"
    )
    port: int = Field(
        default=8000,
        env="API_PORT",
        description="API port number"
    )
    debug: bool = Field(
        default=False,
        env="API_DEBUG",
        description="Enable debug mode"
    )
    reload: bool = Field(
        default=False,
        env="API_RELOAD",
        description="Enable auto-reload in development"
    )
    
    # CORS settings
    cors_origins: list = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins"
    )
    cors_methods: list = Field(
        default=["GET", "POST", "PUT", "DELETE"],
        env="CORS_METHODS",
        description="Allowed CORS methods"
    )
    
    class Config:
        env_file = ".env"


class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment"
    )
    
    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    cache: CacheConfig = CacheConfig()
    bkt: BKTConfig = BKTConfig()
    security: SecurityConfig = SecurityConfig()
    logging: LoggingConfig = LoggingConfig()
    api: APIConfig = APIConfig()
    
    # Feature flags
    enable_analytics: bool = Field(
        default=True,
        env="ENABLE_ANALYTICS",
        description="Enable analytics endpoints"
    )
    enable_batch_processing: bool = Field(
        default=True,
        env="ENABLE_BATCH_PROCESSING",
        description="Enable batch processing endpoints"
    )
    enable_real_time_updates: bool = Field(
        default=True,
        env="ENABLE_REAL_TIME_UPDATES",
        description="Enable real-time competency updates"
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment.lower() == "testing"
    
    def get_mongodb_uri(self) -> str:
        """Get MongoDB URI with proper formatting"""
        return self.database.mongodb_uri
    
    def get_redis_url(self) -> str:
        """Get Redis URL with proper formatting"""
        return self.cache.redis_url
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Convenience functions for accessing specific configurations
def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_settings().database


def get_cache_config() -> CacheConfig:
    """Get cache configuration"""
    return get_settings().cache


def get_bkt_config() -> BKTConfig:
    """Get BKT configuration"""
    return get_settings().bkt


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return get_settings().security


def get_logging_config() -> LoggingConfig:
    """Get logging configuration"""
    return get_settings().logging


def get_api_config() -> APIConfig:
    """Get API configuration"""
    return get_settings().api


# Environment-specific configuration loading
def load_config_for_environment(env: str) -> Settings:
    """Load configuration for specific environment"""
    env_file = f".env.{env.lower()}"
    if os.path.exists(env_file):
        return Settings(_env_file=env_file)
    return Settings()


# Configuration validation
def validate_configuration() -> Dict[str, Any]:
    """Validate configuration and return validation results"""
    settings = get_settings()
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Validate BKT parameters
    bkt_config = settings.bkt
    if bkt_config.default_p_g + bkt_config.default_p_s > 1.0:
        validation_results["errors"].append("P(G) + P(S) must be <= 1.0")
        validation_results["valid"] = False
    
    # Validate security settings in production
    if settings.is_production:
        if settings.security.jwt_secret == "your-secret-key-change-in-production":
            validation_results["errors"].append("JWT secret must be changed in production")
            validation_results["valid"] = False
        
        if settings.api.debug:
            validation_results["warnings"].append("Debug mode should be disabled in production")
    
    # Validate database connection
    if not settings.database.mongodb_uri:
        validation_results["errors"].append("MongoDB URI is required")
        validation_results["valid"] = False
    
    return validation_results