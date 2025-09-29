"""
Common utility functions for the application.
"""
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_hash(data: str, algorithm: str = "sha256") -> str:
    """Generate hash for given data."""
    if algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    elif algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def sanitize_string(text: str, max_length: int = 255) -> str:
    """Sanitize string input."""
    if not isinstance(text, str):
        return ""

    # Remove special characters and limit length
    sanitized = re.sub(r'[^\w\s-]', '', text.strip())
    return sanitized[:max_length]


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


def paginate_results(
    items: List[Any],
    skip: int = 0,
    limit: int = 100
) -> Dict[str, Any]:
    """Paginate a list of items."""
    total = len(items)
    paginated_items = items[skip:skip + limit]

    return {
        "items": paginated_items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": skip + limit < total,
        "has_previous": skip > 0,
    }


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data showing only first few characters."""
    if len(data) <= visible_chars:
        return "*" * len(data)
    return data[:visible_chars] + "*" * (len(data) - visible_chars)
