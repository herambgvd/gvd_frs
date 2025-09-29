"""
Security utilities for license key-based authentication.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from pydantic import BaseModel
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer()


class LicenseKeyData(BaseModel):
    """License key data model."""
    license_key: str
    client_name: str
    client_id: str
    permissions: list[str] = []
    is_active: bool = True
    expires_at: Optional[datetime] = None
    created_at: datetime
    usage_limit: Optional[int] = None
    current_usage: int = 0
    tenant_id: Optional[str] = None


class LicenseKeyManager:
    """Manager for license key operations."""

    def __init__(self):
        # In-memory storage for demo - replace with database in production
        self._license_keys: Dict[str, LicenseKeyData] = {}
        self._initialize_demo_keys()

    def _initialize_demo_keys(self):
        """Initialize some demo license keys for testing."""
        demo_keys = [
            {
                "license_key": "gvd-demo-key-12345",
                "client_name": "Demo Client",
                "client_id": "demo-001",
                "permissions": ["read", "write"],
                "expires_at": datetime.utcnow() + timedelta(days=365),
                "tenant_id": "tenant-demo-001"
            },
            {
                "license_key": "gvd-premium-key-67890",
                "client_name": "Premium Client",
                "client_id": "premium-001",
                "permissions": ["read", "write", "admin"],
                "expires_at": datetime.utcnow() + timedelta(days=365),
                "usage_limit": 10000,
                "tenant_id": "tenant-premium-001"
            }
        ]

        for key_data in demo_keys:
            license_key = LicenseKeyData(
                created_at=datetime.utcnow(),
                **key_data
            )
            self._license_keys[key_data["license_key"]] = license_key

    def generate_license_key(
        self,
        client_name: str,
        client_id: str,
        permissions: list[str] = None,
        expires_in_days: int = 365,
        usage_limit: Optional[int] = None,
        tenant_id: Optional[str] = None
    ) -> str:
        """Generate a new license key."""
        # Generate secure random key
        random_bytes = secrets.token_bytes(32)
        timestamp = str(int(datetime.utcnow().timestamp()))
        key_material = f"{client_id}-{timestamp}-{random_bytes.hex()}"

        # Create hash-based license key
        license_key = f"gvd-{hashlib.sha256(key_material.encode()).hexdigest()[:16]}"

        # Create license key data
        key_data = LicenseKeyData(
            license_key=license_key,
            client_name=client_name,
            client_id=client_id,
            permissions=permissions or ["read"],
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days),
            created_at=datetime.utcnow(),
            usage_limit=usage_limit,
            tenant_id=tenant_id
        )

        # Store the key
        self._license_keys[license_key] = key_data

        logger.info(
            "New license key generated",
            client_name=client_name,
            client_id=client_id,
            license_key=license_key[:16] + "..."  # Log partial key for security
        )

        return license_key

    def validate_license_key(self, license_key: str) -> Optional[LicenseKeyData]:
        """Validate a license key and return its data if valid."""
        if license_key not in self._license_keys:
            return None

        key_data = self._license_keys[license_key]

        # Check if key is active
        if not key_data.is_active:
            return None

        # Check if key has expired
        if key_data.expires_at and datetime.utcnow() > key_data.expires_at:
            return None

        # Check usage limit
        if key_data.usage_limit and key_data.current_usage >= key_data.usage_limit:
            return None

        # Increment usage counter
        key_data.current_usage += 1

        return key_data

    def revoke_license_key(self, license_key: str) -> bool:
        """Revoke a license key."""
        if license_key in self._license_keys:
            self._license_keys[license_key].is_active = False
            logger.info(f"License key revoked: {license_key[:16]}...")
            return True
        return False

    def get_license_key_info(self, license_key: str) -> Optional[LicenseKeyData]:
        """Get license key information without incrementing usage."""
        return self._license_keys.get(license_key)

    def list_license_keys(self) -> list[LicenseKeyData]:
        """List all license keys."""
        return list(self._license_keys.values())


# Global license key manager instance
license_manager = LicenseKeyManager()


def get_api_key_from_header(request: Request) -> str:
    """Extract API key from X-API-Key header."""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required"
        )
    return api_key


def get_api_key_from_auth(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract API key from Authorization Bearer token."""
    return credentials.credentials


def verify_license_key(api_key: str = Depends(get_api_key_from_header)) -> LicenseKeyData:
    """Verify license key and return license data."""
    license_data = license_manager.validate_license_key(api_key)

    if not license_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired license key"
        )

    return license_data


def require_permission(required_permission: str):
    """Decorator to require specific permission."""
    def permission_checker(license_data: LicenseKeyData = Depends(verify_license_key)) -> LicenseKeyData:
        if required_permission not in license_data.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        return license_data
    return permission_checker


def require_admin_permission(license_data: LicenseKeyData = Depends(verify_license_key)) -> LicenseKeyData:
    """Require admin permission."""
    if "admin" not in license_data.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    return license_data


# Convenience functions for common permissions
def require_read_permission():
    return require_permission("read")


def require_write_permission():
    return require_permission("write")
