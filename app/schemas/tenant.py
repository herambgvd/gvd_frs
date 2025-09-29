"""
Tenant Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.tenant import TenantStatus


class TenantBase(BaseModel):
    """Base tenant schema with common fields."""
    name: str = Field(..., description="Tenant name")
    description: Optional[str] = Field(None, description="Tenant description")
    domain: Optional[str] = Field(None, description="Tenant domain")
    status: TenantStatus = Field(default=TenantStatus.ACTIVE, description="Tenant status")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")
    max_users: Optional[int] = Field(None, description="Maximum number of users")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")


class TenantCreate(TenantBase):
    """Schema for creating a new tenant."""
    id: str = Field(..., description="Unique tenant identifier")
    created_by: Optional[str] = Field(None, description="Creator identifier")


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    name: Optional[str] = Field(None, description="Tenant name")
    description: Optional[str] = Field(None, description="Tenant description")
    domain: Optional[str] = Field(None, description="Tenant domain")
    status: Optional[TenantStatus] = Field(None, description="Tenant status")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")
    max_users: Optional[int] = Field(None, description="Maximum number of users")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")


class TenantResponse(TenantBase):
    """Schema for tenant response data."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    current_users: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]


class TenantSummary(BaseModel):
    """Schema for tenant summary information."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: TenantStatus
    current_users: int
    max_users: Optional[int]
    domain: Optional[str]
    created_at: datetime


class TenantStats(BaseModel):
    """Schema for tenant statistics."""
    total_tenants: int
    active_tenants: int
    inactive_tenants: int
    suspended_tenants: int
    pending_tenants: int
    total_users_across_tenants: int
