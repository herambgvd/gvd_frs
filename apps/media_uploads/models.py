"""
Media Upload Models
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MediaUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    file_url: str
    uploaded_at: datetime
    user_id: str
    organization_id: str
