import uuid
from config.settings import settings
from s3_service.rustfs_client import get_s3_client, get_public_url

class RustFSService:

    def __init__(self):
        self.client = get_s3_client()
        self.bucket = settings.RUSTFS_BUCKET   # must be "media"

    async def upload_media_file(self, file_content: bytes, filename: str):
        """Upload from media_uploads app"""
        object_name = f"media_uploads/{uuid.uuid4()}-{filename}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=file_content,
            ContentType="image/jpeg"
        )

        return {
            "success": True,
            "image_url": get_public_url(object_name),
            "object_name": object_name,
            "file_size": len(file_content)
        }

    async def upload_poi_file(self, file_content: bytes, filename: str):
        """Upload from poi app"""
        object_name = f"poi/{uuid.uuid4()}-{filename}"

        self.client.put_object(
            Bucket=self.bucket,
            Key=object_name,
            Body=file_content,
            ContentType="image/jpeg"
        )

        return {
            "success": True,
            "image_url": get_public_url(object_name),
            "object_name": object_name,
            "file_size": len(file_content)
        }

    async def delete_image(self, object_name: str):
        self.client.delete_object(
            Bucket=self.bucket,
            Key=object_name
        )
        return {"success": True}
