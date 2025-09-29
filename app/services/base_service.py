"""
Base service class for business logic operations.
"""
from typing import Generic, TypeVar, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.db.base_repository import BaseRepository

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(LoggerMixin, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class with common business logic operations."""

    def __init__(self, repository: BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]):
        self.repository = repository

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType
    ) -> ModelType:
        """Create a new record with business logic validation."""
        # Add any business logic validation here
        self.logger.info("Creating new record", model=self.repository.model.__name__)
        return await self.repository.create(db, obj_in=obj_in)

    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get record by ID."""
        record = await self.repository.get(db, id=id)
        if record:
            self.logger.info("Record retrieved", model=self.repository.model.__name__, id=id)
        return record

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters."""
        return await self.repository.get_multi(db, skip=skip, limit=limit, **filters)

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any]
    ) -> ModelType:
        """Update a record with business logic validation."""
        # Add any business logic validation here
        self.logger.info("Updating record", model=self.repository.model.__name__)
        return await self.repository.update(db, db_obj=db_obj, obj_in=obj_in)

    async def delete(self, db: AsyncSession, *, id: Any) -> bool:
        """Delete a record."""
        self.logger.info("Deleting record", model=self.repository.model.__name__, id=id)
        return await self.repository.delete(db, id=id)

    async def count(self, db: AsyncSession, **filters) -> int:
        """Count records with optional filters."""
        return await self.repository.count(db, **filters)
