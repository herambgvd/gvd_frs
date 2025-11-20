"""
Media Upload Controller
"""
from fastapi import UploadFile, HTTPException, status
from datetime import datetime
import uuid
from bson import ObjectId

from apps.media_uploads.utils import MediaUtils
from s3_service.minio_service import minio_service


class MediaUploadController:
    def __init__(self, db):
        self.collection = db.media_uploads

    async def upload_media(
        self,
        file: UploadFile,
        user_id: str,
        organization_id: str
    ):
        file_content = await file.read()

        # Validate file
        if not MediaUtils.validate_file(file_content, file.content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid file type. Allowed types:\n"
                    "Images: JPEG, PNG\n"
                    "Videos: MP4, MKV"
                )
            )

        # Create safe filename
        filename = MediaUtils.generate_filename(file.filename)

        # Upload to MinIO
        upload_result = await minio_service.upload_image(
            person_id=str(uuid.uuid4()),
            file_content=file_content,
            filename=filename
        )

        if not upload_result["success"]:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file to MinIO"
            )

        # Save file metadata to MongoDB
        doc = {
            "_id": ObjectId(),
            "file_id": str(uuid.uuid4()),
            "filename": filename,
            "file_type": file.content_type,
            "file_url": upload_result["url"],
            "uploaded_at": datetime.utcnow(),
            "uploaded_by": user_id,
            "organization_id": organization_id
        }

        await self.collection.insert_one(doc)

        return {
            "file_id": doc["file_id"],
            "filename": filename,
            "file_type": doc["file_type"],
            "file_url": doc["file_url"],
            "uploaded_at": doc["uploaded_at"],
            "uploaded_by": user_id,
            "organization_id": organization_id
        }
