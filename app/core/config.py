"""
Application configuration settings.
"""
import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # App
    APP_NAME: str = "GVD-FRS"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # API
    API_V1_STR: str = "/api/v1"

    # CORS - Handle comma-separated string from env
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080"
    )

    # Database (Async for application)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/gvd_frs",
        description="Async database URL for application"
    )

    # Database (Sync for Alembic migrations)
    DATABASE_SYNC_URL: str = Field(
        default="postgresql://user:password@localhost:5432/gvd_frs",
        description="Sync database URL for Alembic migrations"
    )

    # Test Database (Sync)
    DATABASE_TEST_URL: str = Field(
        default="postgresql://user:password@localhost:5432/gvd_frs_test",
        description="Test database URL (sync mode)"
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production",
        description="Secret key for JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # License Management
    LICENSE_KEY_HEADER: str = Field(default="X-License-Key", description="Header name for license key")
    DEFAULT_LICENSE_EXPIRY_DAYS: int = Field(default=365, description="Default license expiry in days")
    ENABLE_LICENSE_USAGE_TRACKING: bool = Field(default=True, description="Enable license usage tracking")

    # External API
    EXTERNAL_API_URL: str = Field(default="https://api.example.com", description="External API URL")
    EXTERNAL_API_KEY: str = Field(default="your-api-key-here", description="External API key")

    # Metrics
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    @field_validator('BACKEND_CORS_ORIGINS')
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT.lower() in ("testing", "test")


# Create settings instance
settings = Settings()
