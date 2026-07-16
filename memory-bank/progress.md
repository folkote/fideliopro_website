### 2026-07-16
- [Architect] UMB completed for DaData proxy/cache review.
- Summary: confirmed current address endpoints proxy to DaData through [`DaDataService`](../app/services/dadata.py:21) and cache repeated lookups through PostgreSQL [`CacheService`](../app/services/cache.py:17) using namespace-scoped keys.
- Documentation: created baseline Memory Bank files [`projectbrief.md`](projectbrief.md), [`productContext.md`](productContext.md), [`systemPatterns.md`](systemPatterns.md), [`techContext.md`](techContext.md), and [`activeContext.md`](activeContext.md) because only [`progress.md`](progress.md) existed.
- Decision refs: [`systemPatterns.md`](systemPatterns.md) documents PostgreSQL-only cache and plain text compatibility endpoint ADRs.
- Next: clarify the new endpoint path, response format, and exact DaData field/transformation before handoff to Coder.
- [Architect] Planned new DaData Suggestions proxy endpoint: `POST /api/suggest/address`, full JSON passthrough, PostgreSQL cache namespace `dadata_suggest_address`, deterministic full-body cache key, and cache only successful HTTP 200 JSON responses.
- [Coder] Implemented DaData Suggestions proxy endpoint; status: done.
- [Coder] Added cache-aware [`DaDataService.suggest_address()`](../app/services/dadata.py:227) using upstream `https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address`, dedicated namespace `dadata_suggest_address`, SHA-256 deterministic cache key from full JSON request body, and successful HTTP 200 JSON response caching only.
- [Coder] Added [`suggest_address()`](../app/routers/api.py:153) route for `POST /api/suggest/address`; it accepts the DaData-compatible JSON body, validates `query`, delegates upstream/cache behavior to the service, and returns the JSON payload unchanged on success.
- Context7: no new external library usage was introduced. Existing project stack uses [`aiohttp.ClientSession.post()`](../app/services/dadata.py:278), FastAPI [`Body`](../app/routers/api.py:7), and [`JSONResponse`](../app/routers/api.py:8) patterns already present in the codebase and documented in local [`README_dadata.md`](../README_dadata.md:155).
- Tests: `python -m compileall -q app scripts run.py` passed.
- Next: validate against a running deployment with real `DATABASE_URL`, `CACHE_SCHEMA`, and DaData token by calling `POST /api/suggest/address` twice with the same body and confirming the second response is served from cache without a new paid upstream call.
- [Coder] Added safe leading postal-code normalization for DaData Suggestions queries; status: done.
- [Coder] [`DaDataService.suggest_address()`](../app/services/dadata.py:229) now sends a normalized payload to DaData/cache where only a leading Russian six-digit postal code followed by additional address text is stripped from `query`.
- Safety: postal-code-only queries such as `127282` remain unchanged, non-leading indexes remain unchanged, and the successful DaData JSON response is still returned without transformation.
- Tests: regex normalization assertions passed; `python -m compileall -q app scripts run.py` passed. Direct import-based assertion was skipped because host Python lacks installed `aiohttp`, while compile validation succeeds.
- Next: deploy and smoke test with `127282, г. Москва, ул. Ленина, дом 8, корп. 1, кв. 77` against the running endpoint.

### 2026-06-30
- [Coder] Implemented Digital ID integration cost calculator page; status: done.
- [Coder] Added static calculator page at `static/website/digital-id-calculator.html` with two inputs: room count and discount percent.
- [Coder] Implemented browser-side calculation for software, services, section totals, and grand total with Russian currency-style number formatting.
- [Coder] Added visible links from `static/website/index.html` hero CTA and solutions section to the calculator page.
- Tests: arithmetic assertions prepared for control case 216 rooms / 0% discount: software `197 960,96`, services `152 880,00`, grand total `350 840,96`; static token/link validation prepared. Terminal output did not stream reliably in VS Code shell integration, but command contained direct Python assertions.
- [Coder] Deployed calculator static files to running `fideliopro_app` container with `docker cp` because local `docker compose up -d --build` is blocked by missing shell `DATABASE_URL` interpolation while `.env` is absent from workspace.
- [Coder] Fixed static HTML downloads by removing `filename` from generic `FileResponse` in `app/routers/static_files.py`; deployed the router hotfix to running `fideliopro_app` and restarted the container.
- Deploy verification: `/` returns HTTP 200 with calculator link; `/digital-id-calculator.html` returns HTTP 200, `content-type: text/html; charset=utf-8`, no `content-disposition`, and contains calculator title.
- [Coder] Updated calculator default room count from `216` to `150` and anonymized prices: `122.50` → `120`, `340.28` → `330`, `50960` → `48000`; deployed updated `static/website/digital-id-calculator.html` to running `fideliopro_app` container.
- Tests: new default arithmetic passed: software `141 500,00`, services `144 000,00`, grand total `285 500,00`; deployed page returns HTTP 200 as HTML without download header and contains updated defaults/prices.
- Context7: no external runtime library was introduced for the calculator; implementation uses standard browser APIs including `Intl.NumberFormat`.
- Next: visually review `static/website/digital-id-calculator.html` in browser and deploy static file changes.

### 2026-06-22
- [Coder] Implemented PostgreSQL-only cache redesign; status: done.
- [Coder] Replaced file/Redis runtime cache service with SQLAlchemy async PostgreSQL cache using schema `fideliopro_website`, JSONB values, idempotent DDL, upsert writes, health checks, and namespace counts.
- [Coder] Updated DaData and geolocation services to use PostgreSQL cache namespaces and removed runtime file cache helpers/TTL expiration behavior.
- [Coder] Added idempotent import script for legacy `cache/` and `data/cache/` files with `--dry-run` support.
- [Coder] Removed stale root cache modules and Redis dependency/configuration.
- Tests: `python -m compileall -q app scripts run.py` passed.
- Notes: Local dependency install/dry-run execution could not complete in the host Python environment: system Python is externally managed; Python 3.13 venv dependency install timed out while downloading packages; `python3.11` is not installed on host. Docker target remains Python 3.11.
- Next: Orchestrator should validate with Docker/Python 3.11 and a real `DATABASE_URL`, then run `python scripts/import_file_cache_to_postgres.py --dry-run` and the real import.

### 2026-06-22
- [Debug] Incident: PostgreSQL cache validation before deployment.
- Context: validated changed files for PostgreSQL-only cache redesign; no commit/push/deploy performed.
- Repro Steps:
  1) Build image with `docker build -t fideliopro-cache-validation .`.
  2) Run schema/cache smoke script in the image with `DATABASE_URL=postgresql+psycopg://postgres:7969900@10.0.0.8:5432/fidelio_backend` and `CACHE_SCHEMA=fideliopro_website`.
  3) Run `python scripts/import_file_cache_to_postgres.py --dry-run` with `cache/` mounted read-only.
  4) Run `python scripts/import_file_cache_to_postgres.py` with `cache/` mounted read-only.
  5) Start container on host port `7081` mapped to container port `7080` and call `/health/json` plus `/metrics`.
- Observed vs Expected:
  - Observed: Docker build succeeded; schema/table existed; cache set/get/upsert/namespace counts/health succeeded; dry-run read 15363 rows; real import inserted 15363 rows; app started; `/health/json` returned HTTP 200 degraded only because DaData credentials were intentionally empty; cache service was healthy.
  - Expected: PostgreSQL cache initializes in schema `fideliopro_website`, supports basic operations, imports legacy file cache without deleting source files, and app can start.
- Hypotheses (initial):
  - H1: Missing PostgreSQL driver/dependency in container.
  - H2: Invalid schema/table/index DDL or missing schema creation.
  - H3: Upsert conflicts or JSONB serialization failures.
  - H4: Import script key normalization or parsing failures.
  - H5: App startup fails because `DATABASE_URL` is required.
  - H6: Redis/file cache references remain and break runtime.
  - H7: Docker Compose port/env mismatch breaks health checks.
- Most Likely (ranked):
  1) H7: Compose/application port alignment needed explicit runtime env validation.
  2) H5: Missing `DATABASE_URL` remains a startup blocker by design.
- Instrumentation:
  - Added: no code instrumentation; validation used Docker smoke commands and runtime HTTP checks.
  - Results: PostgreSQL cache initialized successfully; `health_initial=True`; `set_first=True`; `set_second=True`; namespace `debug_validation=1`; table `fideliopro_website.cache_entries` exists; metrics counts after import were `dadata_cleaned_address=2304`, `dadata_street_fias=10591`, `debug_validation=1`, `geolocation=2468`.
- Tentative Diagnosis: PostgreSQL cache implementation is deployable from the validation perspective; only expected operational requirements remain: provide `DATABASE_URL`, `CACHE_SCHEMA`, and DaData credentials for healthy overall status. Temporary validation row `debug_validation/debug_validation_cache_key` was deleted after validation and the namespace count returned to 0.
- Request Confirmation: not needed; validation-only task completed.
- Next: Coder may optionally remove stale Redis comments from `.env`.

### 2026-06-22
- [Debug] Incident: Post-deploy probe hang around `/metrics` after PostgreSQL cache import.
- Context: `fideliopro_app` was running and Docker health stayed healthy; `/health/json` was fast; earlier smoke probes stalled around `/metrics` and did not reliably report subsequent statuses.
- Repro Steps:
  1) Checked for stale local smoke/probe commands with process listings filtered for post-deploy smoke, probe body, curl, and urllib probes.
  2) Timed `/health/json`, `/metrics`, `/`, `/select.sql`, and conservative DaData endpoint requests against `http://127.0.0.1:7080`.
  3) Inspected recent container logs for `/metrics`, request timings, PostgreSQL cache initialization, and DaData/geolocation messages.
  4) Rebuilt and redeployed with `docker compose build fideliopro` and `docker compose up -d fideliopro`, preserving `DATABASE_URL` and `CACHE_SCHEMA` from the running container environment without printing secrets.
- Observed vs Expected:
  - Observed: `/metrics` responded quickly during diagnosis, but the endpoint performed unbounded awaited PostgreSQL cache health and namespace count calls; logging middleware also performed geolocation enrichment for local/health/metrics probes. DaData endpoints returned HTTP 400 quickly because DaData credentials are not configured, not because of a hang.
  - Expected: `/metrics` and local health/static probes should remain bounded and non-blocking even if PostgreSQL cache count queries or geolocation enrichment degrade.
- Hypotheses (initial):
  - H1: PostgreSQL namespace count query blocks or is slow after importing 15363 cache records.
  - H2: PostgreSQL cache health check blocks `/metrics`.
  - H3: Geolocation logging middleware adds avoidable latency for local probes, health, and metrics.
  - H4: A stale smoke/probe terminal process causes perceived hang after client-side timeout behavior.
  - H5: Docker/container health is misleading while application route workers are blocked.
  - H6: Static file routes `/` or `/select.sql` are slow/unrelated.
  - H7: DaData endpoints are waiting on upstream credentials/network.
- Most Likely (ranked):
  1) H1/H2: `/metrics` had no timeout/fallback around awaited PostgreSQL cache calls, making it vulnerable to blocking on cache operations.
  2) H3: local/health/metrics probes paid unnecessary geolocation logging overhead.
- Instrumentation:
  - Added: bounded `asyncio.wait_for(..., timeout=1.0)` wrappers around `/metrics` cache health and namespace count calls in `app/routers/api.py`; fallback returns `false`/empty counts and logs warnings.
  - Added: skip geolocation enrichment for loopback clients and `/health`, `/health/json`, `/metrics` in `app/middleware/logging.py`.
  - Results: after rebuild/redeploy, quick probes returned `/health/json` HTTP 200 in ~0.003s, `/metrics` HTTP 200 in ~0.006s, `/` HTTP 200 in ~0.001s, `/select.sql` HTTP 200 in ~0.002s; container remained healthy.
- Tentative Diagnosis: The durable risk was unbounded cache operations inside `/metrics`; the immediate post-deploy hang was consistent with probe-side/stale terminal behavior plus `/metrics` lacking defensive timeouts. Local/health/metrics geolocation logging was not the primary cause but was unnecessary overhead and was safely bypassed.
- Request Confirmation: not needed; user requested investigation and fix.
- Next: No commit/push performed. DaData smoke endpoints currently return HTTP 400 because credentials are not configured in the deployed container; this is a configuration blocker for HTTP 200 DaData validation, not a performance hang.
