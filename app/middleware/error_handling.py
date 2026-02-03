"""
Error handling middleware for FidelioPro FastAPI application.
"""

import traceback
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.typing import FilteringBoundLogger

from ..utils.logger import logger, safe_log_data
from ..models.responses import ErrorResponse


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging."""

    def __init__(self, app, logger_instance: FilteringBoundLogger = logger):
        super().__init__(app)
        self.logger = logger_instance

    async def dispatch(self, request: Request, call_next):
        """
        Handle errors and exceptions in HTTP requests.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response or error response
        """
        try:
            response = await call_next(request)
            return response

        except HTTPException as e:
            # FastAPI HTTP exceptions (expected errors)
            self.logger.warning(
                "HTTP exception",
                **safe_log_data(
                    {
                        "status_code": e.status_code,
                        "detail": str(e.detail),
                        "url": str(request.url),
                        "method": request.method,
                    }
                ),
            )

            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error=str(e.detail), code=f"HTTP_{e.status_code}"
                ).dict(),
            )

        except UnicodeDecodeError as e:
            # Handle encoding errors (common with malicious requests)
            self.logger.warning(
                "Unicode decode error",
                **safe_log_data(
                    {"error": str(e), "url": str(request.url), "method": request.method}
                ),
            )

            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Invalid character encoding in request", code="ENCODING_ERROR"
                ).dict(),
            )

        except ValueError as e:
            # Handle validation errors
            self.logger.warning(
                "Validation error",
                **safe_log_data(
                    {"error": str(e), "url": str(request.url), "method": request.method}
                ),
            )

            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error="Invalid request data", detail=str(e), code="VALIDATION_ERROR"
                ).dict(),
            )

        except ConnectionError as e:
            # Handle connection errors (external services)
            self.logger.error(
                "Connection error",
                **safe_log_data(
                    {"error": str(e), "url": str(request.url), "method": request.method}
                ),
            )

            return JSONResponse(
                status_code=503,
                content=ErrorResponse(
                    error="External service temporarily unavailable",
                    code="SERVICE_UNAVAILABLE",
                ).dict(),
            )

        except TimeoutError as e:
            # Handle timeout errors
            self.logger.error(
                "Timeout error",
                **safe_log_data(
                    {"error": str(e), "url": str(request.url), "method": request.method}
                ),
            )

            return JSONResponse(
                status_code=504,
                content=ErrorResponse(
                    error="Request timeout", code="TIMEOUT_ERROR"
                ).dict(),
            )

        except Exception as e:
            # Handle unexpected errors
            error_id = id(e)  # Simple error ID for tracking

            self.logger.error(
                "Unexpected error",
                **safe_log_data(
                    {
                        "error_id": error_id,
                        "error_type": type(e).__name__,
                        "error": str(e),
                        "url": str(request.url),
                        "method": request.method,
                        "traceback": traceback.format_exc(),
                    }
                ),
            )

            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="Internal server error",
                    detail=f"Error ID: {error_id}",
                    code="INTERNAL_ERROR",
                ).dict(),
            )


def create_http_exception_handler():
    """Create HTTP exception handler for FastAPI."""

    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        logger.warning(
            "HTTP exception handler",
            **safe_log_data(
                {
                    "status_code": exc.status_code,
                    "detail": str(exc.detail),
                    "url": str(request.url),
                    "method": request.method,
                }
            ),
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=str(exc.detail), code=f"HTTP_{exc.status_code}"
            ).dict(),
        )

    return http_exception_handler


def create_validation_exception_handler():
    """Create validation exception handler for FastAPI."""

    async def validation_exception_handler(request: Request, exc):
        """Handle validation exceptions."""
        logger.warning(
            "Validation exception handler",
            **safe_log_data(
                {
                    "errors": str(exc.errors()),
                    "url": str(request.url),
                    "method": request.method,
                }
            ),
        )

        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="Validation error",
                detail=str(exc.errors()),
                code="VALIDATION_ERROR",
            ).dict(),
        )

    return validation_exception_handler
