"""
Error Handler Middleware for GVD FRS API
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from typing import Union

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handler middleware"""

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "message": e.detail,
                    "error_type": "HTTPException"
                }
            )
        
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": "Invalid input data",
                    "error_type": "ValidationError",
                    "details": str(e)
                }
            )
        
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "error_type": "InternalError"
                }
            )