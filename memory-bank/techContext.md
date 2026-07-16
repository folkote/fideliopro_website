# Tech Context

## Stack and Dependencies
- Runtime: Python FastAPI application.
- HTTP client: `aiohttp` for DaData and external geolocation calls.
- Database: PostgreSQL via SQLAlchemy async engine and JSONB cache entries.
- Rate limiting: SlowAPI middleware when enabled.
- Static serving: FastAPI `FileResponse` and `HTMLResponse`.

## Configuration
- `DADATA_TOKEN`: DaData API token; required for successful address cleaning.
- `DADATA_SECRET`: DaData API secret; required for successful address cleaning.
- `DATABASE_URL`: required when `CACHE_ENABLED=true` because cache backend is PostgreSQL-only.
- `CACHE_SCHEMA`: PostgreSQL schema for cache entries; default is `fideliopro_website`.
- `CACHE_ENABLED`: enables or disables cache behavior; default is `true`.
- `RATE_LIMIT_ENABLED`: enables SlowAPI middleware; default is `true`.

## Build and Test
- Compile validation has previously used `python -m compileall -q app scripts run.py`.
- Docker validation is preferred for deployment parity because the container target is Python 3.11 and host Python dependency installation may be constrained.
- PostgreSQL cache import validation uses [`scripts/import_file_cache_to_postgres.py`](../scripts/import_file_cache_to_postgres.py).

## SLAs and Budgets
- Metrics endpoint cache checks should remain bounded by short timeouts.
- DaData health checks should avoid repeated paid upstream calls through memoization.
