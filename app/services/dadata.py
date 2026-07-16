"""
DaData API service for address cleaning and validation.
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple

import aiohttp
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger, safe_log_data
from .cache import cache_service


DADATA_STREET_FIAS_NAMESPACE = "dadata_street_fias"
DADATA_CLEANED_ADDRESS_NAMESPACE = "dadata_cleaned_address"
DADATA_SUGGEST_ADDRESS_NAMESPACE = "dadata_suggest_address"


class DaDataService:
    """Asynchronous DaData API client."""

    def __init__(self, logger_instance: FilteringBoundLogger = logger):
        self.logger = logger_instance
        self.base_url = "https://cleaner.dadata.ru/api/v1/clean"
        self.suggestions_base_url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
        self.session: Optional[aiohttp.ClientSession] = None
        self._health_check_cache: Optional[bool] = None
        self._health_check_timestamp: float = 0.0

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
        cached_fias_id = await cache_service.get(
            address,
            namespace=DADATA_STREET_FIAS_NAMESPACE,
        )

        if cached_fias_id is not None:
            self.logger.info("Cache hit for address", address=address[:50])
            return str(cached_fias_id)

        result = await self.clean_address(address)

        if result and "street_fias_id" in result:
            street_fias_id = result["street_fias_id"]
            await cache_service.set(
                address,
                street_fias_id,
                namespace=DADATA_STREET_FIAS_NAMESPACE,
                source="dadata-clean-address",
            )
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
        cached_cleaned_address = await cache_service.get(
            address,
            namespace=DADATA_CLEANED_ADDRESS_NAMESPACE,
        )

        if cached_cleaned_address is not None:
            self.logger.info("Cache hit for full address", address=address[:50])
            return str(cached_cleaned_address)

        result = await self.clean_address(address)

        if result and "result" in result:
            cleaned_address = result["result"]
            await cache_service.set(
                address,
                cleaned_address,
                namespace=DADATA_CLEANED_ADDRESS_NAMESPACE,
                source="dadata-clean-address",
            )
            self.logger.info(
                "Full address cached",
                source=result.get("source", "")[:50],
                result=cleaned_address[:50],
            )
            return cleaned_address

        return None

    async def suggest_address(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Return DaData address suggestions with PostgreSQL caching.

        Usage:
            Minimal initialization::

                await dadata_service.initialize()

            Minimal happy-path call::

                status_code, response = await dadata_service.suggest_address(
                    {"query": "москва хабар", "count": 10}
                )

            Common error-handling case::

                if status_code != 200:
                    logger.warning("DaData suggestions request failed", status=status_code)

        The request follows the DaData Suggestions address API contract described
        in README_dadata.md and the official HTTP example:
        POST /suggestions/api/4_1/rs/suggest/address with a JSON body.
        Successful HTTP 200 JSON responses are cached under a deterministic key
        derived from the complete incoming JSON body. Non-200 responses are not
        cached so transient upstream failures and rate limits do not become
        durable cache entries.
        """
        cache_key = self._suggest_address_cache_key(payload)
        cached_response = await cache_service.get(
            cache_key,
            namespace=DADATA_SUGGEST_ADDRESS_NAMESPACE,
        )

        if cached_response is not None:
            self.logger.info(
                "Cache hit for DaData address suggestions",
                query=str(payload.get("query", ""))[:50],
            )
            return 200, cached_response

        if not settings.dadata_token:
            self.logger.error("DaData token not configured")
            return 503, {"detail": "DaData credentials not configured"}

        try:
            await self.initialize()

            if not self.session:
                self.logger.error("DaData session not initialized")
                return 503, {"detail": "DaData session not initialized"}

            async with self.session.post(
                f"{self.suggestions_base_url}/suggest/address",
                json=payload,
            ) as response:
                response_payload = await self._read_json_response(response)

                if response.status == 200:
                    await cache_service.set(
                        cache_key,
                        response_payload,
                        namespace=DADATA_SUGGEST_ADDRESS_NAMESPACE,
                        source="dadata-suggest-address",
                    )
                    self.logger.info(
                        "DaData address suggestions cached",
                        query=str(payload.get("query", ""))[:50],
                        suggestions_count=len(response_payload.get("suggestions", [])),
                    )
                else:
                    self.logger.warning(
                        "DaData suggestions API returned non-200 status",
                        status=response.status,
                        query=str(payload.get("query", ""))[:50],
                    )

                return response.status, response_payload

        except asyncio.TimeoutError:
            self.logger.error(
                "DaData suggestions request timeout",
                query=str(payload.get("query", ""))[:50],
            )
            return 504, {"detail": "DaData request timeout"}

        except aiohttp.ClientError as e:
            self.logger.error(
                "DaData suggestions client error",
                error=str(e),
                query=str(payload.get("query", ""))[:50],
            )
            return 502, {"detail": "DaData client error"}

        except Exception as e:
            self.logger.error(
                "DaData suggestions unexpected error",
                error=str(e),
                query=str(payload.get("query", ""))[:50],
            )
            return 500, {"detail": "DaData suggestions request failed"}

    def _suggest_address_cache_key(self, payload: Dict[str, Any]) -> str:
        canonical_payload = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        payload_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
        return f"sha256:{payload_hash}"

    async def _read_json_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        try:
            data = await response.json(content_type=None)
            if isinstance(data, dict):
                return data
            return {"data": data}
        except Exception:
            response_text = await response.text()
            return {"detail": response_text}

    async def health_check(self) -> bool:
        """
        Check if DaData service is available.

        Uses an in-memory status memo for 5 minutes to avoid repeated API calls.
        Each health check call costs money, so we cache the result.

        Returns:
            True if service is healthy, False otherwise
        """
        current_time = time.time()
        if (
            self._health_check_cache is not None
            and (current_time - self._health_check_timestamp) < 300
        ):
            return self._health_check_cache

        try:
            # Try to clean a simple test address
            test_result = await self.clean_address("Москва")
            self._health_check_cache = test_result is not None
            self._health_check_timestamp = current_time
            return self._health_check_cache

        except Exception as e:
            self.logger.error("DaData health check failed", error=str(e))
            self._health_check_cache = False
            self._health_check_timestamp = current_time
            return False


# Global DaData service instance
dadata_service = DaDataService()
