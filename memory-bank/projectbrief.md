# Project Brief

## Scope
- In scope: FastAPI application that serves the FidelioPro static website and exposes compatibility API endpoints for address cleaning through DaData.
- In scope: PostgreSQL-backed caching for repeated DaData and geolocation lookups.
- In scope: Operational health and metrics endpoints for deployment validation.
- Out of scope: Direct modification of upstream DaData behavior or replacement of DaData as the source of address normalization.

## Success Criteria
- Repeated identical address requests are served from PostgreSQL cache without repeated DaData calls.
- Existing compatibility endpoints continue returning plain text responses expected by existing clients.
- Static website routes continue to serve HTML, SQL, CSS, JS, and image assets without download headers where HTML rendering is expected.
- Health and metrics endpoints remain bounded and useful for deployment validation.

## Stakeholders
- Product owner: FidelioPro maintainers.
- Users: Website visitors and client integrations that call the address-cleaning endpoints.
- Operators: Maintainers responsible for deployment, DaData credentials, PostgreSQL connectivity, and runtime monitoring.
