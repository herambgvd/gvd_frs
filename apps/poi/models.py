"""
Pydantic models for POI (Person of Interest) management
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import uuid4


class POIBase(BaseModel):
    """Base POI model with common fields"""
    
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name of the person")
    gender: Literal["male", "female", "other"] = Field(..., description="Gender of the person")
    age: int = Field(..., ge=0, le=120, description="Age of the person")
    additional_info: Optional[str] = Field(None, max_length=1000, description="Any additional information about the person")
    tagged_watchlist_id: str = Field(..., description="The watchlist/group ID this person is tagged to (required)")


class POICreate(POIBase):
    """Model for creating a new POI"""
    
    organization_id: str = Field(..., description="Organization ID that owns this POI")
    created_by: str = Field(..., description="User ID who created the POI")
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip().title()


class POIUpdate(BaseModel):
    """Model for updating an existing POI"""
    
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    gender: Optional[Literal["male", "female", "other"]] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    additional_info: Optional[str] = Field(None, max_length=1000)
    tagged_watchlist_id: Optional[str] = None

    @validator('full_name')
    def validate_full_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip().title() if v else v

class POIInDB(POIBase):
    """Model representing a POI as stored in database"""
    
    person_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the person")
    organization_id: str
    created_by: str
    updated_by: Optional[str] = None
    person_image_path: Optional[str] = Field(None, description="File path to person's image")
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra='forbid'
    )


class POIResponse(BaseModel):
    """Model for POI API responses"""
    
    person_id: str
    full_name: str
    gender: Literal["male", "female", "other"]
    age: int
    additional_info: Optional[str]
    tagged_watchlist_id: str
    organization_id: str
    created_by: str
    updated_by: Optional[str]
    person_image_path: Optional[str]
    person_image_url: Optional[str] = None  # Will be populated with actual URL
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    
    # Watchlist information (populated from join)
    watchlist_info: Optional[dict] = None

    @classmethod
    def from_db(cls, poi_doc: dict, base_url: str = None) -> "POIResponse":
        """Convert database document to response model"""
        person_image_url = None
        if poi_doc.get("person_image_path") and base_url:
            person_image_url = f"{base_url}/api/poi/{poi_doc['person_id']}/image"
            
        return cls(
            person_id=poi_doc["person_id"],
            full_name=poi_doc["full_name"],
            gender=poi_doc["gender"],
            age=poi_doc["age"],
            additional_info=poi_doc.get("additional_info"),
            tagged_watchlist_id=poi_doc["tagged_watchlist_id"],
            organization_id=poi_doc["organization_id"],
            created_by=poi_doc["created_by"],
            updated_by=poi_doc.get("updated_by"),
            person_image_path=poi_doc.get("person_image_path"),
            person_image_url=person_image_url,
            created_at=poi_doc["created_at"],
            updated_at=poi_doc.get("updated_at"),
            is_active=poi_doc.get("is_active", True),
            watchlist_info=poi_doc.get("watchlist_info")
        )


class POIListResponse(BaseModel):
    """Response model for listing POIs"""
    
    persons: List[POIResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int


class POIQuery(BaseModel):
    """Query parameters for filtering POIs"""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    search: Optional[str] = Field(None, max_length=100, description="Search term for person name")
    gender: Optional[Literal["male", "female", "other"]] = Field(None, description="Filter by gender")
    min_age: Optional[int] = Field(None, ge=0, le=120, description="Minimum age filter")
    max_age: Optional[int] = Field(None, ge=0, le=120, description="Maximum age filter")
    tagged_watchlist_id: Optional[str] = Field(None, description="Filter by tagged watchlist/group")
    is_active: Optional[bool] = Field(default=True, description="Filter by active status")
    organization_id: Optional[str] = Field(None, description="Filter by organization ID")
    
    @validator('max_age')
    def validate_age_range(cls, v, values):
        min_age = values.get('min_age')
        if min_age is not None and v is not None and v < min_age:
            raise ValueError('max_age must be greater than or equal to min_age')
        return v


class POIImageUpload(BaseModel):
    """Model for handling image upload responses"""
    
    person_id: str
    image_path: str
    image_url: str
    message: str


class POIBulkOperation(BaseModel):
    """Model for bulk operations on POIs"""
    
    person_ids: List[str] = Field(..., min_items=1, description="List of person IDs to operate on")
    operation: Literal["activate", "deactivate", "delete"] = Field(..., description="Operation to perform")


class POIBulkResponse(BaseModel):
    """Response model for bulk operations"""
    
    success_count: int
    failed_count: int
    failed_ids: List[str]
    message: str
