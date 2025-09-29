"""
Tenant API endpoints with license key authentication and async operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.security import (
    verify_license_key,
    require_admin_permission,
    require_permission,
    LicenseKeyData
)
from app.services.tenant_service import TenantService
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantSummary,
    TenantStats
)
from app.models.tenant import TenantStatus
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post(
    "/",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant"
)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_admin_permission)
):
    """Create a new tenant. Requires admin permission."""
    try:
        tenant_service = TenantService(db)
        tenant = await tenant_service.create_tenant(tenant_data)

        logger.info(
            f"Tenant created by license: {license_data.license_key[:16]}...",
            tenant_id=tenant.id,
            tenant_name=tenant.name
        )

        return tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[TenantSummary],
    summary="List all tenants"
)
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[TenantStatus] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_permission("read"))
):
    """List tenants with pagination and optional status filtering. Requires read permission."""
    tenant_service = TenantService(db)
    tenants = await tenant_service.list_tenants(skip=skip, limit=limit, status=status_filter)

    logger.info(
        f"Tenants listed by license: {license_data.license_key[:16]}...",
        count=len(tenants),
        skip=skip,
        limit=limit
    )

    return tenants


@router.get(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Get tenant by ID"
)
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_permission("read"))
):
    """Get a specific tenant by ID. Requires read permission."""
    tenant_service = TenantService(db)
    tenant = await tenant_service.get_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )

    logger.info(
        f"Tenant retrieved by license: {license_data.license_key[:16]}...",
        tenant_id=tenant_id
    )

    return tenant


@router.put(
    "/{tenant_id}",
    response_model=TenantResponse,
    summary="Update tenant"
)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_permission("write"))
):
    """Update tenant information. Requires write permission."""
    try:
        tenant_service = TenantService(db)
        tenant = await tenant_service.update_tenant(tenant_id, tenant_data)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID '{tenant_id}' not found"
            )

        logger.info(
            f"Tenant updated by license: {license_data.license_key[:16]}...",
            tenant_id=tenant_id
        )

        return tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant"
)
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_admin_permission)
):
    """Delete a tenant. Requires admin permission."""
    tenant_service = TenantService(db)
    success = await tenant_service.delete_tenant(tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )

    logger.info(
        f"Tenant deleted by license: {license_data.license_key[:16]}...",
        tenant_id=tenant_id
    )


@router.post(
    "/{tenant_id}/activate",
    response_model=TenantResponse,
    summary="Activate tenant"
)
async def activate_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_admin_permission)
):
    """Activate a tenant. Requires admin permission."""
    tenant_service = TenantService(db)
    tenant = await tenant_service.activate_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )

    logger.info(
        f"Tenant activated by license: {license_data.license_key[:16]}...",
        tenant_id=tenant_id
    )

    return tenant


@router.post(
    "/{tenant_id}/deactivate",
    response_model=TenantResponse,
    summary="Deactivate tenant"
)
async def deactivate_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_admin_permission)
):
    """Deactivate a tenant. Requires admin permission."""
    tenant_service = TenantService(db)
    tenant = await tenant_service.deactivate_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )

    logger.info(
        f"Tenant deactivated by license: {license_data.license_key[:16]}...",
        tenant_id=tenant_id
    )

    return tenant


@router.post(
    "/{tenant_id}/suspend",
    response_model=TenantResponse,
    summary="Suspend tenant"
)
async def suspend_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_admin_permission)
):
    """Suspend a tenant. Requires admin permission."""
    tenant_service = TenantService(db)
    tenant = await tenant_service.suspend_tenant(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )

    logger.info(
        f"Tenant suspended by license: {license_data.license_key[:16]}...",
        tenant_id=tenant_id
    )

    return tenant


@router.get(
    "/stats/summary",
    response_model=TenantStats,
    summary="Get tenant statistics"
)
async def get_tenant_stats(
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_permission("read"))
):
    """Get tenant statistics. Requires read permission."""
    tenant_service = TenantService(db)
    stats = await tenant_service.get_tenant_stats()

    logger.info(
        f"Tenant stats retrieved by license: {license_data.license_key[:16]}..."
    )

    return stats


@router.post(
    "/{tenant_id}/users/increment",
    response_model=TenantResponse,
    summary="Increment user count"
)
async def increment_user_count(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_permission("write"))
):
    """Increment user count for a tenant. Requires write permission."""
    try:
        tenant_service = TenantService(db)
        tenant = await tenant_service.increment_user_count(tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID '{tenant_id}' not found"
            )

        logger.info(
            f"User count incremented by license: {license_data.license_key[:16]}...",
            tenant_id=tenant_id,
            current_users=tenant.current_users
        )

        return tenant
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{tenant_id}/users/decrement",
    response_model=TenantResponse,
    summary="Decrement user count"
)
async def decrement_user_count(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_permission("write"))
):
    """Decrement user count for a tenant. Requires write permission."""
    tenant_service = TenantService(db)
    tenant = await tenant_service.decrement_user_count(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID '{tenant_id}' not found"
        )

    logger.info(
        f"User count decremented by license: {license_data.license_key[:16]}...",
        tenant_id=tenant_id,
        current_users=tenant.current_users
    )

    return tenant
