"""
Configuration settings for GVD FRS application
"""

from pydantic_settings import BaseSettings
from typing import List, Union
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    APP_NAME: str = "GVD FRS API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "gvd_frs_db"
    
    # Authentication settings (for integrating with gvd_ums)
    GVD_UMS_BASE_URL: str = "http://localhost:3000"
    JWT_SECRET_KEY: str = "your-secret-key"  # Should match gvd_ums JWT secret
    JWT_ALGORITHM: str = "HS256"
    
    # CORS settings - can be a string (comma-separated) or list
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173,http://127.0.0.1:8000"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # MinIO S3 settings (Docker container)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "media"
    MINIO_SECURE: bool = False
    MINIO_URL: str = "http://localhost:9000"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Convert CORS_ORIGINS string to list if it's a string
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()