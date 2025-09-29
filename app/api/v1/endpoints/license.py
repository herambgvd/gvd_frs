"""
License API endpoints with license key authentication and async operations.
"""
import json
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
from app.services.license_service import LicenseService
from app.schemas.license import (
    LicenseCreate,
    LicenseUpdate,
    LicenseResponse,
    LicenseInfo,
    LicenseValidationResponse,
    LicenseStats
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/licenses", tags=["licenses"])


@router.post(
    "/",
    response_model=LicenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new license"
)
async def create_license(
    license_data: LicenseCreate,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Create a new license. Requires admin permission."""
    try:
        license_service = LicenseService(db)
        license = await license_service.create_license(license_data)

        # Parse permissions for response
        if license.permissions:
            permissions = json.loads(license.permissions)
        else:
            permissions = []

        logger.info(
            f"License created by admin license: {admin_license.license_key[:16]}...",
            new_license_key=license.license_key[:16] + "...",
            client_id=license.client_id
        )

        return LicenseResponse(
            id=license.id,
            license_key=license.license_key,
            client_name=license.client_name,
            client_id=license.client_id,
            permissions=permissions,
            is_active=license.is_active,
            expires_at=license.expires_at,
            usage_limit=license.usage_limit,
            current_usage=license.current_usage,
            tenant_id=license.tenant_id,
            created_at=license.created_at,
            updated_at=license.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[LicenseResponse],
    summary="List all licenses"
)
async def list_licenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    tenant_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    license_data: LicenseKeyData = Depends(require_admin_permission)
):
    """List licenses with pagination and filtering. Requires admin permission."""
    license_service = LicenseService(db)
    licenses = await license_service.list_licenses(
        skip=skip,
        limit=limit,
        is_active=is_active,
        tenant_id=tenant_id
    )

    # Convert to response format
    response_licenses = []
    for license in licenses:
        permissions = json.loads(license.permissions) if license.permissions else []
        response_licenses.append(LicenseResponse(
            id=license.id,
            license_key=license.license_key,
            client_name=license.client_name,
            client_id=license.client_id,
            permissions=permissions,
            is_active=license.is_active,
            expires_at=license.expires_at,
            usage_limit=license.usage_limit,
            current_usage=license.current_usage,
            tenant_id=license.tenant_id,
            created_at=license.created_at,
            updated_at=license.updated_at
        ))

    logger.info(
        f"Licenses listed by admin license: {license_data.license_key[:16]}...",
        count=len(licenses),
        skip=skip,
        limit=limit
    )

    return response_licenses


@router.get(
    "/{license_id}",
    response_model=LicenseResponse,
    summary="Get license by ID"
)
async def get_license(
    license_id: int,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Get a specific license by ID. Requires admin permission."""
    license_service = LicenseService(db)
    license = await license_service.get_license(license_id)

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License with ID '{license_id}' not found"
        )

    permissions = json.loads(license.permissions) if license.permissions else []

    logger.info(
        f"License retrieved by admin license: {admin_license.license_key[:16]}...",
        license_id=license_id
    )

    return LicenseResponse(
        id=license.id,
        license_key=license.license_key,
        client_name=license.client_name,
        client_id=license.client_id,
        permissions=permissions,
        is_active=license.is_active,
        expires_at=license.expires_at,
        usage_limit=license.usage_limit,
        current_usage=license.current_usage,
        tenant_id=license.tenant_id,
        created_at=license.created_at,
        updated_at=license.updated_at
    )


@router.put(
    "/{license_id}",
    response_model=LicenseResponse,
    summary="Update license"
)
async def update_license(
    license_id: int,
    license_data: LicenseUpdate,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Update license information. Requires admin permission."""
    license_service = LicenseService(db)
    license = await license_service.update_license(license_id, license_data)

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License with ID '{license_id}' not found"
        )

    permissions = json.loads(license.permissions) if license.permissions else []

    logger.info(
        f"License updated by admin license: {admin_license.license_key[:16]}...",
        license_id=license_id
    )

    return LicenseResponse(
        id=license.id,
        license_key=license.license_key,
        client_name=license.client_name,
        client_id=license.client_id,
        permissions=permissions,
        is_active=license.is_active,
        expires_at=license.expires_at,
        usage_limit=license.usage_limit,
        current_usage=license.current_usage,
        tenant_id=license.tenant_id,
        created_at=license.created_at,
        updated_at=license.updated_at
    )


@router.delete(
    "/{license_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete license"
)
async def delete_license(
    license_id: int,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Delete a license. Requires admin permission."""
    license_service = LicenseService(db)
    success = await license_service.delete_license(license_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License with ID '{license_id}' not found"
        )

    logger.info(
        f"License deleted by admin license: {admin_license.license_key[:16]}...",
        license_id=license_id
    )


@router.post(
    "/validate",
    response_model=LicenseValidationResponse,
    summary="Validate license key"
)
async def validate_license_key(
    license_key: str = Query(..., description="License key to validate"),
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_permission("read"))
):
    """Validate a license key without incrementing usage. Requires read permission."""
    license_service = LicenseService(db)
    license = await license_service.get_license_by_key(license_key)

    if not license:
        return LicenseValidationResponse(
            valid=False,
            message="License key not found"
        )

    # Check validity without incrementing usage
    if not license.is_active:
        return LicenseValidationResponse(
            valid=False,
            message="License is inactive"
        )

    from datetime import datetime
    if license.expires_at and license.expires_at < datetime.utcnow():
        return LicenseValidationResponse(
            valid=False,
            message="License has expired"
        )

    if license.usage_limit and license.current_usage >= license.usage_limit:
        return LicenseValidationResponse(
            valid=False,
            message="License usage limit reached"
        )

    permissions = json.loads(license.permissions) if license.permissions else []

    license_info = LicenseInfo(
        client_name=license.client_name,
        client_id=license.client_id,
        permissions=permissions,
        is_active=license.is_active,
        expires_at=license.expires_at,
        current_usage=license.current_usage,
        usage_limit=license.usage_limit,
        tenant_id=license.tenant_id,
        created_at=license.created_at
    )

    logger.info(
        f"License validated by admin license: {admin_license.license_key[:16]}...",
        validated_license_key=license_key[:16] + "..."
    )

    return LicenseValidationResponse(
        valid=True,
        message="License is valid",
        license_info=license_info
    )


@router.post(
    "/{license_id}/revoke",
    response_model=LicenseResponse,
    summary="Revoke license"
)
async def revoke_license(
    license_id: int,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Revoke (deactivate) a license. Requires admin permission."""
    license_service = LicenseService(db)
    license = await license_service.revoke_license(license_id)

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License with ID '{license_id}' not found"
        )

    permissions = json.loads(license.permissions) if license.permissions else []

    logger.info(
        f"License revoked by admin license: {admin_license.license_key[:16]}...",
        license_id=license_id
    )

    return LicenseResponse(
        id=license.id,
        license_key=license.license_key,
        client_name=license.client_name,
        client_id=license.client_id,
        permissions=permissions,
        is_active=license.is_active,
        expires_at=license.expires_at,
        usage_limit=license.usage_limit,
        current_usage=license.current_usage,
        tenant_id=license.tenant_id,
        created_at=license.created_at,
        updated_at=license.updated_at
    )


@router.post(
    "/{license_id}/activate",
    response_model=LicenseResponse,
    summary="Activate license"
)
async def activate_license(
    license_id: int,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Activate a license. Requires admin permission."""
    license_service = LicenseService(db)
    license = await license_service.activate_license(license_id)

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License with ID '{license_id}' not found"
        )

    permissions = json.loads(license.permissions) if license.permissions else []

    logger.info(
        f"License activated by admin license: {admin_license.license_key[:16]}...",
        license_id=license_id
    )

    return LicenseResponse(
        id=license.id,
        license_key=license.license_key,
        client_name=license.client_name,
        client_id=license.client_id,
        permissions=permissions,
        is_active=license.is_active,
        expires_at=license.expires_at,
        usage_limit=license.usage_limit,
        current_usage=license.current_usage,
        tenant_id=license.tenant_id,
        created_at=license.created_at,
        updated_at=license.updated_at
    )


@router.post(
    "/{license_id}/reset-usage",
    response_model=LicenseResponse,
    summary="Reset license usage"
)
async def reset_license_usage(
    license_id: int,
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_admin_permission)
):
    """Reset usage counter for a license. Requires admin permission."""
    license_service = LicenseService(db)
    license = await license_service.reset_usage(license_id)

    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License with ID '{license_id}' not found"
        )

    permissions = json.loads(license.permissions) if license.permissions else []

    logger.info(
        f"License usage reset by admin license: {admin_license.license_key[:16]}...",
        license_id=license_id
    )

    return LicenseResponse(
        id=license.id,
        license_key=license.license_key,
        client_name=license.client_name,
        client_id=license.client_id,
        permissions=permissions,
        is_active=license.is_active,
        expires_at=license.expires_at,
        usage_limit=license.usage_limit,
        current_usage=license.current_usage,
        tenant_id=license.tenant_id,
        created_at=license.created_at,
        updated_at=license.updated_at
    )


@router.get(
    "/stats/summary",
    response_model=LicenseStats,
    summary="Get license statistics"
)
async def get_license_stats(
    db: AsyncSession = Depends(get_db),
    admin_license: LicenseKeyData = Depends(require_permission("read"))
):
    """Get license statistics. Requires read permission."""
    license_service = LicenseService(db)
    stats = await license_service.get_license_stats()

    logger.info(
        f"License stats retrieved by admin license: {admin_license.license_key[:16]}..."
    )

    return stats


@router.get(
    "/my-info",
    response_model=LicenseInfo,
    summary="Get current license information"
)
async def get_my_license_info(
    license_data: LicenseKeyData = Depends(verify_license_key)
):
    """Get information about the current license being used."""
    logger.info(
        f"License info retrieved for: {license_data.license_key[:16]}..."
    )

    return LicenseInfo(
        client_name=license_data.client_name,
        client_id=license_data.client_id,
        permissions=license_data.permissions,
        is_active=license_data.is_active,
        expires_at=license_data.expires_at,
        current_usage=license_data.current_usage,
        usage_limit=license_data.usage_limit,
        tenant_id=license_data.tenant_id,
        created_at=license_data.created_at
    )
