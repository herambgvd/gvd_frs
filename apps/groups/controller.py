"""
Controller for Group management - combines business logic and database operations
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorCollection

from config.database import get_collection
from .models import GroupCreate, GroupUpdate, GroupQuery, GroupResponse, GroupListResponse

logger = logging.getLogger(__name__)


class GroupController:
    """Controller class for Group operations combining repository and service logic"""
    
    def __init__(self):
        self.collection: AsyncIOMotorCollection = get_collection("groups")
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure database indexes are created (async operation would be done via migration)"""
        # Note: In production, indexes should be created via migration scripts
        pass
    
    # ===============================
    # Database Operations (Repository Logic)
    # ===============================
    
    async def _create_group_in_db(self, group_data: GroupCreate, created_by: str) -> dict:
        """Create a new group in database"""
        try:
            group_dict = {
                "group_name": group_data.group_name,
                "display_color": group_data.display_color,
                "sound_on_alert": group_data.sound_on_alert,
                "watchlist_type": group_data.watchlist_type,
                "notes": group_data.notes,
                "organization_id": group_data.organization_id,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "is_active": True
            }
            
            result = await self.collection.insert_one(group_dict)
            created_group = await self.collection.find_one({"_id": result.inserted_id})
            
            if created_group:
                return created_group
            else:
                raise Exception("Failed to retrieve created group")
            
        except Exception as e:
            logger.error(f"Error creating group in database: {e}")
            raise Exception(f"Failed to create group: {str(e)}")
    
    async def _get_group_by_id_from_db(self, group_id: str, organization_id: str = None) -> Optional[dict]:
        """Get group by ID from database"""
        try:
            if not ObjectId.is_valid(group_id):
                return None
            
            filter_query = {"_id": ObjectId(group_id), "is_active": True}
            if organization_id:
                filter_query["organization_id"] = organization_id
            
            group_doc = await self.collection.find_one(filter_query)
            
            if group_doc:
                return group_doc
            return None
            
        except Exception as e:
            logger.error(f"Error getting group by ID from database: {e}")
            return None
    
    async def _get_groups_from_db(self, query: GroupQuery, organization_id: str = None) -> Tuple[List[dict], int]:
        """Get groups from database with pagination and filtering"""
        try:
            filter_query = {"is_active": query.is_active}
            
            if organization_id:
                filter_query["organization_id"] = organization_id
            elif query.organization_id:
                filter_query["organization_id"] = query.organization_id
            
            if query.watchlist_type:
                filter_query["watchlist_type"] = query.watchlist_type
            
            if query.search:
                filter_query["$or"] = [
                    {"group_name": {"$regex": query.search, "$options": "i"}},
                    {"notes": {"$regex": query.search, "$options": "i"}}
                ]
            
            skip = (query.page - 1) * query.limit
            total_count = await self.collection.count_documents(filter_query)
            
            cursor = self.collection.find(filter_query).sort("created_at", DESCENDING).skip(skip).limit(query.limit)
            groups_docs = await cursor.to_list(length=None)
            
            groups = list(groups_docs)
            return groups, total_count
            
        except Exception as e:
            logger.error(f"Error getting groups from database: {e}")
            raise Exception(f"Failed to get groups: {str(e)}")
    
    async def _update_group_in_db(self, group_id: str, group_data: GroupUpdate, updated_by: str, organization_id: str = None) -> Optional[dict]:
        """Update group in database"""
        try:
            if not ObjectId.is_valid(group_id):
                return None
            
            filter_query = {"_id": ObjectId(group_id), "is_active": True}
            if organization_id:
                filter_query["organization_id"] = organization_id
            
            update_data = {"updated_by": updated_by, "updated_at": datetime.utcnow()}
            
            if group_data.group_name is not None:
                update_data["group_name"] = group_data.group_name
            if group_data.display_color is not None:
                update_data["display_color"] = group_data.display_color
            if group_data.sound_on_alert is not None:
                update_data["sound_on_alert"] = group_data.sound_on_alert
            if group_data.watchlist_type is not None:
                update_data["watchlist_type"] = group_data.watchlist_type
            if group_data.notes is not None:
                update_data["notes"] = group_data.notes
            
            result = await self.collection.find_one_and_update(
                filter_query,
                {"$set": update_data},
                return_document=True
            )
            
            if result:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error updating group in database: {e}")
            raise Exception(f"Failed to update group: {str(e)}")
    
    async def _delete_group_in_db(self, group_id: str, organization_id: str = None) -> bool:
        """Soft delete group in database"""
        try:
            if not ObjectId.is_valid(group_id):
                return False
            
            filter_query = {"_id": ObjectId(group_id), "is_active": True}
            if organization_id:
                filter_query["organization_id"] = organization_id
            
            result = await self.collection.update_one(
                filter_query,
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting group in database: {e}")
            raise Exception(f"Failed to delete group: {str(e)}")
    
    async def _check_group_name_exists_in_db(self, group_name: str, organization_id: str, exclude_id: str = None) -> bool:
        """Check if group name already exists in organization"""
        try:
            filter_query = {
                "group_name": {"$regex": f"^{group_name}$", "$options": "i"},
                "organization_id": organization_id,
                "is_active": True
            }
            
            if exclude_id and ObjectId.is_valid(exclude_id):
                filter_query["_id"] = {"$ne": ObjectId(exclude_id)}
            
            count = await self.collection.count_documents(filter_query)
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking group name in database: {e}")
            return False
    
    async def _get_groups_by_organization_from_db(self, organization_id: str) -> List[dict]:
        """Get all active groups for an organization from database"""
        try:
            cursor = self.collection.find({
                "organization_id": organization_id,
                "is_active": True
            }).sort("group_name", ASCENDING)
            
            groups_docs = await cursor.to_list(length=None)
            return list(groups_docs)
            
        except Exception as e:
            logger.error(f"Error getting groups by organization from database: {e}")
            return []
    
    # ===============================
    # Business Logic (Service Logic)
    # ===============================
    
    def _validate_frs_group_create_permission(self, current_user: Dict[str, Any]) -> bool:
        """Check if user has permission to create FRS groups"""
        return self._check_permission(current_user, 'frs_groups_create')
    
    def _validate_frs_group_read_permission(self, current_user: Dict[str, Any]) -> bool:
        """Check if user has permission to read FRS groups"""
        return self._check_permission(current_user, 'frs_groups_read')
    
    def _validate_frs_group_update_permission(self, current_user: Dict[str, Any]) -> bool:
        """Check if user has permission to update FRS groups"""
        return self._check_permission(current_user, 'frs_groups_update')
    
    def _validate_frs_group_delete_permission(self, current_user: Dict[str, Any]) -> bool:
        """Check if user has permission to delete FRS groups"""
        return self._check_permission(current_user, 'frs_groups_delete')
    
    def _check_permission(self, current_user: Dict[str, Any], permission_name: str) -> bool:
        """Check if user has specific permission"""
        # Check if user is super admin (has all permissions)
        if current_user.get("userType") == "super_admin":
            return True
            
        # Check user permissions
        user_permissions = current_user.get("permissions", [])
        return permission_name in user_permissions

    def _validate_organization_access(self, current_user: Dict[str, Any], organization_id: str) -> bool:
        """Check if user has access to specific organization"""
        from .utils import require_organization_access
        return require_organization_access(current_user, organization_id)
    
    def _validate_admin_access(self, current_user: Dict[str, Any]) -> bool:
        """Check if user has admin access"""
        from .utils import require_admin_access
        return require_admin_access(current_user)
    
    def _get_user_organization_id(self, current_user: Dict[str, Any]) -> Optional[str]:
        """Get organization ID from user data"""
        if current_user.get("userType") == "super_admin":
            return None  # Super admin can access all organizations
        
        user_org_id = current_user.get("organizationId", {})
        if isinstance(user_org_id, dict):
            return user_org_id.get("id") or user_org_id.get("_id")
        return user_org_id
    
    def _get_user_id(self, current_user: Dict[str, Any]) -> str:
        """Get user ID from user data"""
        # Try different possible user ID fields
        user_id = (
            current_user.get("id") or 
            current_user.get("userId") or 
            current_user.get("user_id") or 
            current_user.get("_id")
        )
        
        logger.info(f"Looking for user ID in: {list(current_user.keys())}")
        logger.info(f"Found user ID: {user_id}")
        
        if not user_id:
            raise ValueError("User ID not found in authentication data")
        return str(user_id)
    
    # ===============================
    # Public Controller Methods
    # ===============================
    
    async def create_group(self, group_data: GroupCreate, current_user: Dict[str, Any]) -> GroupResponse:
        """Create a new group with validation and authorization"""
        try:
            # Debug logging
            logger.info(f"Creating group - User data: {current_user}")
            logger.info(f"User type: {current_user.get('userType')}")
            logger.info(f"User permissions: {current_user.get('permissions', [])}")
            
            # Validate organization access
            if not self._validate_organization_access(current_user, group_data.organization_id):
                raise PermissionError("Access denied to organization")
            
            # Check if user has permission to create FRS groups
            if not self._validate_frs_group_create_permission(current_user):
                raise PermissionError("Permission denied: frs_groups_create permission required")
            
            # Check if group name already exists
            name_exists = await self._check_group_name_exists_in_db(
                group_data.group_name,
                group_data.organization_id
            )
            
            if name_exists:
                raise ValueError(f"Group name '{group_data.group_name}' already exists in this organization")
            
            # Get user ID
            user_id = self._get_user_id(current_user)
            
            # Create group
            group_in_db = await self._create_group_in_db(group_data, user_id)
            
            return GroupResponse.from_db(group_in_db)
            
        except (ValueError, PermissionError) as e:
            logger.warning(f"Group creation validation error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            raise Exception(f"Failed to create group: {str(e)}")
    
    async def get_group_by_id(self, group_id: str, current_user: Dict[str, Any]) -> Optional[GroupResponse]:
        """Get group by ID with authorization"""
        try:
            organization_id = self._get_user_organization_id(current_user)
            
            group = await self._get_group_by_id_from_db(group_id, organization_id)
            
            if not group:
                return None
            
            # Check organization access
            if not self._validate_organization_access(current_user, group.get("organization_id")):
                return None
            
            return GroupResponse.from_db(group)
            
        except Exception as e:
            logger.error(f"Error getting group by ID: {e}")
            raise Exception(f"Failed to get group: {str(e)}")
    
    async def get_groups(self, query: GroupQuery, current_user: Dict[str, Any]) -> GroupListResponse:
        """Get groups with pagination, filtering, and authorization"""
        try:
            # Check if user has permission to read FRS groups
            if not self._validate_frs_group_read_permission(current_user):
                raise PermissionError("Permission denied: frs_groups_read permission required")
            
            organization_id = self._get_user_organization_id(current_user)
            
            # If organization_id is specified in query and user is not super admin, validate access
            if query.organization_id and organization_id:
                if not self._validate_organization_access(current_user, query.organization_id):
                    raise PermissionError("Access denied to specified organization")
                organization_id = query.organization_id
            
            groups, total_count = await self._get_groups_from_db(query, organization_id)
            
            group_responses = [GroupResponse.from_db(group) for group in groups]
            total_pages = (total_count + query.limit - 1) // query.limit
            
            return GroupListResponse(
                groups=group_responses,
                total_count=total_count,
                page=query.page,
                limit=query.limit,
                total_pages=total_pages
            )
            
        except PermissionError as e:
            logger.warning(f"Group listing permission error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            raise Exception(f"Failed to get groups: {str(e)}")
    
    async def update_group(self, group_id: str, group_data: GroupUpdate, current_user: Dict[str, Any]) -> Optional[GroupResponse]:
        """Update group with validation and authorization"""
        try:
            # Get existing group
            existing_group = await self._get_group_by_id_from_db(group_id)
            if not existing_group:
                return None
            
            # Check organization access
            if not self._validate_organization_access(current_user, existing_group.get("organization_id")):
                raise PermissionError("Access denied to organization")
            
            # Check admin privileges
            if not self._validate_admin_access(current_user):
                raise PermissionError("Admin privileges required to update groups")
            
            # Check if new group name conflicts
            if group_data.group_name and group_data.group_name != existing_group.get("group_name"):
                name_exists = await self._check_group_name_exists_in_db(
                    group_data.group_name,
                    existing_group.get("organization_id"),
                    group_id
                )
                
                if name_exists:
                    raise ValueError(f"Group name '{group_data.group_name}' already exists in this organization")
            
            # Get user ID
            user_id = self._get_user_id(current_user)
            
            # Update group
            updated_group = await self._update_group_in_db(group_id, group_data, user_id, existing_group.get("organization_id"))
            
            if not updated_group:
                return None
            
            return GroupResponse.from_db(updated_group)
            
        except (ValueError, PermissionError) as e:
            logger.warning(f"Group update validation error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error updating group: {e}")
            raise Exception(f"Failed to update group: {str(e)}")
    
    async def delete_group(self, group_id: str, current_user: Dict[str, Any]) -> bool:
        """Delete group with authorization"""
        try:
            # Get existing group
            existing_group = await self._get_group_by_id_from_db(group_id)
            if not existing_group:
                return False
            
            # Check organization access
            if not self._validate_organization_access(current_user, existing_group.get("organization_id")):
                raise PermissionError("Access denied to organization")
            
            # Check admin privileges
            if not self._validate_admin_access(current_user):
                raise PermissionError("Admin privileges required to delete groups")
            
            # Delete group
            success = await self._delete_group_in_db(group_id, existing_group.get("organization_id"))
            return success
            
        except PermissionError as e:
            logger.warning(f"Group deletion permission error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error deleting group: {e}")
            raise Exception(f"Failed to delete group: {str(e)}")
    
    async def get_groups_by_organization(self, organization_id: str, current_user: Dict[str, Any]) -> List[GroupResponse]:
        """Get all groups for an organization with authorization"""
        try:
            # Check organization access
            if not self._validate_organization_access(current_user, organization_id):
                raise PermissionError("Access denied to organization")
            
            groups = await self._get_groups_by_organization_from_db(organization_id)
            
            return [GroupResponse.from_db(group) for group in groups]
            
        except PermissionError as e:
            logger.warning(f"Organization groups access error: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error getting groups by organization: {e}")
            raise Exception(f"Failed to get organization groups: {str(e)}")


# Global controller instance - lazy initialization
_group_controller = None

def get_group_controller() -> GroupController:
    """Get or create the global group controller instance"""
    global _group_controller
    if _group_controller is None:
        _group_controller = GroupController()
    return _group_controller