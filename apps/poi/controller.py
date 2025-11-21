"""
POI (Person of Interest) Controller
Handles all business logic for POI management
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import HTTPException, UploadFile, status
from bson import ObjectId

from apps.poi.models import (
    POICreate, POIUpdate, POIInDB, POIResponse, POIListResponse, 
    POIQuery, POIBulkOperation, POIBulkResponse
)
from s3_service.rustfs_service import RustFSService

rustfs_service = RustFSService()



class POIController:
    def __init__(self, db):
        self.db = db
        self.collection = db.poi_persons
        self.watchlist_collection = db.groups


    async def create_poi(
        self,
        poi_data: POICreate,
        created_by_user_id: str,
        organization_id: str
    ) -> POIResponse:
        """
        Create a new POI and validate its watchlist/group reference.
        """
        try:
            # ✅ Validate tagged_watchlist_id (required)
            if not ObjectId.is_valid(poi_data.tagged_watchlist_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid watchlist/group ID format"
                )

            watchlist = await self.watchlist_collection.find_one({
                "_id": ObjectId(poi_data.tagged_watchlist_id),
                "organization_id": organization_id,
                "is_active": True
            })
            if not watchlist:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Watchlist/group not found or not active"
                )

            # ✅ Prepare POI document
            poi_doc = POIInDB(
                person_id=str(uuid.uuid4()),
                full_name=poi_data.full_name.strip().title(),
                gender=poi_data.gender,
                age=poi_data.age,
                additional_info=poi_data.additional_info,
                tagged_watchlist_id=poi_data.tagged_watchlist_id,
                organization_id=organization_id,
                created_by=created_by_user_id,
                created_at=datetime.utcnow(),
                is_active=True
            ).dict(by_alias=True)

            # ✅ Insert into MongoDB
            result = await self.collection.insert_one(poi_doc)
            if not result.acknowledged:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create POI"
                )

            # ✅ Fetch and return created document
            created_poi = await self.collection.find_one({"person_id": poi_doc["person_id"]})
            return POIResponse.from_db(created_poi)

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while creating POI: {str(e)}"
            )
    
    async def get_poi_by_id(self, person_id: str, organization_id: str, include_watchlist_info: bool = True) -> POIResponse:
        """Get POI by ID"""
        try:
            # Build aggregation pipeline for watchlist info
            pipeline = [
                {
                    "$match": {
                        "person_id": person_id,
                        "organization_id": organization_id,
                        "is_active": True
                    }
                }
            ]
            
            if include_watchlist_info:
                pipeline.extend([
                    {
                        "$lookup": {
                            "from": "groups",
                            "localField": "tagged_watchlist_id",
                            "foreignField": "_id",
                            "as": "watchlist_info"
                        }
                    },
                    {
                        "$addFields": {
                            "watchlist_info": {
                                "$arrayElemAt": ["$watchlist_info", 0]
                            }
                        }
                    }
                ])
            
            cursor = self.collection.aggregate(pipeline)
            poi_doc = await cursor.to_list(length=1)
            
            if not poi_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="POI not found"
                )
            
            return POIResponse.from_db(poi_doc[0])
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while retrieving POI: {str(e)}"
            )
    
    async def update_poi(self, person_id: str, poi_update: POIUpdate, organization_id: str, updated_by_user_id: str) -> POIResponse:
        """Update POI"""
        try:
            # Check if POI exists
            existing_poi = await self.collection.find_one({
                "person_id": person_id,
                "organization_id": organization_id,
                "is_active": True
            })
            
            if not existing_poi:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="POI not found"
                )
            
            # Check if watchlist exists if provided
            if poi_update.tagged_watchlist_id:
                watchlist = await self.watchlist_collection.find_one({
                    "_id": ObjectId(poi_update.tagged_watchlist_id),
                    "organization_id": organization_id,
                    "is_active": True
                })
                if not watchlist:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Watchlist not found or not accessible"
                    )
            
            # Prepare update data
            update_data = {
                "updated_by": updated_by_user_id,
                "updated_at": datetime.utcnow()
            }
            
            # Add only provided fields
            update_fields = poi_update.dict(exclude_unset=True)
            update_data.update(update_fields)
            
            # Update POI
            result = await self.collection.update_one(
                {"person_id": person_id, "organization_id": organization_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="POI not found or no changes made"
                )
            
            # Return updated POI
            return await self.get_poi_by_id(person_id, organization_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while updating POI: {str(e)}"
            )
    
    async def delete_poi(self, person_id: str, organization_id: str) -> dict:
        """Soft delete POI"""
        try:
            result = await self.collection.update_one(
                {
                    "person_id": person_id,
                    "organization_id": organization_id,
                    "is_active": True
                },
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="POI not found"
                )
            
            # Delete image file if exists
            poi_doc = await self.collection.find_one({"person_id": person_id})
            if poi_doc and poi_doc.get("person_image_path"):
                try:
                    if os.path.exists(poi_doc["person_image_path"]):
                        os.remove(poi_doc["person_image_path"])
                except Exception:
                    pass  # Log this error but don't fail the deletion
            
            return {"message": "POI deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while deleting POI: {str(e)}"
            )
    
    async def list_pois(self, query_params: POIQuery, organization_id: str) -> POIListResponse:
        """List POIs with filtering and pagination"""
        try:
            # Build match criteria
            match_criteria = {
                "organization_id": organization_id,
                "is_active": query_params.is_active
            }
            
            # Add search filter
            if query_params.search:
                match_criteria["$or"] = [
                    {"full_name": {"$regex": query_params.search, "$options": "i"}},
                    {"additional_info": {"$regex": query_params.search, "$options": "i"}}
                ]
            
            # Add gender filter
            if query_params.gender:
                match_criteria["gender"] = query_params.gender
            
            # Add age filters
            age_filter = {}
            if query_params.min_age is not None:
                age_filter["$gte"] = query_params.min_age
            if query_params.max_age is not None:
                age_filter["$lte"] = query_params.max_age
            if age_filter:
                match_criteria["age"] = age_filter
            
            # Add watchlist filter
            if query_params.tagged_watchlist_id:
                match_criteria["tagged_watchlist_id"] = query_params.tagged_watchlist_id
            
            # Build aggregation pipeline
            pipeline = [
                {"$match": match_criteria},
                {
                    "$lookup": {
                        "from": "groups",
                        "localField": "tagged_watchlist_id",
                        "foreignField": "_id",
                        "as": "watchlist_info"
                    }
                },
                {
                    "$addFields": {
                        "watchlist_info": {
                            "$arrayElemAt": ["$watchlist_info", 0]
                        }
                    }
                },
                {"$sort": {"created_at": -1}}
            ]
            
            # Get total count
            count_pipeline = pipeline.copy()
            count_pipeline.append({"$count": "total"})
            count_result = await self.collection.aggregate(count_pipeline).to_list(length=1)
            total_count = count_result[0]["total"] if count_result else 0
            
            # Add pagination
            skip = (query_params.page - 1) * query_params.limit
            pipeline.extend([
                {"$skip": skip},
                {"$limit": query_params.limit}
            ])
            
            # Execute query
            cursor = self.collection.aggregate(pipeline)
            poi_docs = await cursor.to_list(length=query_params.limit)
            
            # Convert to response models
            pois = [POIResponse.from_db(doc) for doc in poi_docs]
            
            total_pages = (total_count + query_params.limit - 1) // query_params.limit
            
            return POIListResponse(
                persons=pois,
                total_count=total_count,
                page=query_params.page,
                limit=query_params.limit,
                total_pages=total_pages
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred while listing POIs: {str(e)}"
            )
    

    async def upload_person_image(self, person_id: str, organization_id: str, file: UploadFile) -> dict:
        try:
            # Validate file
            if not file.content_type.startswith("image/"):
                raise HTTPException(400, "File must be an image")

            # Check POI exists
            poi_doc = await self.collection.find_one({
                "person_id": person_id,
                "organization_id": organization_id,
                "is_active": True
            })

            if not poi_doc:
                raise HTTPException(404, "POI not found")

            # Read file
            file_content = await file.read()

            # Upload to RustFS
            upload_result = await rustfs_service.upload_poi_file(
                file_content=file_content,
                filename=file.filename
            )

            # Save file metadata
            update_data = {
                "person_image_url": upload_result["image_url"],
                "person_image_object_name": upload_result["object_name"],
                "updated_at": datetime.utcnow()
            }

            await self.collection.update_one(
                {"person_id": person_id, "organization_id": organization_id},
                {"$set": update_data}
            )

            return {
                "person_id": person_id,
                "image_url": upload_result["image_url"],
                "object_name": upload_result["object_name"],
                "file_size": upload_result["file_size"],
                "message": "Image uploaded successfully to RustFS"
            }

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                500,
                f"An error occurred while uploading image: {str(e)}"
            )

    # -------------------------------------------------------------
    # GET PERSON IMAGE URL
    # -------------------------------------------------------------
    async def get_person_image_url(self, person_id: str, organization_id: str) -> str:
        try:
            poi_doc = await self.collection.find_one({
                "person_id": person_id,
                "organization_id": organization_id,
                "is_active": True
            })

            if not poi_doc or not poi_doc.get("person_image_url"):
                raise HTTPException(404, "Person image not found")

            return poi_doc["person_image_url"]

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                500,
                f"An error occurred while retrieving image URL: {str(e)}"
            )

    # -------------------------------------------------------------
    # DELETE PERSON IMAGE (RustFS)
    # -------------------------------------------------------------
    async def delete_person_image(self, person_id: str, organization_id: str) -> dict:
        try:
            poi_doc = await self.collection.find_one({
                "person_id": person_id,
                "organization_id": organization_id,
                "is_active": True
            })

            if not poi_doc or not poi_doc.get("person_image_object_name"):
                raise HTTPException(404, "No image found for this person")

            object_name = poi_doc["person_image_object_name"]

            # Delete from RustFS
            await rustfs_service.delete_image(object_name)

            # Update DB
            await self.collection.update_one(
                {"person_id": person_id, "organization_id": organization_id},
                {"$set": {
                    "person_image_url": None,
                    "person_image_object_name": None,
                    "updated_at": datetime.utcnow()
                }}
            )

            return {"message": "Person image deleted successfully from RustFS"}

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                500,
                f"An error occurred while deleting image: {str(e)}"
            )

    async def bulk_operations(self, bulk_op: POIBulkOperation, organization_id: str) -> POIBulkResponse:
        """Perform bulk operations on POIs"""
        try:
            success_count = 0
            failed_ids = []
            
            for person_id in bulk_op.person_ids:
                try:
                    if bulk_op.operation == "activate":
                        result = await self.collection.update_one(
                            {"person_id": person_id, "organization_id": organization_id},
                            {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
                        )
                    elif bulk_op.operation == "deactivate":
                        result = await self.collection.update_one(
                            {"person_id": person_id, "organization_id": organization_id},
                            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
                        )
                    elif bulk_op.operation == "delete":
                        # Hard delete for bulk operations
                        result = await self.collection.delete_one({
                            "person_id": person_id, 
                            "organization_id": organization_id
                        })
                    
                    if result.modified_count > 0 or result.deleted_count > 0:
                        success_count += 1
                    else:
                        failed_ids.append(person_id)
                        
                except Exception:
                    failed_ids.append(person_id)
            
            failed_count = len(failed_ids)
            
            return POIBulkResponse(
                success_count=success_count,
                failed_count=failed_count,
                failed_ids=failed_ids,
                message=f"Bulk {bulk_op.operation} completed. {success_count} successful, {failed_count} failed."
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An error occurred during bulk operation: {str(e)}"
            )


