"""
Media Upload Controller (Local File Storage Only)
"""
from fastapi import UploadFile, HTTPException, status
from datetime import datetime
import uuid
import os
from bson import ObjectId

from apps.media_uploads.utils import MediaUtils


class MediaUploadController:
    def __init__(self, db):
        self.collection = db.media_uploads
        self.upload_dir = "uploads/media"
        os.makedirs(self.upload_dir, exist_ok=True)

    def serialize(self, doc: dict):
        """Convert ObjectId → str"""
        doc["_id"] = str(doc["_id"])
        return doc

    # -------------------------------------------------------------
    # CREATE
    # -------------------------------------------------------------
    async def upload_media(self, file: UploadFile, user_id: str, organization_id: str):

        file_content = await file.read()

        if not MediaUtils.validate_file(file_content, file.content_type):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Allowed: JPEG, PNG, MP4, MKV"
            )

        filename = MediaUtils.generate_filename(file.filename)
        file_path = os.path.join(self.upload_dir, filename)

        # Save file locally
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
        except Exception as e:
            raise HTTPException(500, f"Cannot save file: {str(e)}")

        file_url = f"/{self.upload_dir}/{filename}"

        doc = {
            "_id": ObjectId(),
            "file_id": str(uuid.uuid4()),
            "filename": filename,
            "file_type": file.content_type,
            "file_url": file_url,
            "uploaded_at": datetime.utcnow(),
            "uploaded_by": user_id,
            "organization_id": organization_id
        }

        await self.collection.insert_one(doc)
        return self.serialize(doc)

    # -------------------------------------------------------------
    # READ (GET SINGLE MEDIA)
    # -------------------------------------------------------------
    async def get_media(self, file_id: str):
        media = await self.collection.find_one({"file_id": file_id})
        if not media:
            raise HTTPException(404, "Media not found")
        return self.serialize(media)

    # -------------------------------------------------------------
    # LIST ALL MEDIA (by organization)
    # -------------------------------------------------------------
    async def list_media(self, organization_id: str):
        media_cursor = self.collection.find({"organization_id": organization_id})
        media_list = await media_cursor.to_list(length=None)
        return [self.serialize(m) for m in media_list]

    # -------------------------------------------------------------
    # UPDATE (replace file)
    # -------------------------------------------------------------
    async def update_media(self, file_id: str, new_file: UploadFile):

        media = await self.collection.find_one({"file_id": file_id})
        if not media:
            raise HTTPException(404, "Media not found")

        # Delete old file
        old_path = media["file_url"].lstrip("/")
        if os.path.exists(old_path):
            os.remove(old_path)

        # Save new file
        file_content = await new_file.read()

        if not MediaUtils.validate_file(file_content, new_file.content_type):
            raise HTTPException(400, "Invalid file type")

        new_filename = MediaUtils.generate_filename(new_file.filename)
        new_path = os.path.join(self.upload_dir, new_filename)

        with open(new_path, "wb") as f:
            f.write(file_content)

        new_url = f"/{self.upload_dir}/{new_filename}"

        # Update DB
        await self.collection.update_one(
            {"file_id": file_id},
            {
                "$set": {
                    "filename": new_filename,
                    "file_type": new_file.content_type,
                    "file_url": new_url,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        updated_doc = await self.collection.find_one({"file_id": file_id})
        return self.serialize(updated_doc)

    # -------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------
    async def delete_media(self, file_id: str):

        media = await self.collection.find_one({"file_id": file_id})
        if not media:
            raise HTTPException(404, "Media not found")

        # Delete file locally
        file_path = media["file_url"].lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

        # Delete DB entry
        await self.collection.delete_one({"file_id": file_id})

        return {"success": True, "message": "Media deleted successfully"}
