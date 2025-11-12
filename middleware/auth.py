"""
Authentication Middleware for GVD FRS
Integrates with GVD UMS for JWT token validation and user permissions
"""

import jwt
import httpx
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, List
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """Custom authentication exception"""
    pass


class AuthMiddleware:
    """Authentication middleware class"""
    
    def __init__(self):
        self.gvd_ums_url = settings.GVD_UMS_BASE_URL
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = settings.JWT_ALGORITHM
    
    async def verify_token_and_get_user(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and fetch complete user data from GVD_UMS"""
        try:
            # Decode JWT token to get user ID
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            user_id = payload.get('userId')
            if not user_id:
                raise AuthenticationError("Invalid token: missing userId")
            
            # Fetch complete user details from GVD_UMS (similar to gvd_wf)
            user_data = await self._fetch_user_from_gvd_ums(token, user_id)
            
            return user_data
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationError("Token verification failed")
    
    async def _fetch_user_from_gvd_ums(self, token: str, user_id: str) -> Dict[str, Any]:
        """Fetch user details from GVD_UMS including permissions"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.gvd_ums_url}/api/users/{user_id}",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    raise AuthenticationError(
                        error_data.get('message', 'User validation failed')
                    )
                
                api_response = response.json()
                if not api_response.get('success'):
                    raise AuthenticationError("Invalid token. User validation failed.")
                
                user = api_response.get('data', {}).get('user', {})
                
                # Check if user is active
                if not user.get('isActive'):
                    raise AuthenticationError("Account is deactivated. Please contact administrator.")
                
                # For organization users, ensure organization exists
                if user.get('userType') == 'organization_user' and not user.get('organizationId'):
                    raise AuthenticationError("Organization not found. Access denied.")
                
                # Extract permissions from user roles (same logic as gvd_wf)
                permissions = []
                if user.get('roles') and isinstance(user['roles'], list):
                    for role in user['roles']:
                        if role.get('permissions') and isinstance(role['permissions'], list):
                            for permission in role['permissions']:
                                if isinstance(permission, dict) and permission.get('name'):
                                    # Permission object with name
                                    permissions.append(permission['name'])
                                elif isinstance(permission, str):
                                    permissions.append(permission)
                
                logger.info(
                    f"🔍 User permissions extracted: {permissions[:5]}"
                    f"{f' (+{len(permissions) - 5} more)' if len(permissions) > 5 else ''}"
                )
                
                # Return structured user data
                return {
                'user_id': user.get('_id') or user.get('id'),
                'email': user.get('email'),
                'first_name': user.get('firstName'),
                'last_name': user.get('lastName'),
                'user_type': user.get('userType'),
                'organization_id': (user.get('organizationId', {}).get('id') 
                                 if isinstance(user.get('organizationId'), dict) 
                                 else user.get('organizationId')),
                'organization': user.get('organizationId', {}),
                'permissions': permissions,
                'roles': user.get('roles', []),
                'is_active': user.get('isActive', True)
            }  
                    
        except httpx.RequestError as e:
            logger.error(f"GVD_UMS request error: {e}")
            raise AuthenticationError("Authentication service unavailable")
        except Exception as e:
            logger.error(f"GVD_UMS user fetch error: {e}")
            raise AuthenticationError("User verification failed")


# Global auth middleware instance
auth_middleware = AuthMiddleware()


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current authenticated user
    Returns None if no token provided (for optional authentication)
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    
    try:
        user_data = await auth_middleware.verify_token_and_get_user(token)
        return user_data
    except AuthenticationError:
        return None


async def get_current_user_required(request: Request) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user (required)
    Raises HTTPException if no valid token provided
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing or invalid format"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        user_data = await auth_middleware.verify_token_and_get_user(token)
        return user_data
    except AuthenticationError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


def require_super_admin(user: Dict[str, Any]) -> Dict[str, Any]:
    """Check if user is super admin"""
    if user.get('userType') != 'super_admin':
        raise HTTPException(
            status_code=403,
            detail="Super Admin privileges required"
        )
    return user


def require_organization_access(organization_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    """Check if user has access to specific organization"""
    user_type = user.get('userType')
    user_org_id = user.get('organizationId')
    
    # Super admin has access to all organizations
    if user_type == 'super_admin':
        return user
    
    # Organization users can only access their own organization
    if user_type == 'organization_user':
        if str(user_org_id) != str(organization_id):
            raise HTTPException(
                status_code=403,
                detail="Access denied. You can only access resources within your organization"
            )
    
    return user


def require_frs_permission(permission: str):
    """
    Middleware to check specific FRS permissions (similar to gvd_wf pattern)
    Returns a dependency function that checks if user has the required permission
    """
    def check_permission(user: Dict[str, Any]) -> Dict[str, Any]:
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
        
        # Super admin has all permissions
        if user.get('userType') == 'super_admin':
            return user
        
        # Check if user has the required permission
        user_permissions = user.get('permissions', [])
        
        logger.info(f"🔍 DEBUG: Checking permission: {permission}")
        logger.info(f"🔍 DEBUG: User permissions: {user_permissions}")
        logger.info(f"🔍 DEBUG: User type: {user.get('userType')}")
        
        if permission not in user_permissions:
            logger.warning(
                f"❌ DEBUG: Permission denied. Required: {permission}, "
                f"User has: {user_permissions}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission} permission required"
            )
        
        logger.info(f"✅ DEBUG: Permission granted: {permission}")
        return user
    
    return check_permission


def organization_scope_filter(user: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add organization scope to filters for organization users
    (similar to gvd_wf organizationScope middleware)
    """
    if user.get('userType') == 'organization_user' and user.get('organizationId'):
        filters['organization_id'] = user['organizationId']
    
    return filters