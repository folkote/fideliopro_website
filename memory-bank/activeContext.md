# Active Context

## Current Focus
- Plan full replacement of the split DaData Cleaner runtime cache with one versioned full-response cache while preserving external HTTP compatibility.
- Keep existing compatibility endpoints [`api_address()`](../app/routers/api.py:39) and [`api_full_address()`](../app/routers/api.py:100) stable: same URLs, same `address` query parameter, and same plain-text response semantics.
- Retire runtime use of old partial namespaces `dadata_street_fias` and `dadata_cleaned_address`; do not migrate those rows into the new full-response namespace because derived strings cannot reconstruct a complete DaData Cleaner response.

## Next Steps (ordered)
1. [Architect] Document the target Cleaner cache contract, old-cache retirement policy, compatibility guarantees, and implementation acceptance criteria.
2. [Coder] Add one new Cleaner cache namespace constant in [`app/services/dadata.py`](../app/services/dadata.py:20): `dadata_clean_address_full_v1`.
3. [Coder] Add a canonicalization helper for the compatibility input address before cache lookup. The first implementation should trim surrounding whitespace and preserve the remaining string exactly; if future normalization expands, it must be documented and versioned.
4. [Coder] Add a deterministic cache key helper for Cleaner calls: `sha256(canonical_address.encode("utf-8"))`, optionally prefixed as `address_sha256:<hex>` for operator readability.
5. [Coder] Add a cache-aware full Cleaner method that reads/writes only `dadata_clean_address_full_v1`, calls DaData Cleaner only on cache miss, and stores a versioned JSONB envelope in existing PostgreSQL table [`cache_entries`](../app/services/cache.py:48).
6. [Coder] Preserve wrapper methods [`DaDataService.get_street_fias_id()`](../app/services/dadata.py:142) and [`DaDataService.get_cleaned_address_text()`](../app/services/dadata.py:192) as backward-compatible service APIs, but make both derive their strings from the new full-response envelope instead of reading or writing old partial namespaces.
7. [Coder] Keep [`api_address()`](../app/routers/api.py:39) and [`api_full_address()`](../app/routers/api.py:100) externally unchanged, including plain-text successful responses and existing URL/query shape.
8. [Coder] Remove all new runtime reads and writes to `dadata_street_fias` and `dadata_cleaned_address`; old rows may remain physically present until an operator-led cleanup, but they must be inert.
9. [Coder] Add or update tests for first-call cache miss, second-call cache hit, extraction of `street_fias_id`, extraction of `result`, empty or missing fields, missing credentials, upstream non-200 behavior, and no calls to old namespaces.
10. [Debug] Validate deployed behavior with real `DATABASE_URL`, `CACHE_SCHEMA`, and DaData credentials without printing secrets; confirm old namespace counts do not change during compatibility endpoint calls.

## Delegation Map
- Architect: owns Memory Bank plan, ADR, acceptance criteria, and handoff clarity.
- Coder: implements the service-level replacement in [`app/services/dadata.py`](../app/services/dadata.py:20), updates endpoint-adjacent tests, and avoids source changes outside the compatibility requirement.
- Debug: validates runtime cache behavior, metrics namespace counts, and deployed compatibility responses.
- Operators: may later decide whether to archive or delete old namespace rows from [`cache_entries`](../app/services/cache.py:48); this is not required for the implementation and must not be treated as a data migration into the new namespace.

## Target Cache Contract
- Physical store: existing PostgreSQL JSONB table [`cache_entries`](../app/services/cache.py:48).
- Namespace: `dadata_clean_address_full_v1`.
- Logical key input: canonicalized compatibility `address` query value.
- Canonicalization v1: trim leading and trailing whitespace only; preserve case, internal whitespace, punctuation, and language-specific characters.
- Cache key algorithm: compute SHA-256 over the UTF-8 canonical address and store under a deterministic string key such as `address_sha256:<64-hex-digest>`.
- Cache value envelope:

```json
{
  "schema_version": 1,
  "provider": "dadata",
  "api": "cleaner.address",
  "canonical_address": "<trimmed input address>",
  "response": {"<full DaData Cleaner first result object>": true}
}
```

- The `response` member must contain the full first object returned by DaData Cleaner for the address, not only the derived `street_fias_id` or `result` strings.
- Cache only successful HTTP 200 Cleaner responses that contain a first result object. Do not cache credential failures, network errors, rate limits, non-200 responses, or empty result arrays by default.
- The version suffix `_v1` and `schema_version` allow a future incompatible canonicalization or envelope change to use a new namespace rather than corrupting existing entries.

## Deployment and Test Sequence
1. Run unit tests around canonicalization, key generation, envelope shape, and old-namespace non-use.
2. Run compile validation with `python -m compileall -q app scripts run.py`.
3. In a test database, capture starting namespace counts for `dadata_clean_address_full_v1`, `dadata_street_fias`, and `dadata_cleaned_address`.
4. Call `/apiaddress/api?address=<sample>` twice and verify the second call is served from `dadata_clean_address_full_v1` while returning the same plain-text street FIAS ID semantics.
5. Call `/apifulladdress/api?address=<sample>` twice and verify the second call is served from `dadata_clean_address_full_v1` while returning the same plain-text cleaned address semantics.
6. Confirm old namespace counts for `dadata_street_fias` and `dadata_cleaned_address` do not increase during the smoke tests.
7. Confirm `/metrics` remains bounded and includes namespace counts without requiring old namespace activity.

## Acceptance Criteria
- [`api_address()`](../app/routers/api.py:39) and [`api_full_address()`](../app/routers/api.py:100) keep the same URLs, same `address` query parameter, and same plain-text response semantics for successful requests.
- [`DaDataService.get_street_fias_id()`](../app/services/dadata.py:142) and [`DaDataService.get_cleaned_address_text()`](../app/services/dadata.py:192) remain callable but derive values from one full DaData Cleaner response envelope.
- Runtime cache reads and writes use only `dadata_clean_address_full_v1` for Cleaner compatibility endpoint data.
- Runtime code no longer reads from or writes to `dadata_street_fias` or `dadata_cleaned_address`.
- Repeated canonicalized identical address requests avoid repeated paid DaData Cleaner calls after the first successful cache write.
- The cached JSONB envelope includes `schema_version`, provider/API identity, canonical address, and the full DaData Cleaner first-result object.
- Old partial cache rows are not migrated into `dadata_clean_address_full_v1`; documentation explicitly states they cannot reconstruct the full DaData response.
- Tests or smoke validation prove compatibility responses, cache hit/miss behavior, and old namespace retirement.

## Constraints
- Keep existing plain text compatibility endpoints stable.
- Avoid logging full sensitive user input; continue truncating address values in logs.
- DaData credentials and database URL are operational configuration, not source-controlled values.
- The Cleaner API is paid; cache correctness depends on a deterministic canonical address key and a versioned envelope.
- No application source code changes are made in Architect mode; implementation belongs to Coder mode.
