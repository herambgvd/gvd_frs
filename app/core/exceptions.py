"""
Custom exceptions for the GVD-FRS application.
"""
from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base exception class for application-specific errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class LicenseException(BaseAppException):
    """Exception for license-related errors."""
    pass


class LicenseNotFoundException(LicenseException):
    """Exception raised when a license is not found."""

    def __init__(self, license_key: str):
        super().__init__(
            message=f"License not found: {license_key}",
            status_code=404,
            details={"license_key": license_key}
        )


class LicenseExpiredException(LicenseException):
    """Exception raised when a license has expired."""

    def __init__(self, license_key: str):
        super().__init__(
            message=f"License has expired: {license_key}",
            status_code=403,
            details={"license_key": license_key}
        )


class LicenseInactiveException(LicenseException):
    """Exception raised when a license is inactive."""

    def __init__(self, license_key: str):
        super().__init__(
            message=f"License is inactive: {license_key}",
            status_code=403,
            details={"license_key": license_key}
        )


class TenantException(BaseAppException):
    """Exception for tenant-related errors."""
    pass


class TenantNotFoundException(TenantException):
    """Exception raised when a tenant is not found."""

    def __init__(self, tenant_id: int):
        super().__init__(
            message=f"Tenant not found: {tenant_id}",
            status_code=404,
            details={"tenant_id": tenant_id}
        )


class DatabaseException(BaseAppException):
    """Exception for database-related errors."""

    def __init__(self, message: str, operation: str):
        super().__init__(
            message=f"Database error during {operation}: {message}",
            status_code=500,
            details={"operation": operation}
        )
