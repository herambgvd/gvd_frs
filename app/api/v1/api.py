"""
Main API router for version 1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, demo, license, tenant

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(demo.router, prefix="/demo", tags=["demo"])
api_router.include_router(license.router, tags=["licenses"])
api_router.include_router(tenant.router, tags=["tenants"])
