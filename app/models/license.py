"""
License model for the GVD-FRS application.
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class License(Base):
    """License model for the GVD-FRS system."""

    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    license_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    permissions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of permissions list
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_usage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("tenants.id"), nullable=True)

    # Relationship with tenant
    tenant: Mapped[Optional["Tenant"]] = relationship("Tenant", back_populates="licenses")

    def __repr__(self) -> str:
        return f"<License(license_key='{self.license_key[:16]}...', client_name='{self.client_name}')>"
