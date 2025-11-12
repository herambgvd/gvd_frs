# GVD FRS - Face Recognition System API

A FastAPI-based microservice for face recognition operations that integrates with GVD UMS (User Management System) for authentication.

## Features

- **Face Recognition Services**: Core face recognition and analysis capabilities
- **Authentication Integration**: Seamless integration with GVD UMS for JWT-based authentication
- **MongoDB Database**: Async MongoDB operations using Motor
- **Modular Architecture**: Clean, maintainable code structure
- **Organization-based Access Control**: Secure access control based on organization membership
- **RESTful API**: Comprehensive REST API with proper status codes and error handling

## Project Structure

```
gvd_frs/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── config/                # Configuration files
│   ├── __init__.py
│   ├── settings.py        # Application settings
│   └── database.py        # MongoDB configuration
├── apps/                  # Application modules (ready for future FRS modules)
│   └── __init__.py
├── middleware/            # Custom middleware
│   ├── __init__.py
│   ├── auth.py           # Authentication middleware
│   └── error_handler.py  # Error handling middleware
└── utils/                 # Utility functions
    └── __init__.py
```

## Installation

1. **Clone the repository** (if applicable)
2. **Create virtual environment** (already created in `.venv/`)
3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your configuration values.

5. **Start MongoDB** (make sure MongoDB is running)

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example` and configure:

- `MONGODB_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name for the application
- `JWT_SECRET_KEY`: JWT secret key (must match GVD UMS)
- `GVD_UMS_BASE_URL`: Base URL for GVD UMS service
- `CORS_ORIGINS`: Allowed CORS origins

### GVD UMS Integration

This service integrates with GVD UMS for authentication. Make sure:

1. GVD UMS is running and accessible
2. JWT secret keys match between services
3. User tokens from GVD UMS are valid for this service

## Running the Application

### Development Mode

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

## API Endpoints

### Health Check

- `GET /` - Root endpoint with service information
- `GET /health` - Health check endpoint
- `GET /db-test` - Database connection test

### Authentication

All future API endpoints will require authentication via JWT token from GVD UMS:

```
Authorization: Bearer <jwt_token>
```

## Security

- JWT token validation against GVD UMS
- Organization-based access control
- Input validation using Pydantic
- CORS protection
- Error handling without sensitive data exposure

## Database

Uses MongoDB for future face recognition data storage.

Indexes will be automatically created for optimal query performance.

## Development

### Adding New Features

1. Create new modules in `apps/` directory
2. Add database models in `models.py`
3. Define Pydantic schemas in `schemas.py`
4. Implement API routes in `routes.py`
5. Include router in `main.py`

### Testing

```bash
pytest
```

## Future Development

This service is prepared for implementing:

- Face detection and recognition algorithms
- Face embedding storage and comparison
- Real-time face analysis
- Integration with camera streams for live recognition

## Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Configure production MongoDB connection
3. Set up reverse proxy (nginx) if needed
4. Use process manager like supervisor or systemd
5. Configure logging and monitoring

## Troubleshooting

- **Connection Issues**: Check MongoDB connection and GVD UMS availability
- **Authentication Errors**: Verify JWT secret key matches GVD UMS
- **Permission Errors**: Ensure user has correct organization access

## License

[Your License Here]
