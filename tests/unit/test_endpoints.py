"""
Test cases for license key authentication and demo endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestDemoEndpoints:
    """Test demo endpoints with license key authentication."""

    def test_public_endpoint_no_auth(self, client: TestClient):
        """Test public endpoint doesn't require authentication."""
        response = client.get("/api/v1/demo/public")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "public" in data["message"]

    def test_protected_endpoint_no_auth(self, client: TestClient):
        """Test protected endpoint requires authentication."""
        response = client.get("/api/v1/demo/protected")
        assert response.status_code == 401
        data = response.json()
        assert "License key required" in data["error"]["message"]

    def test_protected_endpoint_with_auth(self, client: TestClient, auth_headers: dict):
        """Test protected endpoint with valid license key."""
        response = client.get("/api/v1/demo/protected", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["client_name"] == "Demo Client"

    def test_read_only_endpoint(self, client: TestClient, auth_headers: dict):
        """Test read-only endpoint with read permission."""
        response = client.get("/api/v1/demo/read-only", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["required_permission"] == "read"

    def test_write_endpoint(self, client: TestClient, auth_headers: dict):
        """Test write endpoint with write permission."""
        test_data = {"key": "value", "number": 123}
        response = client.post("/api/v1/demo/write-data", headers=auth_headers, json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["written_data"] == test_data

    def test_admin_endpoint_with_regular_license(self, client: TestClient, auth_headers: dict):
        """Test admin endpoint with regular license key (should fail)."""
        response = client.get("/api/v1/demo/admin-only", headers=auth_headers)
        assert response.status_code == 403
        data = response.json()
        assert "admin" in data["error"]["message"]

    def test_admin_endpoint_with_admin_license(self, client: TestClient, admin_auth_headers: dict):
        """Test admin endpoint with admin license key."""
        response = client.get("/api/v1/demo/admin-only", headers=admin_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["required_permission"] == "admin"


class TestLicenseEndpoints:
    """Test license management endpoints."""

    def test_validate_license_key(self, client: TestClient, auth_headers: dict):
        """Test license key validation."""
        response = client.get("/api/v1/license/validate", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["license_info"]["client_name"] == "Demo Client"

    def test_get_license_info(self, client: TestClient, auth_headers: dict):
        """Test getting license information."""
        response = client.get("/api/v1/license/info", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["client_name"] == "Demo Client"

    def test_generate_license_key_no_admin(self, client: TestClient, auth_headers: dict):
        """Test license generation without admin permission."""
        license_data = {
            "client_name": "Test Client",
            "client_id": "test-001",
            "permissions": ["read"]
        }
        response = client.post("/api/v1/license/generate", headers=auth_headers, json=license_data)
        assert response.status_code == 403

    def test_generate_license_key_with_admin(self, client: TestClient, admin_auth_headers: dict):
        """Test license generation with admin permission."""
        license_data = {
            "client_name": "Test Client",
            "client_id": "test-001",
            "permissions": ["read", "write"]
        }
        response = client.post("/api/v1/license/generate", headers=admin_auth_headers, json=license_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "license_key" in data["data"]


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/api/v1/health/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "version" in data
