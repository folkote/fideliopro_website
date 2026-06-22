import json
import re
from typing import Optional, Any, Dict

from sqlalchemy import Column, DateTime, MetaData, Table, Text, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from structlog.typing import FilteringBoundLogger

from ..config import settings
from ..utils.logger import logger


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class CacheService:
    """PostgreSQL-backed cache service.

    Usage:
        Minimal initialization::

            await cache_service.initialize()

        Minimal happy-path call::

            await cache_service.set("8.8.8.8", {"country": "United States"}, namespace="geolocation")
            value = await cache_service.get("8.8.8.8", namespace="geolocation")

        Common error-handling case::

            if not await cache_service.health_check():
                logger.error("PostgreSQL cache is unavailable")

    The implementation follows SQLAlchemy 2.0 async engine examples from
    Context7 documentation: `create_async_engine`, `engine.begin()`,
    `conn.execute(text(...))`, `async_sessionmaker.begin()`, and PostgreSQL
    `insert(...).on_conflict_do_update(...)`.
    """

    def __init__(self, logger_instance: FilteringBoundLogger = logger):
        self.logger = logger_instance
        self.schema = settings.cache_schema
        self.backend = "postgresql"
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        self.metadata = MetaData(schema=self.schema)
        self.cache_entries = Table(
            "cache_entries",
            self.metadata,
            Column("namespace", Text, primary_key=True, nullable=False),
            Column("cache_key", Text, primary_key=True, nullable=False),
            Column("value", JSONB, nullable=False),
            Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
            Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
            Column("source", Text, nullable=True),
        )

        if not _IDENTIFIER_RE.match(self.schema):
            raise ValueError(
                "CACHE_SCHEMA must be a valid PostgreSQL identifier "
                "(letters, numbers, underscores; cannot start with a number)"
            )

    async def initialize(self):
        """Initialize PostgreSQL engine and create cache schema/table/indexes."""
        if not settings.cache_enabled:
            self.logger.warning("Cache disabled by configuration")
            return

        if not settings.database_url:
            message = "DATABASE_URL is required for the PostgreSQL cache backend"
            self.logger.error(message)
            raise RuntimeError(message)

        if self.engine is None:
            self.engine = create_async_engine(settings.database_url, pool_pre_ping=True)
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

        try:
            async with self.engine.begin() as conn:
                await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))
                await conn.run_sync(self.metadata.create_all)
                await conn.execute(
                    text(
                        f'CREATE INDEX IF NOT EXISTS idx_cache_entries_namespace_updated_at '
                        f'ON "{self.schema}".cache_entries (namespace, updated_at DESC)'
                    )
                )
                await conn.execute(text("SELECT 1"))
            self.logger.info("PostgreSQL cache initialized successfully", schema=self.schema)
        except Exception as e:
            self.logger.error("Failed to initialize PostgreSQL cache", error=str(e), schema=self.schema)
            raise

    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            namespace: Cache namespace

        Returns:
            Cached value or None if not found
        """
        if not settings.cache_enabled:
            return None

        try:
            self._ensure_initialized()
            stmt = select(self.cache_entries.c.value).where(
                self.cache_entries.c.namespace == namespace,
                self.cache_entries.c.cache_key == key,
            )
            async with self.session_factory() as session:  # type: ignore[union-attr]
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error("Cache get error", key=key, namespace=namespace, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default",
        source: Optional[str] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Deprecated compatibility argument. Ignored; PostgreSQL cache has no TTL.
            namespace: Cache namespace
            source: Optional source label for imports or upstream service names

        Returns:
            True if successful, False otherwise
        """
        if not settings.cache_enabled:
            return False

        try:
            self._ensure_initialized()
            json_value = self._json_safe(value)
            stmt = insert(self.cache_entries).values(
                namespace=namespace,
                cache_key=key,
                value=json_value,
                source=source,
            )
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=[self.cache_entries.c.namespace, self.cache_entries.c.cache_key],
                set_={
                    "value": stmt.excluded.value,
                    "updated_at": func.now(),
                    "source": stmt.excluded.source,
                },
            )
            async with self.session_factory.begin() as session:  # type: ignore[union-attr]
                await session.execute(upsert_stmt)
            if ttl is not None:
                self.logger.debug("Ignoring deprecated cache ttl", key=key, namespace=namespace)
            return True
        except Exception as e:
            self.logger.error("Cache set error", key=key, namespace=namespace, error=str(e))
            return False

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key
            namespace: Cache namespace

        Returns:
            True if successful, False otherwise
        """
        if not settings.cache_enabled:
            return False

        try:
            self._ensure_initialized()
            async with self.session_factory.begin() as session:  # type: ignore[union-attr]
                result = await session.execute(
                    self.cache_entries.delete().where(
                        self.cache_entries.c.namespace == namespace,
                        self.cache_entries.c.cache_key == key,
                    )
                )
            return result.rowcount > 0
        except Exception as e:
            self.logger.error("Cache delete error", key=key, namespace=namespace, error=str(e))
            return False

    async def health_check(self) -> bool:
        """Return True when the PostgreSQL cache backend is reachable."""
        try:
            self._ensure_initialized()
            async with self.engine.connect() as conn:  # type: ignore[union-attr]
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            self.logger.error("PostgreSQL cache health check failed", error=str(e), schema=self.schema)
            return False

    async def namespace_counts(self) -> Dict[str, int]:
        """Return cache row counts grouped by namespace."""
        if not settings.cache_enabled:
            return {}
        try:
            self._ensure_initialized()
            stmt = (
                select(self.cache_entries.c.namespace, func.count().label("count"))
                .group_by(self.cache_entries.c.namespace)
                .order_by(self.cache_entries.c.namespace)
            )
            async with self.session_factory() as session:  # type: ignore[union-attr]
                result = await session.execute(stmt)
                return {row.namespace: int(row.count) for row in result}
        except Exception as e:
            self.logger.error("Cache namespace counts error", error=str(e), schema=self.schema)
            return {}

    def _ensure_initialized(self) -> None:
        if self.engine is None or self.session_factory is None:
            raise RuntimeError("CacheService is not initialized")

    def _json_safe(self, value: Any) -> Any:
        """Convert arbitrary Python values into JSONB-compatible data."""
        try:
            return json.loads(json.dumps(value, ensure_ascii=False, default=str))
        except (TypeError, ValueError):
            return str(value)

    async def close(self):
        """Close PostgreSQL engine connections."""
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None


# Global cache instance
cache_service = CacheService()
