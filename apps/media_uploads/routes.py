"""
Media Upload API Routes
"""
from fastapi import APIRouter, Depends, UploadFile, File
from apps.media_uploads.controller import MediaUploadController
from middleware.auth import get_current_user
from config.database import get_database

router = APIRouter(prefix="/media", tags=["Media Upload"])


def get_media_controller(db=Depends(get_database)):
    return MediaUploadController(db)

# -------------------------------------------------------------
# CREATE MULTIPLE
# -------------------------------------------------------------
@router.post("/upload-multiple")
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    current_user=Depends(get_current_user),
    controller: MediaUploadController = Depends(get_media_controller)
):
    results = []
    for f in files:
        results.append(
            await controller.upload_media(
                file=f,
                user_id=current_user["user_id"],
                organization_id=current_user["organization_id"]
            )
        )
    return {"count": len(results), "files": results}

# -------------------------------------------------------------
# GET SINGLE MEDIA
# -------------------------------------------------------------
@router.get("/{file_id}")
async def get_media(
    file_id: str,
    current_user=Depends(get_current_user),
    controller: MediaUploadController = Depends(get_media_controller)
):
    return await controller.get_media(file_id)

# -------------------------------------------------------------
# LIST ALL MEDIA
# -------------------------------------------------------------
@router.get("/")
async def list_media(
    current_user=Depends(get_current_user),
    controller: MediaUploadController = Depends(get_media_controller)
):
    return await controller.list_media(current_user["organization_id"])

# -------------------------------------------------------------
# UPDATE MEDIA (replace file)
# -------------------------------------------------------------
@router.put("/{file_id}")
async def update_media(
    file_id: str,
    new_file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    controller: MediaUploadController = Depends(get_media_controller)
):
    return await controller.update_media(file_id, new_file)

# -------------------------------------------------------------
# DELETE MEDIA
# -------------------------------------------------------------
@router.delete("/{file_id}")
async def delete_media(
    file_id: str,
    current_user=Depends(get_current_user),
    controller: MediaUploadController = Depends(get_media_controller)
):
    return await controller.delete_media(file_id)
