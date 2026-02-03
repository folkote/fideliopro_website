"""
Logging middleware for FidelioPro FastAPI application.
"""

import time
import asyncio
from typing import Callable
from datetime import datetime
from urllib.parse import unquote

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger
from ..services.geolocation import geolocation_service
from ..services.country_codes import country_code_service


def decode_url_safe(url: str) -> str:
    """
    Safely decode URL-encoded string.
    
    Args:
        url: URL string that may contain encoded characters
        
    Returns:
        Decoded URL string, or original if decoding fails
    """
    try:
        return unquote(url, encoding='utf-8')
    except (UnicodeDecodeError, ValueError):
        return url  # Return original if decoding fails


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with geolocation data."""

    def __init__(self, app, logger_instance: FilteringBoundLogger = logger):
        super().__init__(app)
        self.logger = logger_instance

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request and log with geolocation data.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        start_time = time.time()

        # Extract request information
        client_ip = self._get_client_ip(request)
        method = request.method
        url = str(request.url)
        user_agent = request.headers.get("user-agent", "")

        # Start geolocation lookup asynchronously (fire and forget)
        geolocation_task = None
        if settings.geolocation_enabled and client_ip:
            geolocation_task = asyncio.create_task(
                self._get_geolocation_safe(client_ip)
            )

        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # Log the exception in compact format with decoded URL
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            decoded_url = decode_url_safe(url)
            self.logger.error(f"{timestamp} | {client_ip} (??/??) | {method} {decoded_url} | ERROR | {str(e)}")
            raise

        # Calculate processing time
        process_time = time.time() - start_time

        # Wait for geolocation (with timeout)
        geolocation_data = {"country": "", "city": "", "isp": ""}
        if geolocation_task:
            try:
                geolocation_data = await asyncio.wait_for(
                    geolocation_task, timeout=2.0  # Don't wait too long
                )
            except asyncio.TimeoutError:
                self.logger.debug("Geolocation lookup timeout", ip=client_ip)
                geolocation_task.cancel()
            except Exception as e:
                self.logger.debug(
                    "Geolocation lookup error", ip=client_ip, error=str(e)
                )

        # Format compact location info
        location_info = country_code_service.format_location(
            geolocation_data.get("country", ""),
            geolocation_data.get("city", "")
        )

        # Create compact log message with decoded URL
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        decoded_url = decode_url_safe(url)
        message = f"{timestamp} | {client_ip} ({location_info}) | {method} {decoded_url} | {status_code} | {process_time:.3f}s"

        # Log the request with appropriate level
        if status_code >= 500:
            self.logger.error(message)
        elif status_code >= 400:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Args:
            request: FastAPI request object

        Returns:
            Client IP address
        """
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

    async def _get_geolocation_safe(self, ip: str) -> dict:
        """
        Safely get geolocation data with error handling.

        Args:
            ip: IP address to lookup

        Returns:
            Geolocation data dictionary
        """
        try:
            return await geolocation_service.get_location(ip)
        except Exception as e:
            self.logger.debug("Geolocation error", ip=ip, error=str(e))
            return {"country": "", "city": "", "isp": ""}
