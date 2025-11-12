"""
Pydantic models for Group management
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, Annotated
from datetime import datetime


class GroupBase(BaseModel):
    """Base Group model with common fields"""
    
    group_name: str = Field(..., min_length=1, max_length=100, description="Name of the group")
    display_color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code for display (e.g., #FF5733)")
    sound_on_alert: bool = Field(default=False, description="Whether to play sound on alert")
    watchlist_type: Literal["whitelist", "blacklist"] = Field(..., description="Type of watchlist: whitelist or blacklist")
    notes: Optional[str] = Field(None, max_length=500, description="Optional notes about the group")


class GroupCreate(GroupBase):
    """Model for creating a new group"""
    
    organization_id: str = Field(..., description="Organization ID that owns this group")
    created_by: str = Field(..., description="User ID who created the group")


class GroupUpdate(BaseModel):
    """Model for updating an existing group"""
    
    group_name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    sound_on_alert: Optional[bool] = None
    watchlist_type: Optional[Literal["whitelist", "blacklist"]] = None
    notes: Optional[str] = Field(None, max_length=500)


class GroupInDB(GroupBase):
    """Model representing a group as stored in database"""
    
    id: str = Field(..., alias="_id", description="Group ID")
    organization_id: str
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra='forbid'
    )


class GroupResponse(BaseModel):
    """Model for group API responses"""
    
    id: str
    group_name: str
    display_color: str
    sound_on_alert: bool
    watchlist_type: Literal["whitelist", "blacklist"]
    notes: Optional[str]
    organization_id: str
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    @classmethod
    def from_db(cls, group_doc: dict) -> "GroupResponse":
        """Convert database document to response model"""
        return cls(
            id=str(group_doc["_id"]),
            group_name=group_doc["group_name"],
            display_color=group_doc["display_color"],
            sound_on_alert=group_doc["sound_on_alert"],
            watchlist_type=group_doc["watchlist_type"],
            notes=group_doc.get("notes"),
            organization_id=group_doc["organization_id"],
            created_by=group_doc["created_by"],
            updated_by=group_doc.get("updated_by"),
            created_at=group_doc["created_at"],
            updated_at=group_doc.get("updated_at"),
            is_active=group_doc.get("is_active", True)
        )


class GroupListResponse(BaseModel):
    """Response model for listing groups"""
    
    groups: list[GroupResponse]
    total_count: int
    page: int
    limit: int
    total_pages: int


class GroupQuery(BaseModel):
    """Query parameters for filtering groups"""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    search: Optional[str] = Field(None, max_length=100, description="Search term for group name or notes")
    watchlist_type: Optional[Literal["whitelist", "blacklist"]] = Field(None, description="Filter by watchlist type")
    is_active: Optional[bool] = Field(default=True, description="Filter by active status")
    organization_id: Optional[str] = Field(None, description="Filter by organization ID")