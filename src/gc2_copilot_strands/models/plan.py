"""Pydantic models for pipeline planning."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ResourceSpec(BaseModel):
    """Specification for a planned resource."""

    id: int = Field(..., description="Unique resource ID")
    name: str = Field(..., max_length=50, description="Resource name (max 50 chars, use hyphens)")
    type: str = Field(..., description="GC2 resource type (aws-s3, route, external-partner, etc.)")
    role: str = Field(..., description="Resource role (source, destination, processor)")
    description: str = Field(..., max_length=200, description="What this resource does")



class ConnectionSpec(BaseModel):
    """Specification for a connection between resources."""

    from_resource: int = Field(..., description="Source resource ID")
    to_resource: int = Field(..., description="Destination resource ID")
    via: str = Field(default="route", description="Connection type (usually 'route')")
    route_name: Optional[str] = Field(None, description="Name for the route resource")
    file_filter: str = Field(default=".+", description="Regex pattern for file filtering")
    actions: Optional[List[str]] = Field(
        default=None,
        description="Actions to apply (pgp-decrypt, pgp-encrypt, zip, unzip, virus-check). Use None for no actions.",
    )


class PipelinePlan(BaseModel):
    """Complete pipeline resource plan."""

    pattern_type: str = Field(..., description="Brief description of the data flow pattern")
    resources: List[ResourceSpec] = Field(..., description="List of planned resources")
    connections: List[ConnectionSpec] = Field(..., description="List of connections between resources")
    explanation: str = Field(..., description="Reasoning for this architecture")
