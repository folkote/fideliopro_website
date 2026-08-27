"""Shared SlowAPI limiter for paid upstream endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings


limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
)
paid_api_limit = f"{settings.rate_limit_requests}/{settings.rate_limit_window}second"
