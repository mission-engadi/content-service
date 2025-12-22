"""Media schemas for API requests and responses.

Defines Pydantic models for media-related operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.media import MediaType


class MediaBase(BaseModel):
    """Base media schema with common fields."""
    
    media_type: MediaType = Field(
        ...,
        description="Type of media",
        examples=[MediaType.IMAGE],
    )
    filename: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Original filename",
        examples=["mission-building.jpg"],
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Public URL to access the media",
        examples=["https://cdn.example.com/media/mission-building.jpg"],
    )
    storage_path: Optional[str] = Field(
        None,
        max_length=1000,
        description="Path in storage system (e.g., S3 key)",
        examples=["uploads/2024/12/mission-building.jpg"],
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes",
        examples=[1048576],
    )
    mime_type: Optional[str] = Field(
        None,
        max_length=100,
        description="MIME type of the file",
        examples=["image/jpeg"],
    )
    width: Optional[int] = Field(
        None,
        ge=0,
        description="Width in pixels (for images/videos)",
        examples=[1920],
    )
    height: Optional[int] = Field(
        None,
        ge=0,
        description="Height in pixels (for images/videos)",
        examples=[1080],
    )
    duration: Optional[int] = Field(
        None,
        ge=0,
        description="Duration in seconds (for video/audio)",
        examples=[180],
    )
    metadata: Optional[dict] = Field(
        default={},
        description="Additional metadata as JSON",
        examples=[{"exif": {"camera": "Canon EOS"}, "location": "Uganda"}],
    )


class MediaCreate(MediaBase):
    """Schema for creating new media."""
    
    content_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the associated content (optional)",
    )


class MediaUpdate(BaseModel):
    """Schema for updating media.
    
    All fields are optional to support partial updates.
    """
    
    content_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the associated content",
    )
    media_type: Optional[MediaType] = Field(
        None,
        description="Type of media",
    )
    filename: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Original filename",
    )
    url: Optional[str] = Field(
        None,
        min_length=1,
        max_length=1000,
        description="Public URL",
    )
    storage_path: Optional[str] = Field(
        None,
        max_length=1000,
        description="Storage path",
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes",
    )
    mime_type: Optional[str] = Field(
        None,
        max_length=100,
        description="MIME type",
    )
    width: Optional[int] = Field(
        None,
        ge=0,
        description="Width in pixels",
    )
    height: Optional[int] = Field(
        None,
        ge=0,
        description="Height in pixels",
    )
    duration: Optional[int] = Field(
        None,
        ge=0,
        description="Duration in seconds",
    )
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata",
    )


class MediaInDB(MediaBase):
    """Media schema as stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(
        ...,
        description="Unique media identifier",
    )
    content_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the associated content",
    )
    uploaded_by: uuid.UUID = Field(
        ...,
        description="UUID of the user who uploaded",
    )
    created_at: datetime = Field(
        ...,
        description="When the media was created",
    )


class MediaResponse(MediaInDB):
    """Media schema for API responses."""
    
    pass


class MediaList(BaseModel):
    """Schema for paginated media list."""
    
    items: list[MediaResponse] = Field(
        ...,
        description="List of media items",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of items",
    )
    page: int = Field(
        ...,
        ge=1,
        description="Current page number",
    )
    page_size: int = Field(
        ...,
        ge=1,
        le=100,
        description="Items per page",
    )
    pages: int = Field(
        ...,
        ge=0,
        description="Total number of pages",
    )
