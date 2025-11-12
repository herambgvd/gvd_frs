"""
Utility functions and common logic for Groups module
"""

from typing import Dict, Any, Optional


def require_organization_access(current_user: Dict[str, Any], organization_id: str) -> bool:
    """
    Check if user has access to specific organization
    
    Args:
        current_user: Current authenticated user data
        organization_id: Target organization ID to check access for
        
    Returns:
        bool: True if user has access, False otherwise
    """
    user_type = current_user.get("userType", "").lower()
    user_org_id = current_user.get("organizationId", {})
    
    # Handle different organization ID formats
    if isinstance(user_org_id, dict):
        user_org_id = user_org_id.get("id") or user_org_id.get("_id")
    
    # Super admin has access to all organizations
    if user_type == "super_admin":
        return True
    
    # Organization users can only access their own organization
    if user_type in ["organization_admin", "organization_user"]:
        return str(user_org_id) == str(organization_id)
    
    return False


def require_admin_access(current_user: Dict[str, Any]) -> bool:
    """
    Check if user has admin access (super_admin or organization_admin)
    
    Args:
        current_user: Current authenticated user data
        
    Returns:
        bool: True if user has admin access, False otherwise
    """
    user_type = current_user.get("userType", "")
    
    # Debug logging
    print(f"DEBUG: require_admin_access - userType: {user_type}")
    print(f"DEBUG: require_admin_access - roles: {current_user.get('roles', [])}")
    
    # Check userType directly
    if user_type in ["super_admin", "organization_admin", "admin"]:
        print(f"DEBUG: require_admin_access - GRANTED by userType: {user_type}")
        return True
    
    # Also check roles array for admin role
    roles = current_user.get("roles", [])
    for role in roles:
        if isinstance(role, dict):
            role_name = role.get("name", "")
            if role_name in ["admin", "organization_admin", "super_admin"]:
                print(f"DEBUG: require_admin_access - GRANTED by role: {role_name}")
                return True
    
    print(f"DEBUG: require_admin_access - DENIED - userType: {user_type}, roles: {roles}")
    return False


def require_super_admin_access(current_user: Dict[str, Any]) -> bool:
    """
    Check if user has super admin access
    
    Args:
        current_user: Current authenticated user data
        
    Returns:
        bool: True if user is super admin, False otherwise
    """
    user_type = current_user.get("userType", "").lower()
    return user_type == "super_admin"


def extract_user_id(current_user: Dict[str, Any]) -> Optional[str]:
    """
    Extract user ID from user data with multiple possible field names
    
    Args:
        current_user: Current authenticated user data
        
    Returns:
        str: User ID or None if not found
    """
    return current_user.get("userId") or current_user.get("user_id") or current_user.get("id")


def extract_organization_id(current_user: Dict[str, Any]) -> Optional[str]:
    """
    Extract organization ID from user data handling different formats
    
    Args:
        current_user: Current authenticated user data
        
    Returns:
        str: Organization ID or None if not found or if super admin
    """
    if current_user.get("userType") == "super_admin":
        return None  # Super admin can access all organizations
    
    user_org_id = current_user.get("organizationId", {})
    if isinstance(user_org_id, dict):
        return user_org_id.get("id") or user_org_id.get("_id")
    return user_org_id


def validate_hex_color(color: str) -> bool:
    """
    Validate if a string is a valid hex color code
    
    Args:
        color: Color string to validate
        
    Returns:
        bool: True if valid hex color, False otherwise
    """
    import re
    return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))


def validate_watchlist_type(watchlist_type: str) -> bool:
    """
    Validate if watchlist type is valid
    
    Args:
        watchlist_type: Watchlist type to validate
        
    Returns:
        bool: True if valid watchlist type, False otherwise
    """
    return watchlist_type.lower() in ["whitelist", "blacklist"]


def sanitize_search_query(search: str) -> str:
    """
    Sanitize search query for MongoDB regex
    
    Args:
        search: Raw search string
        
    Returns:
        str: Sanitized search string
    """
    import re
    # Escape special regex characters
    return re.escape(search.strip())


def build_sort_query(sort_by: str = "created_at", sort_order: str = "desc") -> list:
    """
    Build MongoDB sort query
    
    Args:
        sort_by: Field to sort by
        sort_order: Sort order ('asc' or 'desc')
        
    Returns:
        list: MongoDB sort query
    """
    from pymongo import ASCENDING, DESCENDING
    
    direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
    return [(sort_by, direction)]


def calculate_pagination(page: int, limit: int, total_count: int) -> Dict[str, Any]:
    """
    Calculate pagination metadata
    
    Args:
        page: Current page number
        limit: Items per page
        total_count: Total number of items
        
    Returns:
        dict: Pagination metadata
    """
    total_pages = (total_count + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "page": page,
        "limit": limit,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev
    }


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error message for consistent logging and responses
    
    Args:
        error: Exception object
        context: Optional context information
        
    Returns:
        str: Formatted error message
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    if context:
        return f"{context} - {error_type}: {error_message}"
    return f"{error_type}: {error_message}"


def validate_object_id(obj_id: str) -> bool:
    """
    Validate if string is a valid MongoDB ObjectId
    
    Args:
        obj_id: String to validate
        
    Returns:
        bool: True if valid ObjectId, False otherwise
    """
    from bson import ObjectId
    return ObjectId.is_valid(obj_id)


def create_filter_query(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create MongoDB filter query from filters dictionary
    
    Args:
        filters: Dictionary of filter criteria
        
    Returns:
        dict: MongoDB filter query
    """
    query = {}
    
    # Add active status filter (default to True)
    if "is_active" in filters:
        query["is_active"] = filters["is_active"]
    else:
        query["is_active"] = True
    
    # Add organization filter
    if "organization_id" in filters and filters["organization_id"]:
        query["organization_id"] = filters["organization_id"]
    
    # Add watchlist type filter
    if "watchlist_type" in filters and filters["watchlist_type"]:
        query["watchlist_type"] = filters["watchlist_type"]
    
    # Add search filter
    if "search" in filters and filters["search"]:
        sanitized_search = sanitize_search_query(filters["search"])
        query["$or"] = [
            {"group_name": {"$regex": sanitized_search, "$options": "i"}},
            {"notes": {"$regex": sanitized_search, "$options": "i"}}
        ]
    
    return query


class GroupPermissions:
    """Helper class for group permission checks"""
    
    @staticmethod
    def can_create(current_user: Dict[str, Any], organization_id: str) -> bool:
        """Check if user can create groups in organization"""
        return (require_admin_access(current_user) and 
                require_organization_access(current_user, organization_id))
    
    @staticmethod
    def can_read(current_user: Dict[str, Any], group_organization_id: str) -> bool:
        """Check if user can read group"""
        return require_organization_access(current_user, group_organization_id)
    
    @staticmethod
    def can_update(current_user: Dict[str, Any], group_organization_id: str) -> bool:
        """Check if user can update group"""
        return (require_admin_access(current_user) and 
                require_organization_access(current_user, group_organization_id))
    
    @staticmethod
    def can_delete(current_user: Dict[str, Any], group_organization_id: str) -> bool:
        """Check if user can delete group"""
        return (require_admin_access(current_user) and 
                require_organization_access(current_user, group_organization_id))


class GroupValidator:
    """Helper class for group data validation"""
    
    @staticmethod
    def validate_group_name(name: str, min_length: int = 1, max_length: int = 100) -> bool:
        """Validate group name"""
        return isinstance(name, str) and min_length <= len(name.strip()) <= max_length
    
    @staticmethod
    def validate_notes(notes: Optional[str], max_length: int = 500) -> bool:
        """Validate notes field"""
        if notes is None:
            return True
        return isinstance(notes, str) and len(notes) <= max_length
    
    @staticmethod
    def validate_organization_id(org_id: str) -> bool:
        """Validate organization ID format"""
        return isinstance(org_id, str) and validate_object_id(org_id)
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """Validate user ID format"""
        return isinstance(user_id, str) and validate_object_id(user_id)


# Constants
VALID_WATCHLIST_TYPES = ["whitelist", "blacklist"]
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_SORT_FIELD = "created_at"
DEFAULT_SORT_ORDER = "desc"