"""Pydantic models for Route resources."""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, constr


class SourceDestinationRef(BaseModel):
    """Reference to a source or destination resource."""
    ref: constr(max_length=50, pattern=r'.+') = Field(
        ...,
        description="Resource name reference"
    )

    class Config:
        extra = "forbid"


class RouteProperties(BaseModel):
    """
    Route resource properties.

    Routes connect source and destination resources with filtering and transformation logic.
    """
    description: constr(max_length=200, pattern=r'.+') = Field(
        ...,
        description="Human-readable description of this route"
    )
    fileFilter: constr(max_length=200, pattern=r'.+') = Field(
        ...,
        description="Regex pattern for filtering files (e.g., .+\\.csv for CSV files)"
    )
    isEnabled: bool = Field(
        ...,
        description="Whether this route is enabled"
    )
    source: SourceDestinationRef = Field(
        ...,
        description="Reference to source resource"
    )
    destination: SourceDestinationRef = Field(
        ...,
        description="Reference to destination resource"
    )
    actions: Optional[List[Literal["pgp-decrypt", "pgp-encrypt", "zip", "gzip", "unzip", "validate-inline", "validate-offline", "virus-check", "batch"]]] = Field(
        default=None,
        description="Optional list of actions to perform on files (decrypt, encrypt, zip, etc.)"
    )
    failureEmail: constr(max_length=200, pattern=r'.+') = Field(
        ...,
        description="Email address for failure notifications"
    )
    successEmail: constr(max_length=200, pattern=r'.+') = Field(
        ...,
        description="Email address for success notifications"
    )
    disableFailureEmail: bool = Field(
        default=True,
        description="Whether to disable failure email notifications"
    )
    disableSuccessEmail: bool = Field(
        default=False,
        description="Whether to disable success email notifications"
    )

    class Config:
        extra = "forbid"  # Don't allow extra fields


class RouteResource(BaseModel):
    """Complete Route resource with name, type, and properties."""

    resourceName: constr(max_length=50, pattern=r'.+') = Field(
        ...,
        description="Unique name for this route resource"
    )
    type: Literal["route"] = Field(
        default="route",
        description="Resource type"
    )
    properties: RouteProperties = Field(
        ...,
        description="Route resource properties"
    )

    class Config:
        extra = "forbid"
