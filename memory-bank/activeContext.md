# Active Context

## Current Focus
- Completed and closed: unified DaData Cleaner runtime cache now uses the versioned full-response namespace `dadata_clean_address_full_v1` while preserving external HTTP compatibility.
- Compatibility endpoints [`api_address()`](../app/routers/api.py:39) and [`api_full_address()`](../app/routers/api.py:100) were implemented, deployed, validated, committed as `306ddac`, and pushed to `origin/main` on branch `main`.
- Runtime use of old partial namespaces `dadata_street_fias` and `dadata_cleaned_address` is retired for Cleaner compatibility endpoint calls; old rows remain physically present only as historical cache data.

## Next Steps (ordered)
1. [Closed] Planning, documentation, implementation, deployment, validation, commit, and push for the unified DaData Cleaner full-response cache are complete.
2. [Operator optional] Leave old partial namespace rows in place unless a separate cleanup task is explicitly approved; no migration into `dadata_clean_address_full_v1` is possible from derived partial values.
3. [Documentation follow-up] Commit this final Memory Bank synthesis separately because implementation commit `306ddac` was already pushed before closure documentation was added.

## Delegation Map
- Architect: owns Memory Bank plan, ADR, acceptance criteria, and handoff clarity.
- Coder: implements the service-level replacement in [`app/services/dadata.py`](../app/services/dadata.py:20), updates endpoint-adjacent tests, and avoids source changes outside the compatibility requirement.
- Debug: validates runtime cache behavior, metrics namespace counts, and deployed compatibility responses.
- Operators: may later decide whether to archive or delete old namespace rows from [`cache_entries`](../app/services/cache.py:48); this is not required for the implementation and must not be treated as a data migration into the new namespace.

## Closure Evidence
- Commit and push: `306ddac` with message `Unify DaData cleaner address cache`, pushed from branch `main` to `origin/main`.
- Deployed container: `fideliopro_app` on host port `7080`, using image `fideliopro_fastapi_repo-fideliopro:dadata-clean-cache-20260716T165914Z`; Docker health reported healthy.
- Deployed validation: one new `dadata_clean_address_full_v1` row was created for the shared Cleaner smoke address, repeated compatibility endpoint calls reused it, and old namespaces `dadata_street_fias` plus `dadata_cleaned_address` stayed unchanged.
- Compatibility validation: `/apiaddress/api` and `/apifulladdress/api` returned HTTP 200 plain-text responses with stable repeat values; `/api/suggest/address` still returned HTTP 200 JSON and reused its own `dadata_suggest_address` cache.
- Committed implementation/documentation set: [`app/services/dadata.py`](../app/services/dadata.py), [`memory-bank/activeContext.md`](activeContext.md), [`memory-bank/systemPatterns.md`](systemPatterns.md), [`memory-bank/progress.md`](progress.md), and [`test/smoke_dadata_clean_cache.py`](../test/smoke_dadata_clean_cache.py).

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
