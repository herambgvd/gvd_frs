"""
FastAPI dependencies for dependency injection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session


# Use async session as the main database dependency
get_db = get_async_session
