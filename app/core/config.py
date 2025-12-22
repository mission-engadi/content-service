"""Application configuration using Pydantic settings.

Configuration is loaded from environment variables or .env file.
Different configurations can be used for dev/staging/prod environments.
"""

import secrets
from typing import List, Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.
    
    All settings can be overridden via environment variables.
    For example, DATABASE_URL can be set in the environment or .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Application
    PROJECT_NAME: str = "Content Service"
    PROJECT_DESCRIPTION: str = "Manages missions content with multi-language support"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8002
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Override in production!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,https://engadi.org"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [i.strip() for i in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/content_service_db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis (for caching, sessions, etc.)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Kafka (for event-driven architecture)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_PREFIX: str = "content_service"
    
    # External Services
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    
    # Media & Storage
    UPLOAD_DIR: str = "/home/ubuntu/content_service/uploads"
    BASE_URL: str = "http://localhost:8002"  # Base URL for file serving
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    
    # Monitoring
    DATADOG_API_KEY: Optional[str] = None
    DATADOG_APP_KEY: Optional[str] = None
    
    # Feature Flags
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = False
    

# Create global settings instance
settings = Settings()
