"""
Tenant model for the GVD-FRS application.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.license import License


class TenantStatus(str, enum.Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Tenant(Base):
    """Tenant model for multi-tenant architecture."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    status: Mapped[TenantStatus] = mapped_column(
        SQLEnum(TenantStatus),
        default=TenantStatus.ACTIVE,
        nullable=False
    )
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string for tenant settings
    max_users: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationship with licenses
    licenses: Mapped[List["License"]] = relationship("License", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant(id='{self.id}', name='{self.name}', status='{self.status}')>"
