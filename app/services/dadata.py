"""
DaData API service for address cleaning and validation.
"""

import asyncio
import json
import os
from typing import Optional, Dict, Any
import aiohttp
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger, safe_log_data


def load_cache(cache_file: str) -> Dict[str, Any]:
    """Load cache from JSON file."""
    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.error("Error reading cache file", cache_file=cache_file, error=str(e))
    return {}


def save_cache(cache_file: str, cache: Dict[str, Any]) -> None:
    """Save cache to JSON file."""
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except IOError as e:
        logger.error("Error writing to cache file", cache_file=cache_file, error=str(e))


class DaDataService:
    """Asynchronous DaData API client."""

    def __init__(self, logger_instance: FilteringBoundLogger = logger):
        self.logger = logger_instance
        self.base_url = "https://cleaner.dadata.ru/api/v1/clean"
        self.session: Optional[aiohttp.ClientSession] = None

        # Validate configuration
        if not settings.dadata_token or not settings.dadata_secret:
            self.logger.warning("DaData credentials not configured")

    async def initialize(self):
        """Initialize the DaData service."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Token {settings.dadata_token}",
                    "X-Secret": settings.dadata_secret,
                },
            )
            self.logger.info("DaData service initialized")

    async def close(self):
        """Close the DaData service."""
        if self.session:
            await self.session.close()
            self.session = None

    async def clean_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Clean and validate address using DaData API.

        Args:
            address: Raw address string

        Returns:
            Cleaned address data or None if failed
        """
        if not settings.dadata_token or not settings.dadata_secret:
            self.logger.error("DaData credentials not configured")
            return None

        try:
            await self.initialize()

            if not self.session:
                self.logger.error("DaData session not initialized")
                return None

            payload = [address]

            async with self.session.post(
                f"{self.base_url}/address", json=payload
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    if data and len(data) > 0:
                        result = data[0]

                        self.logger.info(
                            "DaData address cleaned successfully",
                            **safe_log_data(
                                {
                                    "source": result.get("source", "")[:50],
                                    "result": result.get("result", "")[:50],
                                }
                            ),
                        )

                        return result
                    else:
                        self.logger.warning(
                            "DaData returned empty result", address=address[:50]
                        )
                        return None

                elif response.status == 429:
                    self.logger.warning("DaData rate limit exceeded")
                    return None

                elif response.status == 401:
                    self.logger.error("DaData authentication failed")
                    return None

                else:
                    error_text = await response.text()
                    self.logger.error(
                        "DaData API error",
                        status=response.status,
                        error=error_text[:200],
                    )
                    return None

        except asyncio.TimeoutError:
            self.logger.error("DaData request timeout", address=address[:50])
            return None

        except aiohttp.ClientError as e:
            self.logger.error("DaData client error", error=str(e), address=address[:50])
            return None

        except Exception as e:
            self.logger.error(
                "DaData unexpected error", error=str(e), address=address[:50]
            )
            return None

    async def get_street_fias_id(self, address: str) -> Optional[str]:
        """
        Get street FIAS ID for address.

        Args:
            address: Raw address string

        Returns:
            Street FIAS ID or None if not found
        """
        cache_file = "address_cache.json"
        cache = load_cache(cache_file)

        if address in cache:
            self.logger.info("Cache hit for address", address=address[:50])
            return cache[address]

        result = await self.clean_address(address)

        if result and "street_fias_id" in result:
            street_fias_id = result["street_fias_id"]
            cache[address] = street_fias_id
            save_cache(cache_file, cache)
            self.logger.info(
                "Address cached",
                source=result.get("source", "")[:50],
                street_fias_id=str(street_fias_id),
            )
            return street_fias_id

        return None

    async def get_full_result(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get full cleaning result for address.

        Args:
            address: Raw address string

        Returns:
            Full result dictionary or None if failed
        """
        return await self.clean_address(address)

    async def get_cleaned_address_text(self, address: str) -> Optional[str]:
        """
        Get cleaned address text from DaData API.

        Args:
            address: Raw address string

        Returns:
            Cleaned address text or None if failed
        """
        cache_file = "fulladdress_cache.json"
        cache = load_cache(cache_file)

        if address in cache:
            self.logger.info("Cache hit for full address", address=address[:50])
            return cache[address]

        result = await self.clean_address(address)

        if result and "result" in result:
            cleaned_address = result["result"]
            cache[address] = cleaned_address
            save_cache(cache_file, cache)
            self.logger.info(
                "Full address cached",
                source=result.get("source", "")[:50],
                result=cleaned_address[:50],
            )
            return cleaned_address

        return None

    async def health_check(self) -> bool:
        """
        Check if DaData service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            # Try to clean a simple test address
            test_result = await self.clean_address("Москва")
            return test_result is not None

        except Exception as e:
            self.logger.error("DaData health check failed", error=str(e))
            return False


# Global DaData service instance
dadata_service = DaDataService()
