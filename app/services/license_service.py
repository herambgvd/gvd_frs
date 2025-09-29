"""
License service layer for business logic with async operations.
"""
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select

from app.models.license import License
from app.schemas.license import LicenseCreate, LicenseUpdate, LicenseStats
from app.core.logging import get_logger

logger = get_logger(__name__)


class LicenseService:
    """Service layer for license operations with async support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def generate_license_key(self, client_id: str) -> str:
        """Generate a secure license key."""
        random_bytes = secrets.token_bytes(32)
        timestamp = str(int(datetime.utcnow().timestamp()))
        key_material = f"{client_id}-{timestamp}-{random_bytes.hex()}"

        # Create hash-based license key
        license_key = f"gvd-{hashlib.sha256(key_material.encode()).hexdigest()[:16]}"
        return license_key

    async def create_license(self, license_data: LicenseCreate) -> License:
        """Create a new license."""
        # Check if client_id already exists
        existing_license = await self.db.execute(
            select(License).where(License.client_id == license_data.client_id)
        )
        if existing_license.scalar_one_or_none():
            raise ValueError(f"Client ID '{license_data.client_id}' already has a license")

        # Generate unique license key
        license_key = self.generate_license_key(license_data.client_id)

        # Ensure the license key is unique
        while True:
            existing_key = await self.db.execute(
                select(License).where(License.license_key == license_key)
            )
            if not existing_key.scalar_one_or_none():
                break
            license_key = self.generate_license_key(license_data.client_id)

        # Convert permissions list to JSON string
        permissions_json = json.dumps(license_data.permissions)

        # Calculate expiration date
        expires_at = None
        if hasattr(license_data, 'expires_in_days') and license_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=license_data.expires_in_days)
        elif license_data.expires_at:
            expires_at = license_data.expires_at

        license = License(
            license_key=license_key,
            client_name=license_data.client_name,
            client_id=license_data.client_id,
            permissions=permissions_json,
            is_active=license_data.is_active,
            expires_at=expires_at,
            usage_limit=license_data.usage_limit,
            tenant_id=license_data.tenant_id
        )

        self.db.add(license)
        await self.db.commit()
        await self.db.refresh(license)

        logger.info(f"Created new license: {license_key[:16]}... for client {license_data.client_id}")
        return license

    async def get_license(self, license_id: int) -> Optional[License]:
        """Get license by ID."""
        result = await self.db.execute(select(License).where(License.id == license_id))
        return result.scalar_one_or_none()

    async def get_license_by_key(self, license_key: str) -> Optional[License]:
        """Get license by license key."""
        result = await self.db.execute(select(License).where(License.license_key == license_key))
        return result.scalar_one_or_none()

    async def get_license_by_client_id(self, client_id: str) -> Optional[License]:
        """Get license by client ID."""
        result = await self.db.execute(select(License).where(License.client_id == client_id))
        return result.scalar_one_or_none()

    async def list_licenses(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        tenant_id: Optional[str] = None
    ) -> List[License]:
        """List licenses with optional filtering."""
        query = select(License)

        if is_active is not None:
            query = query.where(License.is_active == is_active)

        if tenant_id:
            query = query.where(License.tenant_id == tenant_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_license(self, license_id: int, license_data: LicenseUpdate) -> Optional[License]:
        """Update license information."""
        license = await self.get_license(license_id)
        if not license:
            return None

        update_data = license_data.model_dump(exclude_unset=True)

        # Handle permissions conversion to JSON
        if "permissions" in update_data and update_data["permissions"] is not None:
            update_data["permissions"] = json.dumps(update_data["permissions"])

        for field, value in update_data.items():
            setattr(license, field, value)

        await self.db.commit()
        await self.db.refresh(license)

        logger.info(f"Updated license: {license.license_key[:16]}...")
        return license

    async def delete_license(self, license_id: int) -> bool:
        """Delete license."""
        license = await self.get_license(license_id)
        if not license:
            return False

        license_key_partial = license.license_key[:16]
        await self.db.delete(license)
        await self.db.commit()

        logger.info(f"Deleted license: {license_key_partial}...")
        return True

    async def validate_license_key(self, license_key: str) -> Optional[License]:
        """Validate a license key and return license data if valid."""
        license = await self.get_license_by_key(license_key)
        if not license:
            return None

        # Check if license is active
        if not license.is_active:
            return None

        # Check if license has expired
        if license.expires_at and datetime.utcnow() > license.expires_at:
            return None

        # Check usage limit
        if license.usage_limit and license.current_usage >= license.usage_limit:
            return None

        # Increment usage counter
        license.current_usage += 1
        await self.db.commit()

        return license

    async def revoke_license(self, license_id: int) -> Optional[License]:
        """Revoke (deactivate) a license."""
        return await self.update_license(license_id, LicenseUpdate(is_active=False))

    async def activate_license(self, license_id: int) -> Optional[License]:
        """Activate a license."""
        return await self.update_license(license_id, LicenseUpdate(is_active=True))

    async def reset_usage(self, license_id: int) -> Optional[License]:
        """Reset usage counter for a license."""
        license = await self.get_license(license_id)
        if not license:
            return None

        license.current_usage = 0
        await self.db.commit()
        await self.db.refresh(license)

        logger.info(f"Reset usage for license: {license.license_key[:16]}...")
        return license

    async def get_license_stats(self) -> LicenseStats:
        """Get license statistics."""
        # Total licenses
        total_result = await self.db.execute(select(func.count(License.id)))
        total_licenses = total_result.scalar()

        # Active licenses
        active_result = await self.db.execute(
            select(func.count(License.id)).where(License.is_active == True)
        )
        active_licenses = active_result.scalar()

        # Expired licenses
        expired_result = await self.db.execute(
            select(func.count(License.id)).where(
                and_(
                    License.expires_at.isnot(None),
                    License.expires_at < datetime.utcnow()
                )
            )
        )
        expired_licenses = expired_result.scalar()

        # Usage summary
        total_usage_result = await self.db.execute(select(func.sum(License.current_usage)))
        total_usage = total_usage_result.scalar() or 0

        avg_usage_result = await self.db.execute(select(func.avg(License.current_usage)))
        avg_usage = avg_usage_result.scalar() or 0

        licenses_with_limits_result = await self.db.execute(
            select(func.count(License.id)).where(License.usage_limit.isnot(None))
        )
        licenses_with_limits = licenses_with_limits_result.scalar()

        licenses_at_limit_result = await self.db.execute(
            select(func.count(License.id)).where(
                and_(
                    License.usage_limit.isnot(None),
                    License.current_usage >= License.usage_limit
                )
            )
        )
        licenses_at_limit = licenses_at_limit_result.scalar()

        usage_summary = {
            "total_usage": total_usage,
            "average_usage": float(avg_usage),
            "licenses_with_limits": licenses_with_limits,
            "licenses_at_limit": licenses_at_limit
        }

        return LicenseStats(
            total_licenses=total_licenses,
            active_licenses=active_licenses,
            expired_licenses=expired_licenses,
            usage_summary=usage_summary
        )
