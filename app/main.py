"""
Main FastAPI application for FidelioPro.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import settings
from .utils.logger import logger
from .middleware.logging import LoggingMiddleware
from .middleware.error_handling import (
    ErrorHandlingMiddleware,
    create_http_exception_handler,
    create_validation_exception_handler,
)
from .routers import api, static_files
from .services.cache import cache_service
from .services.dadata import dadata_service
from .services.geolocation import geolocation_service


# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting FidelioPro FastAPI application", version=settings.app_version)

    try:
        # Initialize services
        await cache_service.initialize()
        await dadata_service.initialize()
        await geolocation_service.initialize()

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down FidelioPro FastAPI application")

    try:
        # Close services
        await cache_service.close()
        await dadata_service.close()
        await geolocation_service.close()

        logger.info("All services closed successfully")

    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FidelioPro FastAPI - Address cleaning and static website server",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Add custom middleware (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Add rate limiting middleware
if settings.rate_limit_enabled:
    app.add_middleware(SlowAPIMiddleware)

# Add exception handlers
app.add_exception_handler(HTTPException, create_http_exception_handler())
app.add_exception_handler(RequestValidationError, create_validation_exception_handler())

# Include routers
app.include_router(api.router, tags=["API"])

# Static files router should be last to catch all remaining paths
app.include_router(static_files.router, tags=["Static Files"])


# Rate limited endpoints
@app.get("/api/limited-test")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def limited_test(request):
    """Test endpoint with rate limiting."""
    return {"message": "This endpoint is rate limited"}


# Root endpoint (handled by static_files router)
# This is just for documentation purposes
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - handled by static files router."""
    pass


if __name__ == "__main__":
    import uvicorn

    # Configure uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default"],
        },
    }

    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_config=log_config,
        reload=settings.debug,
        access_log=False,  # We handle access logging in middleware
    )
