# GVD-FRS FastAPI Project

A production-ready FastAPI application with license key-based authentication, structured logging, and modular architecture.

## Features

- **License Key Authentication**: Secure API access using license keys instead of traditional JWT tokens
- **Structured Logging**: JSON-formatted logging with request tracking using structlog
- **Modular Architecture**: Clean separation of concerns with proper folder structure
- **Comprehensive Error Handling**: Custom exceptions with detailed error responses
- **Health Monitoring**: Built-in health check endpoints
- **Permission-based Access**: Role-based permissions (read, write, admin)
- **Usage Tracking**: Monitor API usage per license key
- **Test Suite**: Comprehensive test coverage with pytest

## Project Structure

```
gvd_frs/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # API router configuration
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py   # Health check endpoints
│   │           ├── license.py  # License management
│   │           └── demo.py     # Demo endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Application settings
│   │   ├── logging.py          # Structured logging setup
│   │   ├── security.py         # License key authentication
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── middleware.py       # Custom middleware
│   │   └── exception_handlers.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # Database configuration
│   │   └── base_repository.py  # Repository pattern
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── base.py            # Base Pydantic schemas
│   │   └── license.py         # License-related schemas
│   ├── services/
│   │   ├── __init__.py
│   │   └── base_service.py    # Base service class
│   └── utils/
│       ├── __init__.py
│       └── helpers.py         # Utility functions
├── tests/
│   ├── conftest.py            # Test configuration
│   ├── unit/
│   │   └── test_endpoints.py  # Unit tests
│   ├── integration/
│   └── e2e/
├── logs/                      # Application logs
├── scripts/                   # Deployment scripts
├── docs/                      # Documentation
├── .env.example              # Environment variables template
├── pyproject.toml            # Project configuration
└── main.py                   # Application entry point
```

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API documentation**:
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

## License Key Authentication

This application uses license key-based authentication instead of traditional JWT tokens. Here's how it works:

### Demo License Keys

The application comes with two pre-configured demo license keys:

1. **Demo License Key**: `gvd-demo-key-12345`
   - Client: "Demo Client"
   - Permissions: `["read", "write"]`
   - No usage limit

2. **Premium License Key**: `gvd-premium-key-67890`
   - Client: "Premium Client"
   - Permissions: `["read", "write", "admin"]`
   - Usage limit: 10,000 requests

### Using License Keys

Include your license key in one of these headers:

1. **Authorization header** (Bearer token format):
   ```bash
   curl -H "Authorization: Bearer gvd-demo-key-12345" http://localhost:8000/api/v1/demo/protected
   ```

2. **X-License-Key header**:
   ```bash
   curl -H "X-License-Key: gvd-demo-key-12345" http://localhost:8000/api/v1/demo/protected
   ```

3. **License-Key header**:
   ```bash
   curl -H "License-Key: gvd-demo-key-12345" http://localhost:8000/api/v1/demo/protected
   ```

### API Endpoints

#### Public Endpoints
- `GET /` - Root endpoint
- `GET /api/v1/health/health` - Health check
- `GET /api/v1/demo/public` - Public demo endpoint

#### Protected Endpoints (Require License Key)
- `GET /api/v1/demo/protected` - Basic protected endpoint
- `GET /api/v1/demo/read-only` - Requires 'read' permission
- `POST /api/v1/demo/write-data` - Requires 'write' permission
- `GET /api/v1/demo/admin-only` - Requires 'admin' permission

#### License Management
- `GET /api/v1/license/validate` - Validate current license key
- `GET /api/v1/license/info` - Get license information
- `POST /api/v1/license/generate` - Generate new license key (admin only)
- `POST /api/v1/license/revoke` - Revoke license key (admin only)

### Permission System

The application supports three permission levels:

1. **read**: Basic read access to resources
2. **write**: Read and write access to resources  
3. **admin**: Full administrative access

### License Key Features

- **Expiration**: License keys can have expiration dates
- **Usage Limits**: Track and limit API usage per license key
- **Permissions**: Fine-grained permission control
- **Active/Inactive**: Enable/disable license keys
- **Usage Tracking**: Monitor API calls per license key

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_endpoints.py -v
```

## Logging

The application uses structured logging with the following features:

- **JSON Format**: Machine-readable logs in production
- **Pretty Format**: Human-readable logs in development
- **Request Tracking**: Each request gets a unique ID
- **Contextual Logging**: Rich context in log messages
- **File and Console**: Logs to both file and console

## Configuration

Key configuration options in `.env`:

```env
# Application
APP_NAME=GVD-FRS
ENVIRONMENT=development
DEBUG=true

# License Authentication
LICENSE_KEY_HEADER=X-License-Key
ENABLE_LICENSE_USAGE_TRACKING=true
DEFAULT_LICENSE_EXPIRY_DAYS=365

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/gvd_frs

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Security Features

- **License Key Validation**: Secure key validation with expiration
- **Permission-based Access**: Role-based access control
- **Usage Tracking**: Monitor and limit API usage
- **Security Headers**: Automatic security headers
- **Request Logging**: Comprehensive request/response logging
- **Error Handling**: Secure error responses without data leakage
