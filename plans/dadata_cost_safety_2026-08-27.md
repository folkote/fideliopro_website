# DaData cost-safety production release — 2026-08-27

## Scope

Investigate unexpected DaData usage, remove paid calls from health checks, verify caching, protect all paid DaData endpoints with rate limits, rotate runtime credentials, and preserve the existing HTTP API contract for deployed clients.

## Verified findings

- The application intentionally uses DaData Cleaner address standardization through `/apiaddress/api` and `/apifulladdress/api`; no FIO/name standardization call exists.
- Address suggestions use the separate DaData Suggestions API through `/api/suggest/address`.
- Health checks formerly reached paid address cleaning; deployed health checks now inspect local service/session readiness only.
- Successful Cleaner and Suggestions responses use PostgreSQL caching.

## Release

- Code release commit: `dc5d3187fbe26cbcd8c21d950611a05272909114`.
- Production image: `fideliopro_fastapi_repo-fideliopro:trusted-proxy-dc5d318-20260827T230012Z`.
- Production image ID: `sha256:ec74385d5c9e3005a9b97e2748aeeafca9adaa40a7e86ef152d228ffd5985ff2`.
- OCI revision matches the code release commit.
- Retained rollback: `fideliopro_app_rollback_pre_trusted_proxy_20260827T230058Z`.

## Security and compatibility behavior

- Paid endpoints retain their existing paths, HTTP methods, request schemas, and response schemas.
- OpenAPI hashes for `/apiaddress/api`, `/apifulladdress/api`, `/api/suggest/address`, and `/health/json` matched between the previous production image and the release candidate.
- Default quota remains 100 requests per 60 seconds per effective client.
- `X-Forwarded-For` is trusted only from `10.0.0.25/32` and loopback.
- Docker gateway `172.19.0.1` is not trusted; direct clients cannot create new buckets by changing forwarding headers.
- Duplicate, malformed, or oversized forwarding chains fail closed to the socket peer.
- Ports 80 and 7080 remain published for backward compatibility; removing 7080 is deferred until client usage is known.

## Gates and live acceptance

- Regression suite: 11 passed.
- Compile check, cache smoke, and `git diff --check`: passed.
- Independent fail-closed review: passed with no security or logic blockers.
- Published-port spoof integration with quota 1 returned `[503, 429]` after changing `X-Forwarded-For`, proving one direct-peer bucket and zero upstream calls.
- Production health returned HTTP 200 through local ports 80 and 7080 and `https://fidelio.pro`.
- Twenty repeated health requests produced zero paid Cleaner success events.
- Production Suggestions smoke returned HTTP 200; subsequent cache reads were byte-identical and semantically identical, with cache-hit log evidence.
- Container remained healthy with restart count zero, no traceback/critical log events, and no die/restart events during a 90-second observation.

## Remaining follow-up

- Keep the trusted-proxy allowlist deployment-specific; never add broad Docker/network CIDRs.
- Retain regression coverage for duplicate forwarding fields, malformed chains, untrusted peers, and direct published-port traffic.
- Consider removing direct publication of port 7080 only after confirming that no legacy clients depend on it.
