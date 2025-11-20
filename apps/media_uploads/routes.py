"""
Media Upload API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File
from apps.media_uploads.controller import MediaUploadController
from apps.media_uploads.models import MediaUploadResponse
from middleware.auth import get_current_user
from config.database import get_database

router = APIRouter(prefix="/media", tags=["Media Upload"])


def get_media_controller(db=Depends(get_database)):
    return MediaUploadController(db)


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    current_user=Depends(get_current_user),
    controller: MediaUploadController = Depends(get_media_controller)
):
    results = []

    for file in files:
        uploaded = await controller.upload_media(
            file=file,
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"]
        )
        results.append(uploaded)

    return {"count": len(results), "files": results}
