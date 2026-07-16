# Product Context

## Problem
- The application preserves a legacy FidelioPro website/API surface while moving runtime behavior into a FastAPI service.
- Address-related clients need DaData normalization results, but repeated calls should avoid unnecessary upstream cost and latency.

## Goals
- Provide stable compatibility endpoints for existing address-cleaning consumers.
- Reduce repeated DaData usage through durable PostgreSQL caching.
- Keep the static website and utility pages available from the same service.

## User Stories
- As an integration client I want to submit an address and receive a street FIAS ID so that guest address data can be validated.
- As an integration client I want to submit an address and receive cleaned address text so that downstream systems can store normalized address strings.
- As an operator I want health and metrics endpoints so that deployment status and cache connectivity can be checked quickly.

## UX Notes
- Address API compatibility responses are plain text, not JSON, for current endpoint behavior.
- Static website pages should render in browser by default rather than forcing file download.
