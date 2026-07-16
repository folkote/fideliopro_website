# Active Context

## Current Focus
- Review current DaData proxy/cache behavior before adding another endpoint.
- Preserve existing compatibility behavior while avoiding duplicated cache/upstream logic.
- Plan a new DaData Suggestions proxy endpoint: `POST /api/suggest/address`, accepting the same JSON body as DaData and returning the full DaData JSON response unchanged.

## Next Steps (ordered)
1. [Architect] Confirm the desired new endpoint path, response format, and exact DaData field or transformation to expose. Confirmed: `POST /api/suggest/address`, full JSON passthrough.
2. [Coder] Add a cache-aware method to [`DaDataService`](../app/services/dadata.py:21) for DaData Suggestions address API with a dedicated namespace such as `dadata_suggest_address`.
3. [Coder] Build a canonical cache key from the entire incoming JSON body after deterministic JSON serialization so optional parameters such as `count`, `language`, `division`, `locations`, `locations_geo`, `locations_boost`, `from_bound`, and `to_bound` produce distinct cache entries.
4. [Coder] Add a thin `POST /api/suggest/address` endpoint in [`app/routers/api.py`](../app/routers/api.py:20) that validates body presence and delegates to the service method without transforming the successful response.
5. [Coder] Preserve DaData response body exactly on successful upstream calls and cache only successful HTTP 200 JSON responses.
6. [Coder] Add or update tests and smoke checks for cache hit, cache miss, invalid body, missing DaData credentials, DaData non-200 responses, and existing endpoint compatibility.
7. [Debug] Validate deployed behavior with real `DATABASE_URL`, `CACHE_SCHEMA`, and DaData credentials without printing secrets.

## Acceptance Criteria
- New endpoint does not duplicate direct DaData HTTP calls in the router.
- New endpoint uses namespace-scoped PostgreSQL caching for complete DaData Suggestions response payloads.
- Existing `/apiaddress/api` and `/apifulladdress/api` behavior remains unchanged unless a compatibility change is explicitly approved.
- Repeated identical requests to the new endpoint avoid repeated DaData calls after the first successful cache write.
- Successful response body from `POST /api/suggest/address` is the same JSON object returned by DaData, with no field filtering, renaming, or enrichment.
- Non-200 DaData responses are not cached by default, so transient upstream errors and rate-limit responses do not become durable cached failures.

## Constraints
- Keep existing plain text compatibility endpoints stable.
- Avoid logging full sensitive user input; continue truncating address values in logs.
- DaData credentials and database URL are operational configuration, not source-controlled values.
- The Suggestions API is interactive and paid; cache correctness depends on using all request body parameters in the cache key.
