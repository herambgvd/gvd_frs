"""
Demo endpoints for testing and development.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import get_async_session
from app.models.tenant import Tenant
from app.models.license import License

router = APIRouter()
logger = get_logger(__name__)


@router.get("/")
async def demo_info():
    """
    Demo endpoint showing application information.
    """
    return {
        "message": "Welcome to GVD-FRS Demo API",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "features": [
            "License Management",
            "Tenant Management",
            "Database Migrations with Alembic",
            "Health Monitoring"
        ]
    }


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_async_session)):
    """
    Get basic statistics about tenants and licenses.
    """
    try:
        # Count tenants
        tenant_result = await db.execute(select(Tenant))
        tenant_count = len(tenant_result.scalars().all())

        # Count licenses
        license_result = await db.execute(select(License))
        license_count = len(license_result.scalars().all())

        # Count active licenses
        active_license_result = await db.execute(
            select(License).where(License.status == "active")
        )
        active_license_count = len(active_license_result.scalars().all())

        return {
            "statistics": {
                "total_tenants": tenant_count,
                "total_licenses": license_count,
                "active_licenses": active_license_count,
                "inactive_licenses": license_count - active_license_count
            }
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        return {
            "statistics": {
                "error": "Unable to retrieve statistics"
            }
        }
