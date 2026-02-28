# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run (development)
```bash
# Windows
start.bat

# Linux/macOS
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Run (production)
```bash
docker-compose up -d
```

### One-time JSON→PostgreSQL migration
```bash
python scripts/migrate_json_to_postgres.py
```

### Install dependencies
```bash
pip install -r requirements.txt
```

No linting, formatting, or test tooling is configured in this project.

## Architecture

### Request flow
Every API call goes through: `SlowAPIMiddleware` → `ErrorHandlingMiddleware` → `LoggingMiddleware` → `CORSMiddleware` → router handler → service layer.

The logging middleware performs async geolocation lookups on each request (fire-and-forget, 2s timeout) to enrich log lines with `IP (country/city)` data.

### Service layer (`app/services/`)

Three singleton services are initialized on startup via the `lifespan` context manager in `main.py` and shut down cleanly on exit:

- **`cache_service`** (`cache.py`) — unified cache with three backends selectable via `CACHE_TYPE`: `postgres` (default), `redis`, `file`. Wraps `AsyncConnectionPool` from `psycopg-pool`. On `postgres` mode, strips the `postgresql+psycopg://` prefix from `DATABASE_URL` to use a plain `postgresql://` DSN directly — bypassing SQLAlchemy, which has binary-mode incompatibility with PostgreSQL 18.
- **`dadata_service`** (`dadata.py`) — async HTTP client calling `https://cleaner.dadata.ru/api/v1/clean/address`. All calls are cache-first; results stored with no TTL (address data is stable).
- **`geolocation_service`** (`geolocation.py`) — queries `ip-api.com` with fallback to `ipapi.co`. Private IPs are detected and short-circuited. Results cached with `CACHE_TTL` (default 1h).

### Cache key conventions
| Data | Key format |
|------|-----------|
| Street FIAS ID | `dadata:street_fias_id:{address}` |
| Cleaned address text | `dadata:cleaned_text:{address}` |
| IP geolocation | `geolocation_{ip}` |

Note the inconsistency: dadata keys use colon separators, geolocation uses underscore — this is intentional (legacy compat).

### PostgreSQL schema
Database: `fidelio_address_api`, schema: `fideliopro`, table: `cache_entries`.

```sql
cache_key   TEXT PRIMARY KEY
cache_value JSONB NOT NULL
expires_at  TIMESTAMPTZ NULL   -- NULL = no expiry
created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### Static file serving
`app/routers/static_files.py` is registered last and acts as a catch-all. It routes by file extension: `.sql` files from `static/sql/`, everything else from `static/website/`. Path traversal (`../`) is blocked explicitly.

### Windows-specific note
`run.py` sets `asyncio.WindowsSelectorEventLoopPolicy()` on Windows because `psycopg3` requires `SelectorEventLoop` (the Windows default `ProactorEventLoop` is incompatible). This is a no-op on Linux/Docker.

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:port/db` |
| `CACHE_DB_SCHEMA` | PostgreSQL schema (default: `fideliopro`) |
| `CACHE_TYPE` | `postgres` / `redis` / `file` |
| `DADATA_TOKEN` / `DADATA_SECRET` | DaData API credentials |
| `DEBUG` | Enables `/docs`, `/redoc`, and uvicorn hot-reload |
| `RATE_LIMIT_ENABLED` | Toggle SlowAPI rate limiting |

`.env` is excluded from git — copy and fill in credentials manually.

## API endpoints

| Method | Path | Response | Description |
|--------|------|----------|-------------|
| GET | `/apiaddress/api?address=...` | `text/plain` | Street FIAS ID (UUID) |
| GET | `/apifulladdress/api?address=...` | `text/plain` | Normalized address string |
| GET | `/health` | HTML | Visual health dashboard |
| GET | `/health/json` | JSON | Machine-readable health check |
| GET | `/metrics` | JSON | Basic app metrics |
| GET | `/{path}` | file | Static files (HTML, CSS, JS, SQL, fonts) |
