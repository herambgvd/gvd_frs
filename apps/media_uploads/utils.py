"""
Utility functions for media upload
"""
import uuid

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/mkv"]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class MediaUtils:

    @staticmethod
    def validate_file(file_content: bytes, content_type: str) -> bool:
        """Validate file size and type (only jpg/png/mp4/mkv allowed)."""

        # 1. Size check
        if len(file_content) > MAX_FILE_SIZE:
            return False

        # 2. Type check
        if content_type in ALLOWED_IMAGE_TYPES:
            return True

        if content_type in ALLOWED_VIDEO_TYPES:
            return True

        return False

    @staticmethod
    def generate_filename(original_name: str) -> str:
        ext = original_name.split(".")[-1]
        return f"{uuid.uuid4()}.{ext}"
