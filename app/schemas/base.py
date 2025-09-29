"""
Base Pydantic schemas for the application.
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseSchema):
    """Mixin for models with timestamp fields."""

    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class APIResponse(BaseSchema):
    """Standard API response format."""

    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field("Success", description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PaginationParams(BaseSchema):
    """Standard pagination parameters."""

    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class PaginatedResponse(APIResponse):
    """Paginated response format."""

    data: list = Field(default_factory=list, description="List of items")
    meta: Dict[str, Any] = Field(
        default_factory=lambda: {
            "total": 0,
            "skip": 0,
            "limit": 100,
            "has_next": False,
            "has_previous": False,
        },
        description="Pagination metadata"
    )


class HealthCheck(BaseSchema):
    """Health check response."""

    status: str = Field("healthy", description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(description="Application version")
    environment: str = Field(description="Current environment")
    database: str = Field("connected", description="Database connection status")
    redis: str = Field("connected", description="Redis connection status")
