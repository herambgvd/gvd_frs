"""
Media Upload Controller (RustFS S3 Storage)
"""

import uuid
from fastapi import UploadFile, HTTPException
from datetime import datetime
from bson import ObjectId

from apps.media_uploads.utils import MediaUtils
from s3_service.rustfs_service import RustFSService

rustfs = RustFSService()


class MediaUploadController:

    def __init__(self, db):
        self.collection = db.media_uploads

    def serialize(self, doc: dict):
        doc["_id"] = str(doc["_id"])
        return doc

    # ============================================================
    # 1️⃣ UPLOAD MEDIA (IMAGE / VIDEO) → RustFS
    # ============================================================
    async def upload_media(self, file: UploadFile, user_id: str, organization_id: str):

        file_bytes = await file.read()

        if not MediaUtils.validate_file(file_bytes, file.content_type):
            raise HTTPException(400, "Invalid file type (Allowed: jpg, png, mp4, mkv)")

        # 🔥 Using correct RustFS method
        upload = await rustfs.upload_media_file(
            file_content=file_bytes,
            filename=file.filename
        )

        doc = {
            "_id": ObjectId(),
            "file_id": str(uuid.uuid4()),
            "filename": file.filename,
            "file_type": file.content_type,
            "file_url": upload["image_url"],
            "object_name": upload["object_name"],
            "file_size": upload["file_size"],
            "uploaded_at": datetime.utcnow(),
            "uploaded_by": user_id,
            "organization_id": organization_id
        }

        await self.collection.insert_one(doc)
        return self.serialize(doc)

    # ============================================================
    # 2️⃣ GET MEDIA
    # ============================================================
    async def get_media(self, file_id: str):
        media = await self.collection.find_one({"file_id": file_id})
        if not media:
            raise HTTPException(404, "Media not found")
        return self.serialize(media)

    # ============================================================
    # 3️⃣ LIST ALL MEDIA (BY ORG)
    # ============================================================
    async def list_media(self, organization_id: str):
        cursor = self.collection.find({"organization_id": organization_id})
        return [self.serialize(m) for m in await cursor.to_list(length=None)]

    # ============================================================
    # 4️⃣ UPDATE MEDIA (DELETE OLD THEN UPLOAD NEW)
    # ============================================================
    async def update_media(self, file_id: str, new_file: UploadFile):

        media = await self.collection.find_one({"file_id": file_id})
        if not media:
            raise HTTPException(404, "Media not found")

        # delete old file
        if media.get("object_name"):
            await rustfs.delete_image(media["object_name"])

        # upload new file
        file_bytes = await new_file.read()

        if not MediaUtils.validate_file(file_bytes, new_file.content_type):
            raise HTTPException(400, "Invalid file type")

        upload = await rustfs.upload_media_file(
            file_content=file_bytes,
            filename=new_file.filename
        )

        await self.collection.update_one(
            {"file_id": file_id},
            {"$set": {
                "filename": new_file.filename,
                "file_url": upload["image_url"],
                "file_type": new_file.content_type,
                "file_size": upload["file_size"],
                "object_name": upload["object_name"],
                "updated_at": datetime.utcnow()
            }}
        )

        updated = await self.collection.find_one({"file_id": file_id})
        return self.serialize(updated)

    # ============================================================
    # 5️⃣ DELETE MEDIA
    # ============================================================
    async def delete_media(self, file_id: str):

        media = await self.collection.find_one({"file_id": file_id})
        if not media:
            raise HTTPException(404, "Media not found")

        # delete from RustFS
        if media.get("object_name"):
            await rustfs.delete_image(media["object_name"])

        # delete DB
        await self.collection.delete_one({"file_id": file_id})

        return {"success": True, "message": "Media deleted successfully"}

    # ============================================================
    # 6️⃣ PERSON IMAGE UPLOAD → RustFS (POI)
    # ============================================================
    async def upload_person_image(self, person_id: str, organization_id: str, file: UploadFile):

        if not file.content_type.startswith("image/"):
            raise HTTPException(400, "Only image files allowed")

        file_bytes = await file.read()

        upload = await rustfs.upload_poi_file(
            file_content=file_bytes,
            filename=file.filename
        )

        await self.collection.update_one(
            {"person_id": person_id},
            {"$set": {
                "person_image_url": upload["image_url"],
                "person_image_object_name": upload["object_name"],
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )

        return upload

    # ============================================================
    # 7️⃣ DELETE PERSON IMAGE
    # ============================================================
    async def delete_person_image(self, person_id: str):

        poi = await self.collection.find_one({"person_id": person_id})

        if not poi or not poi.get("person_image_object_name"):
            raise HTTPException(404, "No image found")

        await rustfs.delete_image(poi["person_image_object_name"])

        await self.collection.update_one(
            {"person_id": person_id},
            {"$set": {
                "person_image_url": None,
                "person_image_object_name": None,
                "updated_at": datetime.utcnow()
            }}
        )

        return {"message": "Person image deleted"}
