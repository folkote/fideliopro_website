"""
Pydantic models for API responses.
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class AddressResponse(BaseModel):
    """Response model for address API."""

    street_fias_id: Optional[str] = Field(None, description="FIAS ID of the street")

    class Config:
        json_encoders = {type(None): lambda v: None}


class FullAddressResponse(BaseModel):
    """Response model for full address API."""

    result: Optional[Dict[str, Any]] = Field(
        None, description="Full DaData cleaning result"
    )

    class Config:
        json_encoders = {type(None): lambda v: None}


class GeolocationResponse(BaseModel):
    """Response model for IP geolocation."""

    country: Optional[str] = Field(None, description="Country name")
    city: Optional[str] = Field(None, description="City name")
    isp: Optional[str] = Field(None, description="Internet Service Provider")
    status: Optional[str] = Field(None, description="Request status")

    class Config:
        json_encoders = {type(None): lambda v: ""}


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: str = Field(..., description="Current timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
