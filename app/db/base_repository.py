"""
Base repository pattern for database operations.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.logging import get_logger

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)

        logger.info(
            "Created new record",
            model=self.model.__name__,
            record_id=getattr(db_obj, 'id', None)
        )
        return db_obj

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """Get record by ID."""
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
            self,
            db: AsyncSession,
            *,
            skip: int = 0,
            limit: int = 100,
            **filters
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters."""
        query = select(self.model)

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: ModelType,
                     obj_in: UpdateSchemaType | Dict[str, Any]) -> ModelType:
        """Update a record."""
        if hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await db.flush()
        await db.refresh(db_obj)

        logger.info(
            "Updated record",
            model=self.model.__name__,
            record_id=getattr(db_obj, 'id', None)
        )
        return db_obj

    async def delete(self, db: AsyncSession, *, id: Any) -> bool:
        """Delete a record by ID."""
        result = await db.execute(delete(self.model).where(self.model.id == id))
        deleted = result.rowcount > 0

        if deleted:
            logger.info(
                "Deleted record",
                model=self.model.__name__,
                record_id=id
            )

        return deleted

    async def count(self, db: AsyncSession, **filters) -> int:
        """Count records with optional filters."""
        query = select(func.count(self.model.id))

        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        result = await db.execute(query)
        return result.scalar() or 0
