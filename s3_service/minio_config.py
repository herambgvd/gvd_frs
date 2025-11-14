"""
MinIO S3 Configuration
"""

from pydantic_settings import BaseSettings
from config.settings import settings

class MinIOSettings(BaseSettings):
    """MinIO configuration settings"""
    
    # MinIO connection details from main settings
    minio_endpoint: str = settings.MINIO_ENDPOINT
    minio_access_key: str = settings.MINIO_ACCESS_KEY
    minio_secret_key: str = settings.MINIO_SECRET_KEY
    minio_bucket_name: str = settings.MINIO_BUCKET_NAME
    minio_secure: bool = settings.MINIO_SECURE
    
    # URL configuration for accessing images
    minio_url: str = settings.MINIO_URL  # Public URL for accessing images
    
    class Config:
        case_sensitive = False

# Initialize settings
minio_settings = MinIOSettings()
