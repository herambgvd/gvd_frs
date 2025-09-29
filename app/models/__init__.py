"""
Database models for the GVD-FRS application.

This module imports all models to make them available for import
and ensures they are registered with SQLAlchemy for migrations.
"""

# Import all models to register them with SQLAlchemy
from app.models.tenant import Tenant
from app.models.license import License

# Make models available for import
__all__ = ["Tenant", "License"]
