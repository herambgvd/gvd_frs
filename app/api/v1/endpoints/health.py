"""
Health check endpoint for monitoring service status.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import get_async_session

router = APIRouter()
logger = get_logger(__name__)


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_async_session)):
    """
    Health check endpoint to verify service status.
    Returns the status of the application and database connectivity.
    """
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status
    }
