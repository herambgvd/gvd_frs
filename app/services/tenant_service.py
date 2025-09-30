"""
Tenant service layer for business logic with async operations.
"""
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.tenant import Tenant, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantStats
from app.core.logging import get_logger

logger = get_logger(__name__)


class TenantService:
    """Service layer for tenant operations with async support."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """Create a new tenant."""
        # Check if tenant with same ID already exists
        existing_tenant = await self.db.execute(select(Tenant).where(Tenant.id == tenant_data.id))
        if existing_tenant.scalar_one_or_none():
            raise ValueError(f"Tenant with ID '{tenant_data.id}' already exists")

        # Check if domain is already taken
        if tenant_data.domain:
            existing_domain = await self.db.execute(select(Tenant).where(Tenant.domain == tenant_data.domain))
            if existing_domain.scalar_one_or_none():
                raise ValueError(f"Domain '{tenant_data.domain}' is already taken")

        # Convert settings dict to JSON string if provided
        

        tenant = Tenant(
            id=tenant_data.id,
            name=tenant_data.name,
            description=tenant_data.description,
            domain=tenant_data.domain,
            status=tenant_data.status,
            settings=json.dumps(tenant_data.settings) if tenant_data.settings else None,
            max_users=tenant_data.max_users,
            contact_email=tenant_data.contact_email,
            contact_phone=tenant_data.contact_phone,
            created_by=tenant_data.created_by
        )

        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)

        if tenant.settings and isinstance(tenant.settings, str):
            tenant.settings = json.loads(tenant.settings)

        logger.info(f"Created new tenant: {tenant.id} - {tenant.name}")
        return tenant

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()

        if tenant and isinstance(tenant.settings, str):
            import json
            try:
                tenant.settings = json.loads(tenant.settings)
            except Exception:
                tenant.settings = None  # fallback if corrupted

        return tenant

    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain."""
        result = await self.db.execute(select(Tenant).where(Tenant.domain == domain))
        return result.scalar_one_or_none()

    async def list_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TenantStatus] = None
    ) -> List[Tenant]:
        """List tenants with optional filtering."""
        query = select(Tenant)

        if status:
            query = query.where(Tenant.status == status)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate) -> Optional[Tenant]:
        """Update tenant information."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None

        update_data = tenant_data.model_dump(exclude_unset=True)

        # Handle settings conversion to JSON
        if "settings" in update_data and update_data["settings"] is not None:
            update_data["settings"] = json.dumps(update_data["settings"])

        # Check domain uniqueness if being updated
        if "domain" in update_data and update_data["domain"]:
            existing_domain = await self.db.execute(
                select(Tenant).where(Tenant.domain == update_data["domain"]).where(Tenant.id != tenant_id)
            )
            if existing_domain.scalar_one_or_none():
                raise ValueError(f"Domain '{update_data['domain']}' is already taken")

        for field, value in update_data.items():
            setattr(tenant, field, value)
        
        if tenant.settings and isinstance(tenant.settings, dict):
            tenant.settings = json.dumps(tenant.settings)

        await self.db.commit()
        await self.db.refresh(tenant)

        if tenant.settings and isinstance(tenant.settings, str):
            tenant.settings = json.loads(tenant.settings)

        logger.info(f"Updated tenant: {tenant.id}")
        return tenant

    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False

        await self.db.delete(tenant)
        await self.db.commit()

        logger.info(f"Deleted tenant: {tenant_id}")
        return True

    async def activate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        tenant = await self.update_tenant(tenant_id, TenantUpdate(status=TenantStatus.ACTIVE))
        if tenant and isinstance(tenant.settings, str):
            tenant.settings = json.loads(tenant.settings)
        return tenant

    async def deactivate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        tenant = await self.update_tenant(tenant_id, TenantUpdate(status=TenantStatus.INACTIVE))
        if tenant and isinstance(tenant.settings, str):
            tenant.settings = json.loads(tenant.settings)
        return tenant


    async def suspend_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Suspend a tenant."""
        return await self.update_tenant(tenant_id, TenantUpdate(status=TenantStatus.SUSPENDED))

    async def get_tenant_stats(self) -> TenantStats:
        """Get tenant statistics."""
        # Total tenants
        total_result = await self.db.execute(select(func.count(Tenant.id)))
        total_tenants = total_result.scalar()

        # Active tenants
        active_result = await self.db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.ACTIVE)
        )
        active_tenants = active_result.scalar()

        # Inactive tenants
        inactive_result = await self.db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.INACTIVE)
        )
        inactive_tenants = inactive_result.scalar()

        # Suspended tenants
        suspended_result = await self.db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.SUSPENDED)
        )
        suspended_tenants = suspended_result.scalar()

        # Pending tenants
        pending_result = await self.db.execute(
            select(func.count(Tenant.id)).where(Tenant.status == TenantStatus.PENDING)
        )
        pending_tenants = pending_result.scalar()

        # Total users across all tenants
        total_users_result = await self.db.execute(select(func.sum(Tenant.current_users)))
        total_users = total_users_result.scalar() or 0

        return TenantStats(
            total_tenants=total_tenants,
            active_tenants=active_tenants,
            inactive_tenants=inactive_tenants,
            suspended_tenants=suspended_tenants,
            pending_tenants=pending_tenants,
            total_users_across_tenants=total_users
        )

    async def increment_user_count(self, tenant_id: str) -> Optional[Tenant]:
        """Increment user count for tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None

        # Check if max users limit would be exceeded
        if tenant.max_users and tenant.current_users >= tenant.max_users:
            raise ValueError(f"Tenant {tenant_id} has reached maximum user limit")

        tenant.current_users += 1
        if tenant.settings and isinstance(tenant.settings, dict):
            tenant.settings = json.dumps(tenant.settings)

        await self.db.commit()
        await self.db.refresh(tenant)

        if tenant.settings and isinstance(tenant.settings, str):
            tenant.settings = json.loads(tenant.settings)
        return tenant

    async def decrement_user_count(self, tenant_id: str) -> Optional[Tenant]:
        """Decrement user count for tenant."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None

        if tenant.current_users > 0:
            tenant.current_users -= 1
            if tenant.settings and isinstance(tenant.settings, dict):
                tenant.settings = json.dumps(tenant.settings)
                
            await self.db.commit()
            await self.db.refresh(tenant)

            if tenant.settings and isinstance(tenant.settings, str):
                tenant.settings = json.loads(tenant.settings)

        return tenant
