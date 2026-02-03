"""
API routers for address cleaning endpoints.
"""

from typing import Union
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse, HTMLResponse

from ..config import settings
from ..models.requests import AddressRequest
from ..models.responses import ErrorResponse, HealthResponse
from ..services.dadata import dadata_service
from ..services.geolocation import geolocation_service
from ..utils.logger import logger, safe_log_data
from datetime import datetime


# Create API router
router = APIRouter()


@router.get(
    "/apiaddress/api",
    response_class=PlainTextResponse,
    summary="Get street FIAS ID for address",
    description="Clean address and return street FIAS ID using DaData API",
    responses={
        200: {
            "description": "Street FIAS ID",
            "content": {
                "text/plain": {"example": "0c5b2444-70a0-4932-980c-b4dc0d3f02b5"}
            },
        },
        400: {"description": "Invalid address parameter"},
        500: {"description": "Internal server error"},
    },
)
async def api_address(
    address: str = Query(
        ...,
        description="Address to be cleaned and validated",
        min_length=1,
        max_length=500,
        example="Москва, ул. Тверская, д. 1",
    )
):
    """
    Get street FIAS ID for the provided address.

    This endpoint maintains compatibility with the original Flask application.
    """
    if not address or not address.strip():
        raise HTTPException(status_code=400, detail="Address parameter is missing")

    try:
        # Clean the address
        cleaned_address = address.strip()

        # Get street FIAS ID from DaData
        fias_id = await dadata_service.get_street_fias_id(cleaned_address)

        if fias_id is None:
            logger.warning("Address cleaning failed", address=cleaned_address[:50])
            raise HTTPException(
                status_code=400, detail="Address is incorrect! Check the guest address!"
            )

        logger.info(
            "Address API success",
            **safe_log_data({"address": cleaned_address[:50], "fias_id": fias_id}),
        )

        # Return the FIAS ID as plain string
        return str(fias_id) if fias_id else ""

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Address API error", error=str(e), address=address[:50])
        raise HTTPException(status_code=500, detail="An internal server error occurred")


@router.get(
    "/apifulladdress/api",
    response_class=PlainTextResponse,
    summary="Get cleaned address text",
    description="Clean address and return cleaned address text using DaData API",
    responses={
        200: {
            "description": "Cleaned address text",
            "content": {
                "text/plain": {"example": "Астраханская обл, г Астрахань, пл Заводская"}
            },
        },
        400: {"description": "Invalid address parameter"},
        500: {"description": "Internal server error"},
    },
)
async def api_full_address(
    address: str = Query(
        ...,
        description="Address to be cleaned and validated",
        min_length=1,
        max_length=500,
        example="Москва, ул. Тверская, д. 1",
    )
):
    """
    Get cleaned address text from DaData API.

    This endpoint maintains compatibility with the original Flask application.
    """
    if not address or not address.strip():
        raise HTTPException(status_code=400, detail="Address parameter is missing")

    try:
        # Clean the address
        cleaned_address = address.strip()

        # Get cleaned address text from DaData
        cleaned_text = await dadata_service.get_cleaned_address_text(cleaned_address)

        if cleaned_text is None:
            logger.warning("Address cleaning failed", address=cleaned_address[:50])
            raise HTTPException(
                status_code=400, detail="Address is incorrect! Check the guest address!"
            )

        logger.info(
            "Full address API success",
            **safe_log_data(
                {
                    "address": cleaned_address[:50],
                    "cleaned_text": cleaned_text[:50],
                }
            ),
        )

        # Return the cleaned address text as plain string
        return cleaned_text

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Full address API error", error=str(e), address=address[:50])
        raise HTTPException(status_code=500, detail="An internal server error occurred")


@router.get(
    "/health",
    response_class=HTMLResponse,
    summary="Health check endpoint",
    description="Check the health status of the application and its dependencies",
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns a beautiful HTML page showing system health status.
    """
    try:
        # Read the HTML template
        import os
        from pathlib import Path

        # Get the path to the health.html file
        current_dir = Path(__file__).parent.parent.parent  # Go up to project root
        health_html_path = current_dir / "static" / "website" / "health.html"

        if health_html_path.exists():
            with open(health_html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content, status_code=200)
        else:
            # Fallback to JSON if HTML file not found
            logger.warning("Health HTML template not found, falling back to JSON")
            return await health_check_json()

    except Exception as e:
        logger.error("Health check error", error=str(e))
        # Fallback to simple HTML error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Health Check Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1e2a3a; color: white; text-align: center; padding: 50px; }}
                .error {{ background: #f44336; padding: 20px; border-radius: 10px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Health Check Failed</h1>
                <p>Error: {str(e)}</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html, status_code=500)


@router.get(
    "/health/json",
    response_model=HealthResponse,
    summary="Health check JSON endpoint",
    description="Check the health status of the application and its dependencies (JSON format)",
)
async def health_check_json():
    """
    Health check endpoint for monitoring and load balancers (JSON format).
    """
    try:
        # Check DaData service
        dadata_healthy = await dadata_service.health_check()

        # Check geolocation service
        geolocation_healthy = await geolocation_service.health_check()

        # Check cache service (always healthy for file cache)
        cache_healthy = True

        services = {
            "dadata": "healthy" if dadata_healthy else "unhealthy",
            "geolocation": "healthy" if geolocation_healthy else "unhealthy",
            "cache": "healthy" if cache_healthy else "unhealthy",
        }

        # Overall status
        overall_status = (
            "healthy" if all([dadata_healthy, cache_healthy]) else "degraded"
        )

        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            timestamp=datetime.now().isoformat(),
            services=services,
        )

    except Exception as e:
        logger.error("Health check JSON error", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get(
    "/metrics",
    summary="Application metrics",
    description="Get basic application metrics (if enabled)",
)
async def get_metrics():
    """
    Basic metrics endpoint for monitoring.
    """
    try:
        # Basic metrics - can be extended with proper metrics library
        metrics = {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "timestamp": datetime.now().isoformat(),
            "cache_enabled": settings.cache_enabled,
            "geolocation_enabled": settings.geolocation_enabled,
        }

        return metrics

    except Exception as e:
        logger.error("Metrics error", error=str(e))
        raise HTTPException(status_code=500, detail="Metrics unavailable")
