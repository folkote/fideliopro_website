"""
Configuration settings for FidelioPro FastAPI application.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    app_name: str = "FidelioPro FastAPI"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 80

    # DaData API settings
    dadata_token: str = ""
    dadata_secret: str = ""

    # Geolocation settings
    geolocation_enabled: bool = True
    geolocation_service_url: str = (
        "http://ip-api.com/json/{ip}?fields=status,country,city,isp"
    )
    geolocation_timeout: float = 5.0
    geolocation_fallback_service: str = "https://ipapi.co/{ip}/json/"

    # Cache settings
    cache_enabled: bool = True
    cache_type: str = "file"  # "file" or "redis"
    cache_ttl: int = 3600  # 1 hour
    cache_dir: str = "data/cache"

    # Redis settings (if using Redis cache)
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Logging settings
    log_level: str = "INFO"
    log_file: str = "data/logs/webserver.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Rate limiting settings
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # Static files settings
    static_dir: str = "static"
    website_dir: str = "static/website"
    sql_dir: str = "static/sql"

    # Security settings
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
