"""
DaData API service for address cleaning and validation.
"""

import asyncio
import hashlib
import json
import re
import time
from typing import Any, Dict, Optional, Tuple

import aiohttp
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger, safe_log_data
from .cache import cache_service


DADATA_STREET_FIAS_NAMESPACE = "dadata_street_fias"
DADATA_CLEANED_ADDRESS_NAMESPACE = "dadata_cleaned_address"
DADATA_CLEAN_ADDRESS_FULL_NAMESPACE = "dadata_clean_address_full_v1"
DADATA_SUGGEST_ADDRESS_NAMESPACE = "dadata_suggest_address"
LEADING_RUSSIAN_POSTAL_CODE_RE = re.compile(r"^\s*\d{6}\s*[,;\-–—:]?\s+(?=\S)")


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
        envelope = await self.get_clean_address_cached(address)
        if not envelope:
            return None

        street_fias_id = envelope.get("derived", {}).get("street_fias_id")
        return str(street_fias_id) if street_fias_id is not None else None

    async def get_full_result(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get full cleaning result for address.

        Args:
            address: Raw address string

        Returns:
            Full result dictionary or None if failed
        """
        envelope = await self.get_clean_address_cached(address)
        if not envelope:
            return None

        response = envelope.get("response", {})
        body = response.get("body") if isinstance(response, dict) else None
        return body if isinstance(body, dict) else None

    async def get_cleaned_address_text(self, address: str) -> Optional[str]:
        """
        Get cleaned address text from DaData API.

        Args:
            address: Raw address string

        Returns:
            Cleaned address text or None if failed
        """
        envelope = await self.get_clean_address_cached(address)
        if not envelope:
            return None

        cleaned_address = envelope.get("derived", {}).get("result")
        return str(cleaned_address) if cleaned_address is not None else None

    async def get_clean_address_cached(self, address: str) -> Optional[Dict[str, Any]]:
        """Return a versioned full DaData Cleaner envelope from cache or upstream.

        Usage:
            Minimal initialization::

                await dadata_service.initialize()

            Minimal happy-path call::

                envelope = await dadata_service.get_clean_address_cached("Москва")
                cleaned_text = envelope["derived"]["result"] if envelope else None

            Common error-handling case::

                if envelope is None:
                    logger.warning("DaData Cleaner result unavailable")

        No new external API usage was introduced for this method. It adapts the
        existing aiohttp-based ``clean_address`` call and the existing
        PostgreSQL JSONB ``cache_service`` contract, while replacing the retired
        derived-string runtime namespaces with one full-response namespace.
        """
        canonical_address = self._canonicalize_clean_address(address)
        cache_key = self._clean_address_cache_key(canonical_address)

        cached_envelope = await cache_service.get(
            cache_key,
            namespace=DADATA_CLEAN_ADDRESS_FULL_NAMESPACE,
        )

        if self._is_valid_clean_address_envelope(cached_envelope):
            self.logger.info(
                "Cache hit for DaData Cleaner address",
                address=canonical_address[:50],
            )
            return cached_envelope

        result = await self.clean_address(canonical_address)
        if not result:
            return None

        envelope = self._build_clean_address_envelope(
            canonical_address=canonical_address,
            cache_key=cache_key,
            result=result,
        )
        await cache_service.set(
            cache_key,
            envelope,
            namespace=DADATA_CLEAN_ADDRESS_FULL_NAMESPACE,
            source="dadata-clean-address-full",
        )
        self.logger.info(
            "DaData Cleaner full response cached",
            source=str(result.get("source", ""))[:50],
            result=str(result.get("result", ""))[:50],
        )
        return envelope

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
        normalized_payload = self._normalize_suggest_address_payload(payload)
        cache_key = self._suggest_address_cache_key(normalized_payload)
        cached_response = await cache_service.get(
            cache_key,
            namespace=DADATA_SUGGEST_ADDRESS_NAMESPACE,
        )

        if cached_response is not None:
            self.logger.info(
                "Cache hit for DaData address suggestions",
                query=str(normalized_payload.get("query", ""))[:50],
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
                json=normalized_payload,
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
                        query=str(normalized_payload.get("query", ""))[:50],
                        suggestions_count=len(response_payload.get("suggestions", [])),
                    )
                else:
                    self.logger.warning(
                        "DaData suggestions API returned non-200 status",
                        status=response.status,
                        query=str(normalized_payload.get("query", ""))[:50],
                    )

                return response.status, response_payload

        except asyncio.TimeoutError:
            self.logger.error(
                "DaData suggestions request timeout",
                query=str(normalized_payload.get("query", ""))[:50],
            )
            return 504, {"detail": "DaData request timeout"}

        except aiohttp.ClientError as e:
            self.logger.error(
                "DaData suggestions client error",
                error=str(e),
                query=str(normalized_payload.get("query", ""))[:50],
            )
            return 502, {"detail": "DaData client error"}

        except Exception as e:
            self.logger.error(
                "DaData suggestions unexpected error",
                error=str(e),
                query=str(normalized_payload.get("query", ""))[:50],
            )
            return 500, {"detail": "DaData suggestions request failed"}

    def _normalize_suggest_address_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return a DaData suggestions payload with a safe query normalization.

        A leading Russian six-digit postal code often makes interactive address
        suggestions worse, while DaData still supports a postal-code-only query.
        Therefore only strip the leading index when the remaining query contains
        non-empty address text. The successful response is still returned exactly
        as DaData sends it for the normalized query.
        """
        normalized_payload = dict(payload)
        query = normalized_payload.get("query")
        if isinstance(query, str):
            normalized_payload["query"] = self._strip_leading_postal_code(query)
        return normalized_payload

    def _strip_leading_postal_code(self, query: str) -> str:
        stripped_query = query.strip()
        normalized_query = LEADING_RUSSIAN_POSTAL_CODE_RE.sub("", stripped_query, count=1).strip()
        return normalized_query or stripped_query

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

    def _canonicalize_clean_address(self, address: str) -> str:
        return address.strip()

    def _clean_address_cache_key(self, canonical_address: str) -> str:
        address_hash = hashlib.sha256(canonical_address.encode("utf-8")).hexdigest()
        return f"sha256:v1:cleaner_address:{address_hash}"

    def _build_clean_address_envelope(
        self,
        canonical_address: str,
        cache_key: str,
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        derived: Dict[str, Any] = {
            "result": result.get("result"),
            "street_fias_id": result.get("street_fias_id"),
            "fias_id": result.get("fias_id"),
            "unrestricted_value": result.get("unrestricted_value"),
        }
        for quality_field in (
            "qc",
            "qc_complete",
            "qc_geo",
            "qc_house",
            "qc_name",
            "qc_conflict",
        ):
            if quality_field in result:
                derived[quality_field] = result.get(quality_field)

        return {
            "schema_version": 1,
            "provider": "dadata",
            "api": "cleaner.address",
            "request": {
                "canonical_address": canonical_address,
                "cache_key_algorithm": "sha256:v1:cleaner_address:utf8_trim",
                "cache_key": cache_key,
            },
            "response": {
                "status_code": 200,
                "body": result,
            },
            "derived": derived,
        }

    def _is_valid_clean_address_envelope(self, value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        if value.get("schema_version") != 1:
            return False
        if value.get("provider") != "dadata" or value.get("api") != "cleaner.address":
            return False
        response = value.get("response")
        if not isinstance(response, dict) or response.get("status_code") != 200:
            return False
        return isinstance(response.get("body"), dict)

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
