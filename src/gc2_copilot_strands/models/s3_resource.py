"""Pydantic models for AWS S3 resources."""

from typing import Literal
from pydantic import BaseModel, Field, constr


class S3Properties(BaseModel):
    """
    AWS S3 resource properties.

    Minimal set of required properties for S3 resource configuration.
    """
    awsRegion: Literal["us-east-1", "us-east-2", "us-west-1", "us-west-2", "eu-west-2", "eu-west-1", "eu-central-1"] = Field(
        ...,
        description="AWS region where the S3 bucket exists"
    )
    s3Path: constr(max_length=319, pattern=r'.+') = Field(
        ...,
        description="S3 bucket path in format: bucket-name/path/to/folder"
    )
    awsAccountName: constr(max_length=100) = Field(
        ...,
        description="AWS account name"
    )
    kmsKey: constr(max_length=50, pattern=r'.+') = Field(
        ...,
        description="KMS key for encryption (use alias format like 'alias/aws/s3')"
    )
    isEnabled: bool = Field(
        ...,
        description="Whether this resource is enabled"
    )
    description: constr(max_length=100, pattern=r'.+') = Field(
        ...,
        description="Human-readable description of this S3 resource"
    )

    class Config:
        extra = "forbid"  # Don't allow extra fields


class S3Resource(BaseModel):
    """Complete S3 resource with name, type, and properties."""

    resourceName: constr(max_length=50, pattern=r'.+') = Field(
        ...,
        description="Unique name for this S3 resource"
    )
    type: Literal["aws-s3"] = Field(
        default="aws-s3",
        description="Resource type"
    )
    properties: S3Properties = Field(
        ...,
        description="S3 resource properties"
    )

    class Config:
        extra = "forbid"
