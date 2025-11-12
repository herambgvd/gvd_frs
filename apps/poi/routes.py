"""
POI (Person of Interest) API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer
from typing import List, Optional

from apps.poi.controller import POIController
from apps.poi.models import (
    POICreate, POIUpdate, POIResponse, POIListResponse, POIQuery,
    POIBulkOperation, POIBulkResponse, POIImageUpload
)
from middleware.auth import get_current_user
from config.database import get_database

# Initialize router
router = APIRouter(prefix="/api/poi", tags=["POI Management"])
security = HTTPBearer()


def get_poi_controller(db=Depends(get_database)) -> POIController:
    """Dependency to get POI controller"""
    return POIController(db["client"], db["db_name"])


@router.post("/", response_model=POIResponse, status_code=status.HTTP_201_CREATED)
async def create_poi(
    poi_data: POICreate,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Create a new Person of Interest
    
    - **full_name**: Full name of the person (required)
    - **gender**: Gender (male/female/other) (required)  
    - **age**: Age of the person (0-120) (required)
    - **additional_info**: Additional information about the person (optional)
    - **tagged_watchlist_id**: ID of watchlist to tag this person to (optional)
    - **organization_id**: Organization ID (required)
    - **created_by**: User ID who created this POI (required)
    """
    return await controller.create_poi(poi_data, current_user["user_id"])


@router.get("/", response_model=POIListResponse)
async def list_pois(
    page: int = 1,
    limit: int = 20,
    search: Optional[str] = None,
    gender: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    tagged_watchlist_id: Optional[str] = None,
    is_active: Optional[bool] = True,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    List all POIs with filtering and pagination
    
    - **page**: Page number (default: 1)
    - **limit**: Number of items per page (default: 20, max: 100)
    - **search**: Search term for person name or additional info
    - **gender**: Filter by gender (male/female/other)
    - **min_age**: Minimum age filter
    - **max_age**: Maximum age filter  
    - **tagged_watchlist_id**: Filter by watchlist ID
    - **is_active**: Filter by active status (default: true)
    """
    query_params = POIQuery(
        page=page,
        limit=limit,
        search=search,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        tagged_watchlist_id=tagged_watchlist_id,
        is_active=is_active,
        organization_id=current_user["organization_id"]
    )
    
    return await controller.list_pois(query_params, current_user["organization_id"])


@router.get("/{person_id}", response_model=POIResponse)
async def get_poi(
    person_id: str,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Get a specific POI by ID
    
    - **person_id**: Unique identifier of the person
    """
    return await controller.get_poi_by_id(
        person_id, 
        current_user["organization_id"],
        include_watchlist_info=True
    )


@router.put("/{person_id}", response_model=POIResponse)
async def update_poi(
    person_id: str,
    poi_update: POIUpdate,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Update a POI
    
    - **person_id**: Unique identifier of the person
    - **poi_update**: Updated POI data (only provided fields will be updated)
    """
    return await controller.update_poi(
        person_id,
        poi_update,
        current_user["organization_id"],
        current_user["user_id"]
    )


@router.delete("/{person_id}")
async def delete_poi(
    person_id: str,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Delete a POI (soft delete)
    
    - **person_id**: Unique identifier of the person
    """
    return await controller.delete_poi(person_id, current_user["organization_id"])


@router.post("/{person_id}/image", response_model=dict)
async def upload_person_image(
    person_id: str,
    file: UploadFile = File(..., description="Person image file"),
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Upload image for a person
    
    - **person_id**: Unique identifier of the person
    - **file**: Image file (JPEG, PNG, GIF, WebP)
    """
    # Validate file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size too large. Maximum size is 10MB."
        )
    
    return await controller.upload_person_image(
        person_id,
        current_user["organization_id"],
        file
    )


@router.get("/{person_id}/image")
async def get_person_image(
    person_id: str,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Get person image
    
    - **person_id**: Unique identifier of the person
    """
    file_path, content_type = await controller.get_person_image(
        person_id,
        current_user["organization_id"]
    )
    
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=f"person_{person_id}.jpg"
    )


@router.delete("/{person_id}/image")
async def delete_person_image(
    person_id: str,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Delete person image
    
    - **person_id**: Unique identifier of the person
    """
    # Get POI to check if image exists
    poi = await controller.get_poi_by_id(person_id, current_user["organization_id"], False)
    
    if not poi.person_image_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image found for this person"
        )
    
    # Update POI to remove image reference
    update_data = POIUpdate(person_image_path=None)
    await controller.update_poi(
        person_id,
        update_data,
        current_user["organization_id"],
        current_user["user_id"]
    )
    
    # Delete physical file
    import os
    if os.path.exists(poi.person_image_path):
        os.remove(poi.person_image_path)
    
    return {"message": "Person image deleted successfully"}


@router.post("/bulk", response_model=POIBulkResponse)
async def bulk_poi_operations(
    bulk_operation: POIBulkOperation,
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Perform bulk operations on POIs
    
    - **person_ids**: List of person IDs to operate on
    - **operation**: Operation to perform (activate/deactivate/delete)
    """
    return await controller.bulk_operations(bulk_operation, current_user["organization_id"])


@router.get("/statistics/overview")
async def get_poi_statistics(
    current_user=Depends(get_current_user),
    controller: POIController = Depends(get_poi_controller)
):
    """
    Get POI statistics overview
    """
    # Get total counts by various criteria
    organization_id = current_user["organization_id"]
    
    pipeline = [
        {"$match": {"organization_id": organization_id}},
        {
            "$group": {
                "_id": None,
                "total_pois": {"$sum": 1},
                "active_pois": {
                    "$sum": {"$cond": [{"$eq": ["$is_active", True]}, 1, 0]}
                },
                "inactive_pois": {
                    "$sum": {"$cond": [{"$eq": ["$is_active", False]}, 1, 0]}
                },
                "with_images": {
                    "$sum": {"$cond": [{"$ne": ["$person_image_path", None]}, 1, 0]}
                },
                "male_count": {
                    "$sum": {"$cond": [{"$eq": ["$gender", "male"]}, 1, 0]}
                },
                "female_count": {
                    "$sum": {"$cond": [{"$eq": ["$gender", "female"]}, 1, 0]}
                },
                "other_gender_count": {
                    "$sum": {"$cond": [{"$eq": ["$gender", "other"]}, 1, 0]}
                },
                "avg_age": {"$avg": "$age"}
            }
        }
    ]
    
    result = await controller.collection.aggregate(pipeline).to_list(length=1)
    stats = result[0] if result else {
        "total_pois": 0,
        "active_pois": 0,
        "inactive_pois": 0,
        "with_images": 0,
        "male_count": 0,
        "female_count": 0,
        "other_gender_count": 0,
        "avg_age": 0
    }
    
    # Remove the _id field
    if "_id" in stats:
        del stats["_id"]
    
    return {
        "organization_id": organization_id,
        "statistics": stats
    }


# Export router
__all__ = ["router"]
