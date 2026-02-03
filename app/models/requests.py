"""
Pydantic models for API requests.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class AddressRequest(BaseModel):
    """Request model for address cleaning."""

    address: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Address to be cleaned and validated",
    )

    @validator("address")
    def validate_address(cls, v):
        """Validate and clean address input."""
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")

        # Remove excessive whitespace
        cleaned = " ".join(v.strip().split())

        if len(cleaned) < 3:
            raise ValueError("Address is too short")

        return cleaned


class GeolocationRequest(BaseModel):
    """Request model for IP geolocation."""

    ip: str = Field(..., description="IP address for geolocation lookup")

    @validator("ip")
    def validate_ip(cls, v):
        """Basic IP validation."""
        if not v or not v.strip():
            raise ValueError("IP address cannot be empty")

        # Basic IP format validation (IPv4)
        parts = v.strip().split(".")
        if len(parts) == 4:
            try:
                for part in parts:
                    num = int(part)
                    if not 0 <= num <= 255:
                        raise ValueError("Invalid IP address format")
            except ValueError:
                raise ValueError("Invalid IP address format")

        return v.strip()
