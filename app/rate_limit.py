"""Shared SlowAPI limiter for paid upstream endpoints."""

from ipaddress import ip_address, ip_network
from typing import Sequence

from slowapi import Limiter
from starlette.requests import Request

from .config import settings


TRUSTED_PROXY_NETWORKS = tuple(
    ip_network(value, strict=False) for value in settings.rate_limit_trusted_proxies
)


def rate_limit_client_ip(
    request: Request,
    trusted_proxies: Sequence | None = None,
) -> str:
    """Return a spoof-resistant client IP through explicitly trusted proxies."""
    peer_value = request.client.host if request.client else "unknown"
    try:
        peer = ip_address(peer_value)
    except ValueError:
        return peer_value

    networks = TRUSTED_PROXY_NETWORKS if trusted_proxies is None else trusted_proxies
    forwarded_headers = request.headers.getlist("x-forwarded-for")
    if (
        len(forwarded_headers) != 1
        or not any(peer in network for network in networks)
    ):
        return str(peer)

    forwarded_for = forwarded_headers[0]
    values = [value.strip() for value in forwarded_for.split(",")]
    if not values or len(values) > 20 or any(not value for value in values):
        return str(peer)

    try:
        forwarded = [ip_address(value) for value in values]
    except ValueError:
        return str(peer)

    current = peer
    for candidate in reversed(forwarded):
        if not any(current in network for network in networks):
            break
        current = candidate
    return str(current)


limiter = Limiter(
    key_func=rate_limit_client_ip,
    enabled=settings.rate_limit_enabled,
)
paid_api_limit = f"{settings.rate_limit_requests}/{settings.rate_limit_window}second"
