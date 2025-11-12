"""
API routes for Group management with permission-based access control
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import Optional, Dict, Any
import logging

from .models import GroupCreate, GroupUpdate, GroupResponse, GroupListResponse, GroupQuery
from .controller import get_group_controller
from middleware.auth import get_current_user_required, require_frs_permission

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=GroupResponse, status_code=201)
async def create_group(
    request: Request,
    group_data: GroupCreate
):
    """
    Create a new group
    
    **Required Permission:** frs_groups_create
    
    - **group_name**: Name of the group
    - **display_color**: Hex color code for display
    - **sound_on_alert**: Whether to play sound on alert
    - **watchlist_type**: Type of watchlist (whitelist or blacklist)
    - **notes**: Optional notes about the group
    - **organization_id**: Organization ID that owns this group
    """
    try:
        # Get current user and check permissions manually
        current_user = await get_current_user_required(request)
        
        # Check permission
        if current_user.get('userType') != 'super_admin':
            user_permissions = current_user.get('permissions', [])
            if 'frs_groups_create' not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied: frs_groups_create permission required"
                )
        
        return await get_group_controller().create_group(group_data, current_user)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=GroupListResponse)
async def get_groups(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, max_length=100, description="Search term"),
    watchlist_type: Optional[str] = Query(None, pattern="^(whitelist|blacklist)$", description="Filter by watchlist type"),
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    is_active: bool = Query(True, description="Filter by active status")
):
    """
    Get groups with pagination and filtering
    
    **Required Permission:** frs_groups_read
    
    - **page**: Page number (default: 1)
    - **limit**: Number of items per page (default: 20, max: 100)
    - **search**: Search in group name and notes
    - **watchlist_type**: Filter by whitelist or blacklist
    - **organization_id**: Filter by organization (super admin only)
    - **is_active**: Filter by active status
    """
    try:
        # Get current user manually
        current_user = await get_current_user_required(request)
        
        # Check permission manually
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Super admin has all permissions
        if current_user.get('userType') != 'super_admin':
            # Check if user has the required permission
            user_permissions = current_user.get('permissions', [])
            if 'frs_groups_read' not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied: frs_groups_read permission required"
                )
        
        query = GroupQuery(
            page=page,
            limit=limit,
            search=search,
            watchlist_type=watchlist_type,
            organization_id=organization_id,
            is_active=is_active
        )
        return await get_group_controller().get_groups(query, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_by_id(
    request: Request,
    group_id: str = Path(..., description="Group ID")
):
    """
    Get group by ID
    
    **Required Permission:** frs_groups_read
    
    - **group_id**: The ID of the group to retrieve
    """
    try:
        # Get current user and check permissions manually
        current_user = await get_current_user_required(request)
        
        # Check permission
        if current_user.get('userType') != 'super_admin':
            user_permissions = current_user.get('permissions', [])
            if 'frs_groups_read' not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied: frs_groups_read permission required"
                )
        
        group = await get_group_controller().get_group_by_id(group_id, current_user)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        return group
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting group by ID: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    request: Request,
    group_id: str = Path(..., description="Group ID")
):
    """
    Update group
    
    **Required Permission:** frs_groups_update
    
    - **group_id**: The ID of the group to update
    - **group_data**: Updated group data (only provide fields to update)
    """
    try:
        # Get current user and check permissions manually
        current_user = await get_current_user_required(request)
        
        # Check permission
        if current_user.get('userType') != 'super_admin':
            user_permissions = current_user.get('permissions', [])
            if 'frs_groups_update' not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied: frs_groups_update permission required"
                )
        
        # Get the request body manually
        body = await request.json()
        group_data = GroupUpdate(**body)
        
        updated_group = await get_group_controller().update_group(group_id, group_data, current_user)
        if not updated_group:
            raise HTTPException(status_code=404, detail="Group not found")
        return updated_group
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating group: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    request: Request,
    group_id: str = Path(..., description="Group ID")
):
    """
    Delete group (soft delete)
    
    **Required Permission:** frs_groups_delete
    
    - **group_id**: The ID of the group to delete
    """
    try:
        # Get current user and check permissions manually
        current_user = await get_current_user_required(request)
        
        # Check permission
        if current_user.get('userType') != 'super_admin':
            user_permissions = current_user.get('permissions', [])
            if 'frs_groups_delete' not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail="Permission denied: frs_groups_delete permission required"
                )
        
        success = await get_group_controller().delete_group(group_id, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="Group not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/organization/{organization_id}", response_model=list[GroupResponse])
async def get_groups_by_organization(
    organization_id: str = Path(..., description="Organization ID"),
    current_user: Dict[str, Any] = Depends(get_current_user_required),
    _: Dict[str, Any] = Depends(require_frs_permission("frs_groups_read"))
):
    """
    Get all groups for an organization
    
    **Required Permission:** frs_groups_read
    
    - **organization_id**: The ID of the organization
    """
    try:
        groups = await get_group_controller().get_groups_by_organization(organization_id, current_user)
        return groups
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting groups by organization: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint for the groups module
@router.get("/health/check")
async def groups_health_check():
    """Health check for groups module"""
    return {
        "status": "healthy",
        "module": "groups",
        "timestamp": "2025-11-10T00:00:00Z"
    }