# GVD-FRS API Postman Collection

This directory contains a complete Postman collection for the **GVD-FRS (Global Vulnerability Database - Facial Recognition System)** API, including environment configurations and comprehensive documentation.

## 📁 Files Overview

- `GVD-FRS-API-Collection.postman_collection.json` - Complete API collection with all endpoints
- `GVD-FRS-Development.postman_environment.json` - Development environment configuration
- `GVD-FRS-Production.postman_environment.json` - Production environment template
- `README.md` - This documentation file

## 🚀 Quick Start

### 1. Import Collection and Environment

1. **Import Collection:**
   - Open Postman
   - Click "Import" → Select `GVD-FRS-API-Collection.postman_collection.json`

2. **Import Environment:**
   - Click "Import" → Select `GVD-FRS-Development.postman_environment.json`
   - Select the "GVD-FRS Development" environment in the top right corner

### 2. Start the API Server

Ensure your GVD-FRS API server is running:
```bash
cd /path/to/gvd_frs
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the Collection

Start with the health check endpoint to verify connectivity:
- Navigate to **Health & System** → **Health Check**
- Click "Send"

## 🔐 Authentication

The GVD-FRS API uses **License Key Authentication** with the `X-API-Key` header.

### Available Demo License Keys

| License Key | Permissions | Description |
|-------------|-------------|-------------|
| `gvd-demo-key-12345` | read, write | Demo license for testing |
| `gvd-premium-key-67890` | read, write, admin | Admin license with full access |

### Permission Levels

- **Read**: View data (GET requests)
- **Write**: Modify data (POST, PUT requests)
- **Admin**: Full access including delete operations and license management

## 📊 Collection Structure

### 1. Health & System
- **Health Check** - Verify API and database status
- **Demo Info** - Get application information

### 2. License Management
- **Get My License Info** - View current license details
- **Create License** - Generate new license (Admin only)
- **List All Licenses** - View all licenses with filtering (Admin only)
- **Get License by ID** - Retrieve specific license (Admin only)
- **Update License** - Modify license properties (Admin only)
- **Delete License** - Remove license (Admin only)
- **Validate License Key** - Check license validity
- **Revoke License** - Deactivate license (Admin only)
- **Activate License** - Reactivate license (Admin only)
- **Reset License Usage** - Reset usage counter (Admin only)
- **Get License Statistics** - View license metrics

### 3. Tenant Management
- **Create Tenant** - Add new tenant (Admin only)
- **List All Tenants** - View tenants with filtering
- **Get Tenant by ID** - Retrieve specific tenant
- **Update Tenant** - Modify tenant properties (Write permission)
- **Delete Tenant** - Remove tenant (Admin only)
- **Activate Tenant** - Set tenant status to active (Admin only)
- **Deactivate Tenant** - Set tenant status to inactive (Admin only)
- **Suspend Tenant** - Suspend tenant access (Admin only)
- **Get Tenant Statistics** - View tenant metrics
- **Increment User Count** - Add user to tenant (Write permission)
- **Decrement User Count** - Remove user from tenant (Write permission)

## 🌍 Environment Variables

### Development Environment
```json
{
  "base_url": "http://localhost:8000",
  "license_key": "gvd-demo-key-12345",
  "admin_license_key": "gvd-premium-key-67890",
  "write_license_key": "gvd-demo-key-12345",
  "license_id": "1",
  "tenant_id": "tenant-demo-001"
}
```

### Production Environment Setup
1. Copy `GVD-FRS-Production.postman_environment.json`
2. Update the following variables:
   - `base_url`: Your production API URL
   - `license_key`: Your production license key
   - `admin_license_key`: Your production admin license key
   - `write_license_key`: Your production write license key

## 🧪 Testing Guidelines

### Basic API Testing Flow

1. **Health Check**
   ```
   GET /api/v1/health/
   Expected: 200 OK with system status
   ```

2. **Authentication Test**
   ```
   GET /api/v1/licenses/my-info
   Header: X-API-Key: gvd-demo-key-12345
   Expected: 200 OK with license information
   ```

3. **Permission Testing**
   ```
   # Test read permission
   GET /api/v1/tenants/
   Header: X-API-Key: gvd-demo-key-12345
   
   # Test admin permission
   POST /api/v1/licenses/
   Header: X-API-Key: gvd-premium-key-67890
   ```

### Automated Testing

The collection includes pre-request and test scripts that:
- Validate response times (< 5000ms)
- Check content types for successful responses
- Handle authentication/authorization errors
- Log request/response information

## 📝 Request Examples

### Creating a License
```json
POST /api/v1/licenses/
Headers: X-API-Key: gvd-premium-key-67890
Body:
{
  "client_name": "New Client Company",
  "client_id": "client-new-001",
  "permissions": ["read", "write"],
  "is_active": true,
  "expires_in_days": 365,
  "usage_limit": 5000,
  "tenant_id": "tenant-new-001"
}
```

### Creating a Tenant
```json
POST /api/v1/tenants/
Headers: X-API-Key: gvd-premium-key-67890
Body:
{
  "id": "tenant-new-001",
  "name": "New Tenant Organization",
  "description": "A new tenant for testing purposes",
  "domain": "newtenant.example.com",
  "status": "ACTIVE",
  "max_users": 100,
  "contact_email": "admin@newtenant.example.com",
  "contact_phone": "+1-555-0123",
  "created_by": "admin-user",
  "settings": {
    "feature_flags": {
      "advanced_analytics": true,
      "export_data": false
    },
    "theme": "dark"
  }
}
```

## 🔄 Response Formats

### Successful Response (200 OK)
```json
{
  "id": 1,
  "license_key": "gvd-1234567890abcdef",
  "client_name": "Demo Client",
  "client_id": "demo-001",
  "permissions": ["read", "write"],
  "is_active": true,
  "expires_at": "2025-09-29T12:00:00Z",
  "usage_limit": 5000,
  "current_usage": 42,
  "tenant_id": "tenant-demo-001",
  "created_at": "2024-09-29T12:00:00Z",
  "updated_at": "2024-09-29T12:00:00Z"
}
```

### Error Response (401 Unauthorized)
```json
{
  "detail": "X-API-Key header is required"
}
```

### Error Response (403 Forbidden)
```json
{
  "detail": "Permission 'admin' required"
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Ensure `X-API-Key` header is present
   - Verify license key is valid and active
   - Check license key hasn't expired

2. **403 Forbidden**
   - Verify license has required permissions
   - Use admin license key for admin operations
   - Check license usage limits

3. **404 Not Found**
   - Verify the resource ID exists
   - Check the endpoint URL is correct
   - Ensure the API server is running

4. **422 Validation Error**
   - Check request body format
   - Verify required fields are present
   - Validate data types match schema

### API Server Not Running
```bash
# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Check if server is running
curl http://localhost:8000/api/v1/health/
```

## 📋 Collection Features

### Pre-request Scripts
- Set dynamic timestamps
- Validate license key presence
- Log request information

### Test Scripts
- Response time validation
- Content type verification
- Authentication error handling
- Status code logging

### Variables
- Environment-specific configurations
- Reusable license keys
- Dynamic IDs for testing

## 🔄 Updating the Collection

When the API changes:

1. **Add New Endpoints**
   - Create new request in appropriate folder
   - Set correct HTTP method and URL
   - Add required headers and body
   - Include description

2. **Update Environment Variables**
   - Add new variables as needed
   - Update existing values
   - Maintain environment parity

3. **Test Changes**
   - Run collection tests
   - Verify all endpoints work
   - Update documentation

## 📞 Support

For issues with the API or Postman collection:
1. Check the troubleshooting guide above
2. Verify your environment setup
3. Test with the health check endpoint
4. Review the API logs for detailed error information

---

**Last Updated:** September 29, 2025
**API Version:** v0.1.0
**Collection Version:** 1.0.0
