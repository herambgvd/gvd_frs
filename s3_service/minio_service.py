"""
MinIO S3 Service
Handles image upload and management in MinIO
"""

import io
from datetime import datetime, timedelta

from minio import Minio as MinIOClient
from minio.error import S3Error

from fastapi import HTTPException, status

# Import config
from .minio_config import minio_settings

class MinIOService:
    """Service for handling MinIO S3 operations"""
    
    def __init__(self):
        """Initialize MinIO client (lazy initialization)"""
        self.client = None
        self.bucket_name = minio_settings.minio_bucket_name
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure MinIO client is initialized and connected"""
        if self._initialized:
            return
        
        try:
            self.client = MinIOClient(
                endpoint=minio_settings.minio_endpoint,
                access_key=minio_settings.minio_access_key,
                secret_key=minio_settings.minio_secret_key,
                secure=minio_settings.minio_secure
            )
            self._ensure_bucket_exists()
            self._initialized = True
        except Exception as e:
            print(f"❌ Error initializing MinIO: {e}")
            raise
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"✅ MinIO bucket '{self.bucket_name}' created successfully")
            else:
                print(f"✅ MinIO bucket '{self.bucket_name}' already exists")
        except S3Error as e:
            print(f"❌ Error creating bucket: {e}")
    
    async def upload_image(self, person_id: str, file_content: bytes, filename: str) -> dict:
        """
        Upload image/video to MinIO bucket.

        Args:
            person_id: Person unique ID
            file_content: File bytes
            filename: Original filename

        Returns:
            dict: Upload result (success, url, object_name, file_size)
        """
        try:
            self._ensure_initialized()

            # Extract extension
            file_extension = filename.split('.')[-1].lower()

            # Object Path in MinIO
            object_name = (
                f"{person_id}/media_{datetime.utcnow().timestamp()}.{file_extension}"
            )

            # Upload to MinIO
            file_size = len(file_content)
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=self._get_content_type(file_extension)
            )

            # Correct public URL
            file_url = f"{minio_settings.minio_url}/{self.bucket_name}/{object_name}"

            return {
                "success": True,
                "url": file_url,                # IMPORTANT: controller expects this
                "object_name": object_name,
                "file_size": file_size,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload image to MinIO: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while uploading image: {str(e)}"
            )
    
    async def delete_image(self, object_name: str) -> dict:
        """
        Delete image from MinIO bucket
        
        Args:
            object_name: Object name in MinIO
        
        Returns:
            Dictionary with deletion status
        """
        try:
            self._ensure_initialized()
            
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            return {
                "success": True,
                "message": f"Image deleted successfully from MinIO",
                "object_name": object_name
            }
            
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete image from MinIO: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while deleting image: {str(e)}"
            )
    
    async def get_image_presigned_url(self, object_name: str, expiry_hours: int = 24) -> str:
        """
        Get presigned URL for image (valid for specified hours)
        
        Args:
            object_name: Object name in MinIO
            expiry_hours: URL expiry time in hours
        
        Returns:
            Presigned URL string
        """
        try:
            self._ensure_initialized()
            
            url = self.client.get_presigned_download_url(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(hours=expiry_hours)
            )
            return url
            
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )
    
    @staticmethod
    def _get_content_type(file_extension: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
            'tiff': 'image/tiff'
        }
        return content_types.get(file_extension.lower(), 'image/jpeg')


# Global MinIO service instance
minio_service = MinIOService()
