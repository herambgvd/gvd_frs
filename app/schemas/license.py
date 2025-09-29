"""
License Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class LicenseBase(BaseModel):
    """Base license schema with common fields."""
    client_name: str = Field(..., description="Name of the client")
    client_id: str = Field(..., description="Unique client identifier")
    permissions: List[str] = Field(default=["read"], description="List of permissions")
    is_active: bool = Field(default=True, description="Whether the license is active")
    expires_at: Optional[datetime] = Field(None, description="License expiration datetime")
    usage_limit: Optional[int] = Field(None, description="Maximum usage limit")
    tenant_id: Optional[str] = Field(None, description="Associated tenant ID")


class LicenseCreate(LicenseBase):
    """Schema for creating a new license."""
    expires_in_days: int = Field(default=365, description="License validity period in days")


class LicenseUpdate(BaseModel):
    """Schema for updating a license."""
    client_name: Optional[str] = Field(None, description="Name of the client")
    permissions: Optional[List[str]] = Field(None, description="List of permissions")
    is_active: Optional[bool] = Field(None, description="Whether the license is active")
    expires_at: Optional[datetime] = Field(None, description="License expiration datetime")
    usage_limit: Optional[int] = Field(None, description="Maximum usage limit")
    tenant_id: Optional[str] = Field(None, description="Associated tenant ID")


class LicenseResponse(LicenseBase):
    """Schema for license response data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    license_key: str
    current_usage: int
    created_at: datetime
    updated_at: datetime


class LicenseInfo(BaseModel):
    """Schema for license information without sensitive data."""
    model_config = ConfigDict(from_attributes=True)

    client_name: str
    client_id: str
    permissions: List[str]
    is_active: bool
    expires_at: Optional[datetime]
    current_usage: int
    usage_limit: Optional[int]
    tenant_id: Optional[str]
    created_at: datetime


class LicenseValidationResponse(BaseModel):
    """Schema for license validation response."""
    valid: bool
    message: str
    license_info: Optional[LicenseInfo] = None


class LicenseStats(BaseModel):
    """Schema for license statistics."""
    total_licenses: int
    active_licenses: int
    expired_licenses: int
    usage_summary: dict
