"""
Caching service for FidelioPro FastAPI application.
"""

import json
import re
from typing import Optional, Any
from pathlib import Path
from datetime import datetime, timedelta, timezone

import aiofiles
from psycopg_pool import AsyncConnectionPool
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger


class CacheService:
    """Unified caching service supporting PostgreSQL, Redis and file backends."""

    def __init__(self, logger_instance: FilteringBoundLogger = logger):
        self.logger = logger_instance
        self.redis_client: Optional[Any] = None
        self._redis_connected = False
        self.pool: Optional[AsyncConnectionPool] = None
        self._postgres_connected = False

        # Ensure cache directory exists for file cache
        if settings.cache_type == "file":
            cache_dir = Path(settings.cache_dir)
            cache_dir.mkdir(exist_ok=True)

    async def initialize(self):
        """Initialize the cache service."""
        if settings.cache_type == "postgres":
            await self._initialize_postgres()
        elif settings.cache_type == "redis" and settings.redis_url:
            try:
                import redis.asyncio as aioredis
                self.redis_client = aioredis.from_url(
                    settings.redis_url, encoding="utf-8", decode_responses=True
                )
                await self.redis_client.ping()
                self._redis_connected = True
                self.logger.info("Redis cache initialized successfully")
            except Exception as e:
                self.logger.error("Failed to connect to Redis", error=str(e))
                self._redis_connected = False

    async def _initialize_postgres(self):
        """Initialize PostgreSQL cache backend using psycopg connection pool."""
        if not settings.database_url:
            self.logger.error(
                "DATABASE_URL is not configured for postgres cache backend"
            )
            self._postgres_connected = False
            return

        try:
            self._validate_identifier(settings.cache_db_schema, "cache_db_schema")
            self._validate_identifier(settings.cache_db_table, "cache_db_table")

            # Build a standard PostgreSQL DSN from DATABASE_URL
            # Strip SQLAlchemy driver prefixes if present
            conninfo = settings.database_url
            for prefix in ("postgresql+psycopg_async://", "postgresql+psycopg://"):
                if conninfo.startswith(prefix):
                    conninfo = "postgresql://" + conninfo[len(prefix):]
                    break

            self.pool = AsyncConnectionPool(
                conninfo,
                min_size=1,
                max_size=5,
                open=False,
            )
            await self.pool.open()
            await self.pool.wait()

            await self._create_postgres_cache_table()
            self._postgres_connected = True
            self.logger.info(
                "PostgreSQL cache initialized successfully",
                schema=settings.cache_db_schema,
                table=settings.cache_db_table,
            )
        except Exception as e:
            self.logger.error("Failed to initialize PostgreSQL cache", error=str(e))
            self._postgres_connected = False

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not settings.cache_enabled:
            return None

        try:
            if settings.cache_type == "postgres":
                if not self._postgres_connected:
                    return None
                return await self._get_from_postgres(key)
            if settings.cache_type == "redis":
                if not (self._redis_connected and self.redis_client):
                    return None
                return await self._get_from_redis(key)
            return await self._get_from_file(key)
        except Exception as e:
            self.logger.error("Cache get error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not settings.cache_enabled:
            return False

        try:
            if settings.cache_type == "postgres":
                if not self._postgres_connected:
                    return False
                return await self._set_to_postgres(key, value, ttl)
            if settings.cache_type == "redis":
                if not (self._redis_connected and self.redis_client):
                    return False
                return await self._set_to_redis(key, value, ttl)
            return await self._set_to_file(key, value, ttl)
        except Exception as e:
            self.logger.error("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not settings.cache_enabled:
            return False

        try:
            if settings.cache_type == "postgres":
                if not self._postgres_connected:
                    return False
                return await self._delete_from_postgres(key)
            if settings.cache_type == "redis":
                if not (self._redis_connected and self.redis_client):
                    return False
                return await self._delete_from_redis(key)
            return await self._delete_from_file(key)
        except Exception as e:
            self.logger.error("Cache delete error", key=key, error=str(e))
            return False

    async def health_check(self) -> bool:
        """Check active cache backend health."""
        if not settings.cache_enabled:
            return True
        if settings.cache_type == "postgres":
            if not self._postgres_connected:
                return False
            return await self._postgres_ping()
        if settings.cache_type == "redis":
            if not (self._redis_connected and self.redis_client):
                return False
            try:
                await self.redis_client.ping()
                return True
            except Exception:
                return False
        return True

    @staticmethod
    def _validate_identifier(value: str, field_name: str) -> str:
        """Validate SQL identifier to avoid SQL injection in schema/table names."""
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError(
                f"Invalid {field_name}: '{value}'. Use only letters, numbers and underscores."
            )
        return value

    def _cache_table_ref(self) -> str:
        """Get quoted schema-qualified table name."""
        return f'"{settings.cache_db_schema}"."{settings.cache_db_table}"'

    async def _create_postgres_cache_table(self):
        """Create cache schema and table if they do not exist."""
        if not self.pool:
            raise RuntimeError("PostgreSQL pool is not initialized")

        async with self.pool.connection() as conn:
            await conn.execute(
                f'CREATE SCHEMA IF NOT EXISTS "{settings.cache_db_schema}"'
            )
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._cache_table_ref()} (
                    cache_key   TEXT PRIMARY KEY,
                    cache_value JSONB NOT NULL,
                    expires_at  TIMESTAMPTZ NULL,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS "{settings.cache_db_table}_expires_at_idx"
                ON {self._cache_table_ref()} (expires_at)
                """
            )

    async def _postgres_ping(self) -> bool:
        """Verify PostgreSQL connectivity."""
        if not self.pool:
            return False
        try:
            async with self.pool.connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error("PostgreSQL cache ping failed", error=str(e))
            return False

    async def _get_from_postgres(self, key: str) -> Optional[Any]:
        """Get value from PostgreSQL cache."""
        if not self.pool:
            return None

        try:
            async with self.pool.connection() as conn:
                cur = await conn.execute(
                    f"""
                    SELECT cache_value, expires_at
                    FROM {self._cache_table_ref()}
                    WHERE cache_key = %s
                    """,
                    (key,),
                )
                row = await cur.fetchone()
                if not row:
                    return None

                cache_value, expires_at = row

                if expires_at:
                    now_utc = datetime.now(timezone.utc)
                    if expires_at.tzinfo is None:
                        expires_at = expires_at.replace(tzinfo=timezone.utc)
                    if now_utc > expires_at:
                        await self._delete_from_postgres(key)
                        return None

                return cache_value
        except Exception as e:
            self.logger.error("PostgreSQL cache get error", key=key, error=str(e))
            return None

    async def _set_to_postgres(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value to PostgreSQL cache."""
        if not self.pool:
            return False

        expires_at = None
        if ttl:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            serialized_value = json.dumps(str(value), ensure_ascii=False)

        try:
            async with self.pool.connection() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self._cache_table_ref()}
                        (cache_key, cache_value, expires_at, created_at, updated_at)
                    VALUES
                        (%s, %s::jsonb, %s, NOW(), NOW())
                    ON CONFLICT (cache_key) DO UPDATE SET
                        cache_value = EXCLUDED.cache_value,
                        expires_at  = EXCLUDED.expires_at,
                        updated_at  = NOW()
                    """,
                    (key, serialized_value, expires_at),
                )
            return True
        except Exception as e:
            self.logger.error("PostgreSQL cache set error", key=key, error=str(e))
            return False

    async def _delete_from_postgres(self, key: str) -> bool:
        """Delete value from PostgreSQL cache."""
        if not self.pool:
            return False

        try:
            async with self.pool.connection() as conn:
                cur = await conn.execute(
                    f"DELETE FROM {self._cache_table_ref()} WHERE cache_key = %s",
                    (key,),
                )
                return cur.rowcount > 0
        except Exception as e:
            self.logger.error("PostgreSQL cache delete error", key=key, error=str(e))
            return False

    # ── Redis backend ──────────────────────────────────────────────────────────

    async def _get_from_redis(self, key: str) -> Optional[Any]:
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
        if not self.redis_client:
            return False
        result = await self.redis_client.delete(key)
        return result > 0

    # ── File backend ───────────────────────────────────────────────────────────

    async def _get_from_file(self, key: str) -> Optional[Any]:
        cache_file = Path(settings.cache_dir) / f"{key}.json"
        if not cache_file.exists():
            return None
        try:
            async with aiofiles.open(cache_file, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                if "expires_at" in data:
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    if datetime.now() > expires_at:
                        await self._delete_from_file(key)
                        return None
                return data.get("value")
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.warning("Cache file read error", key=key, error=str(e))
            return None

    async def _set_to_file(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        cache_file = Path(settings.cache_dir) / f"{key}.json"
        data = {"value": value, "created_at": datetime.now().isoformat()}
        if ttl:
            data["expires_at"] = (datetime.now() + timedelta(seconds=ttl)).isoformat()
        try:
            async with aiofiles.open(cache_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            return True
        except Exception as e:
            self.logger.error("Cache file write error", key=key, error=str(e))
            return False

    async def _delete_from_file(self, key: str) -> bool:
        cache_file = Path(settings.cache_dir) / f"{key}.json"
        try:
            if cache_file.exists():
                cache_file.unlink()
            return True
        except Exception as e:
            self.logger.error("Cache file delete error", key=key, error=str(e))
            return False

    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()
        if self.pool:
            await self.pool.close()


# Global cache instance
cache_service = CacheService()
