"""
Configuration settings for FidelioPro FastAPI application.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

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

    # PostgreSQL-only cache settings
    cache_enabled: bool = True
    database_url: Optional[str] = None
    cache_schema: str = "fideliopro_website"

    # Logging settings
    log_level: str = "INFO"
    log_file: str = "logs/webserver.log"
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


# Global settings instance
settings = Settings()
