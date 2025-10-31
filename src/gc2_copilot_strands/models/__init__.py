"""Pydantic models for GC2 resources."""

from .plan import ResourceSpec, ConnectionSpec, PipelinePlan
from .s3_resource import S3Properties, S3Resource
from .route_resource import RouteProperties, RouteResource, SourceDestinationRef

__all__ = [
    "ResourceSpec",
    "ConnectionSpec",
    "PipelinePlan",
    "S3Properties",
    "S3Resource",
    "RouteProperties",
    "RouteResource",
    "SourceDestinationRef",
]
