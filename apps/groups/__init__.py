"""
Groups module for Face Recognition System

This module handles group management for organizing face recognition entities.
Groups can be either whitelist or blacklist type and support various configuration options.
"""

from .models import GroupCreate, GroupUpdate, GroupResponse, GroupListResponse
from .routes import router as groups_router

__all__ = [
    "GroupCreate",
    "GroupUpdate", 
    "GroupResponse",
    "GroupListResponse",
    "group_service",
    "groups_router"
]