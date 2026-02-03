"""
Caching service for FidelioPro FastAPI application.
Supports file-based cache with JSON and JSONL formats.
"""

import json
import os
import asyncio
from typing import Optional, Any, Dict
from pathlib import Path
from datetime import datetime, timedelta

import aiofiles
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger, safe_log_data


class CacheService:
    """Unified caching service supporting both file and Redis backends."""

    def __init__(self, logger_instance: FilteringBoundLogger = logger):
        self.logger = logger_instance
        self.redis_client: Optional[Any] = None
        self._redis_connected = False

        # Ensure cache directory exists for file cache
        if settings.cache_type == "file":
            cache_dir = Path(settings.cache_dir)
            cache_dir.mkdir(exist_ok=True)

    async def initialize(self):
        """Initialize the cache service."""
        if settings.cache_type == "redis" and settings.redis_url:
            try:
                import redis.asyncio as aioredis
                self.redis_client = aioredis.from_url(
                    settings.redis_url, encoding="utf-8", decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
                self._redis_connected = True
                self.logger.info("Redis cache initialized successfully")
            except Exception as e:
                self.logger.error("Failed to connect to Redis", error=str(e))
                self._redis_connected = False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not settings.cache_enabled:
            return None

        try:
            if self._redis_connected and self.redis_client:
                return await self._get_from_redis(key)
            else:
                return await self._get_from_file(key)
        except Exception as e:
            self.logger.error("Cache get error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not settings.cache_enabled:
            return False

        try:
            if self._redis_connected and self.redis_client:
                return await self._set_to_redis(key, value, ttl)
            else:
                return await self._set_to_file(key, value, ttl)
        except Exception as e:
            self.logger.error("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not settings.cache_enabled:
            return False

        try:
            if self._redis_connected and self.redis_client:
                return await self._delete_from_redis(key)
            else:
                return await self._delete_from_file(key)
        except Exception as e:
            self.logger.error("Cache delete error", key=key, error=str(e))
            return False

    async def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None

        value = await self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def _set_to_redis(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value to Redis cache."""
        if not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            serialized_value = str(value)

        if ttl:
            await self.redis_client.setex(key, ttl, serialized_value)
        else:
            await self.redis_client.set(key, serialized_value)
        return True

    async def _delete_from_redis(self, key: str) -> bool:
        """Delete value from Redis cache."""
        if not self.redis_client:
            return False

        result = await self.redis_client.delete(key)
        return result > 0

    async def _get_from_file(self, key: str) -> Optional[Any]:
        """Get value from file cache.
        
        Supports both JSON (individual files) and JSONL (geolocation cache).
        """
        # Check if this is a geolocation key (format: geolocation_<ip>)
        if key.startswith("geolocation_"):
            return await self._get_from_jsonl(key)
        
        # Standard JSON file cache
        cache_file = Path(settings.cache_dir) / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)

                # Check TTL
                if "expires_at" in data:
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    if datetime.now() > expires_at:
                        # Cache expired, delete file
                        await self._delete_from_file(key)
                        return None

                return data.get("value")
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.warning("Cache file read error", key=key, error=str(e))
            return None

    async def _set_to_file(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value to file cache.
        
        Supports both JSON (individual files) and JSONL (geolocation cache).
        """
        # Check if this is a geolocation key (format: geolocation_<ip>)
        if key.startswith("geolocation_"):
            return await self._set_to_jsonl(key, value, ttl)
        
        # Standard JSON file cache
        cache_file = Path(settings.cache_dir) / f"{key}.json"

        data = {"value": value, "created_at": datetime.now().isoformat()}

        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            data["expires_at"] = expires_at.isoformat()

        try:
            async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            self.logger.error("Cache file write error", key=key, error=str(e))
            return False

    async def _delete_from_file(self, key: str) -> bool:
        """Delete value from file cache."""
        # Geolocation entries are stored in JSONL, not individual files
        if key.startswith("geolocation_"):
            return await self._delete_from_jsonl(key)
        
        cache_file = Path(settings.cache_dir) / f"{key}.json"

        try:
            if cache_file.exists():
                cache_file.unlink()
            return True
        except Exception as e:
            self.logger.error("Cache file delete error", key=key, error=str(e))
            return False

    async def _get_from_jsonl(self, key: str) -> Optional[Any]:
        """Get value from JSONL geolocation cache."""
        jsonl_file = Path(settings.cache_dir) / "geolocation_cache.jsonl"
        
        if not jsonl_file.exists():
            return None
        
        try:
            async with aiofiles.open(jsonl_file, "r", encoding="utf-8") as f:
                async for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("key") == key:
                            # Check TTL
                            if "expires_at" in entry:
                                expires_at = datetime.fromisoformat(entry["expires_at"])
                                if datetime.now() > expires_at:
                                    # Entry expired, skip it
                                    continue
                            return entry.get("value")
                    except json.JSONDecodeError:
                        continue
            return None
        except Exception as e:
            self.logger.warning("JSONL cache read error", key=key, error=str(e))
            return None

    async def _set_to_jsonl(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value to JSONL geolocation cache."""
        jsonl_file = Path(settings.cache_dir) / "geolocation_cache.jsonl"
        
        entry = {
            "key": key,
            "value": value,
            "created_at": datetime.now().isoformat()
        }
        
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
            entry["expires_at"] = expires_at.isoformat()
        
        try:
            # Append to JSONL file
            async with aiofiles.open(jsonl_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            self.logger.error("JSONL cache write error", key=key, error=str(e))
            return False

    async def _delete_from_jsonl(self, key: str) -> bool:
        """Delete value from JSONL geolocation cache by rewriting without the entry."""
        jsonl_file = Path(settings.cache_dir) / "geolocation_cache.jsonl"
        
        if not jsonl_file.exists():
            return True
        
        try:
            # Read all entries except the one to delete
            entries = []
            async with aiofiles.open(jsonl_file, "r", encoding="utf-8") as f:
                async for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("key") != key:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Rewrite file without the deleted entry
            async with aiofiles.open(jsonl_file, "w", encoding="utf-8") as f:
                for entry in entries:
                    await f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            self.logger.error("JSONL cache delete error", key=key, error=str(e))
            return False

    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()


# Global cache instance
cache_service = CacheService()
