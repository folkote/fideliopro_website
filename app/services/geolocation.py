"""
Asynchronous IP geolocation service with fallback and caching.
"""

import asyncio
from typing import Optional, Dict, Any, List
import aiohttp
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger, safe_log_data
from .cache import cache_service


class GeolocationService:
    """Asynchronous IP geolocation service with multiple providers and fallback."""

    def __init__(self, logger_instance: FilteringBoundLogger = logger):
        self.logger = logger_instance
        self.session: Optional[aiohttp.ClientSession] = None

        # Primary and fallback services
        self.services = [
            {
                "name": "ip-api",
                "url": settings.geolocation_service_url,
                "fields": ["status", "country", "city", "isp"],
            },
            {
                "name": "ipapi",
                "url": settings.geolocation_fallback_service,
                "fields": ["country_name", "city", "org"],
            },
        ]

    async def initialize(self):
        """Initialize the geolocation service."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=settings.geolocation_timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout, headers={"User-Agent": "FidelioPro-FastAPI/1.0"}
            )
            self.logger.info("Geolocation service initialized")

    async def close(self):
        """Close the geolocation service."""
        if self.session:
            await self.session.close()
            self.session = None

    async def get_location(self, ip: str) -> Dict[str, str]:
        """
        Get geolocation data for IP address.

        Args:
            ip: IP address to lookup

        Returns:
            Dictionary with country, city, isp fields
        """
        if not settings.geolocation_enabled:
            return {"country": "", "city": "", "isp": ""}

        # Skip private/local IPs
        if self._is_private_ip(ip):
            return {"country": "Local", "city": "Local", "isp": "Local"}

        # Check cache first
        cache_key = f"geolocation_{ip}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            self.logger.debug("Geolocation cache hit", ip=ip)
            return cached_result

        # Try each service with fallback
        for service in self.services:
            try:
                result = await self._query_service(ip, service)
                if result and any(result.values()):
                    # Cache successful result
                    await cache_service.set(cache_key, result, ttl=settings.cache_ttl)
                    return result

            except Exception as e:
                self.logger.warning(
                    "Geolocation service failed",
                    ip=ip,
                    service=service["name"],
                    error=str(e),
                )
                continue

        # All services failed, return empty result
        empty_result = {"country": "", "city": "", "isp": ""}
        self.logger.warning("All geolocation services failed", ip=ip)

        # Cache empty result for shorter time to retry sooner
        await cache_service.set(cache_key, empty_result, ttl=300)  # 5 minutes

        return empty_result

    async def _query_service(self, ip: str, service: Dict[str, Any]) -> Dict[str, str]:
        """
        Query a specific geolocation service.

        Args:
            ip: IP address to lookup
            service: Service configuration

        Returns:
            Normalized geolocation data
        """
        await self.initialize()

        if not self.session:
            raise Exception("Session not initialized")

        url = service["url"].format(ip=ip)

        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._normalize_response(data, service)
            else:
                raise Exception(f"HTTP {response.status}")

    def _normalize_response(
        self, data: Dict[str, Any], service: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Normalize response from different geolocation services.

        Args:
            data: Raw response data
            service: Service configuration

        Returns:
            Normalized geolocation data
        """
        result = {"country": "", "city": "", "isp": ""}

        if service["name"] == "ip-api":
            # ip-api.com format
            if data.get("status") == "success":
                result["country"] = data.get("country", "")
                result["city"] = data.get("city", "")
                result["isp"] = data.get("isp", "")

        elif service["name"] == "ipapi":
            # ipapi.co format
            result["country"] = data.get("country_name", "")
            result["city"] = data.get("city", "")
            result["isp"] = data.get("org", "")

        # Clean up empty strings
        for key, value in result.items():
            if value is None:
                result[key] = ""
            else:
                result[key] = str(value).strip()

        return result

    def _is_private_ip(self, ip: str) -> bool:
        """
        Check if IP address is private/local.

        Args:
            ip: IP address to check

        Returns:
            True if IP is private/local
        """
        try:
            parts = ip.split(".")
            if len(parts) != 4:
                return True  # Invalid format, treat as private

            first = int(parts[0])
            second = int(parts[1])

            # Private IP ranges
            if first == 10:  # 10.0.0.0/8
                return True
            elif first == 172 and 16 <= second <= 31:  # 172.16.0.0/12
                return True
            elif first == 192 and second == 168:  # 192.168.0.0/16
                return True
            elif first == 127:  # 127.0.0.0/8 (localhost)
                return True
            elif ip == "::1":  # IPv6 localhost
                return True

            return False

        except (ValueError, IndexError):
            return True  # Invalid format, treat as private

    async def health_check(self) -> bool:
        """
        Check if geolocation service is available.

        Returns:
            True if at least one service is healthy
        """
        try:
            # Test with a known public IP (Google DNS)
            result = await self.get_location("8.8.8.8")
            return bool(result.get("country"))

        except Exception as e:
            self.logger.error("Geolocation health check failed", error=str(e))
            return False


# Global geolocation service instance
geolocation_service = GeolocationService()
