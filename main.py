"""
GVD FRS (Face Recognition System) Main Application
Fast API application with modular structure
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from config.database import connect_to_mongodb, close_mongodb_connection
from middleware.error_handler import ErrorHandlerMiddleware
from config.settings import settings

# Import routers
from apps.groups.routes import router as groups_router
from apps.poi.routes import router as poi_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongodb()
    yield
    # Shutdown
    await close_mongodb_connection()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="GVD FRS API",
        description="Face Recognition System",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)

    # Include routers
    app.include_router(groups_router, prefix="/api")
    app.include_router(poi_router)

    @app.get("/")
    async def root():
        return {
            "message": "GVD FRS API",
            "version": "1.0.0",
            "status": "running"
        }

    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": "2025-11-05T00:00:00Z"
        }

    @app.get("/db-test")
    async def db_test():
        """Test database connection without authentication"""
        try:
            from config.database import database
            if database.database is None:
                return {"status": "error", "message": "Database not connected"}
            else:
                return {"status": "success", "message": "Database connected", "db_name": settings.DATABASE_NAME}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
        log_level="info"
    )