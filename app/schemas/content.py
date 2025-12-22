"""Content schemas for API requests and responses.

Defines Pydantic models for content-related operations.
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict

from app.models.content import ContentType, ContentStatus

if TYPE_CHECKING:
    from app.schemas.translation import TranslationResponse
    from app.schemas.media import MediaResponse


class ContentBase(BaseModel):
    """Base content schema with common fields."""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Content title",
        examples=["Mission Update: Building Hope in Uganda"],
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="URL-friendly slug",
        examples=["mission-update-building-hope-uganda"],
    )
    body: str = Field(
        ...,
        min_length=1,
        description="Main content body (supports markdown)",
        examples=["This month we celebrated the completion of..."],
    )
    content_type: ContentType = Field(
        ...,
        description="Type of content",
        examples=[ContentType.STORY],
    )
    language: str = Field(
        default="en",
        max_length=10,
        description="Content language code",
        examples=["en", "es", "fr", "pt-br"],
    )
    featured_image_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to featured image",
        examples=["https://example.com/images/featured.jpg"],
    )
    tags: Optional[list[str]] = Field(
        default=[],
        description="Array of tags for categorization",
        examples=[["missions", "uganda", "education"]],
    )
    metadata: Optional[dict] = Field(
        default={},
        description="Additional metadata as JSON",
        examples=[{"reading_time": 5, "location": "Uganda"}],
    )


class ContentCreate(ContentBase):
    """Schema for creating new content."""
    
    status: ContentStatus = Field(
        default=ContentStatus.DRAFT,
        description="Publication status",
        examples=[ContentStatus.DRAFT],
    )


class ContentUpdate(BaseModel):
    """Schema for updating content.
    
    All fields are optional to support partial updates.
    """
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Content title",
    )
    slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="URL-friendly slug",
    )
    body: Optional[str] = Field(
        None,
        min_length=1,
        description="Main content body",
    )
    content_type: Optional[ContentType] = Field(
        None,
        description="Type of content",
    )
    status: Optional[ContentStatus] = Field(
        None,
        description="Publication status",
    )
    language: Optional[str] = Field(
        None,
        max_length=10,
        description="Content language code",
    )
    featured_image_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to featured image",
    )
    tags: Optional[list[str]] = Field(
        None,
        description="Array of tags",
    )
    metadata: Optional[dict] = Field(
        None,
        description="Additional metadata",
    )


class ContentInDB(ContentBase):
    """Content schema as stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(
        ...,
        description="Unique content identifier",
    )
    status: ContentStatus = Field(
        ...,
        description="Publication status",
    )
    author_id: uuid.UUID = Field(
        ...,
        description="UUID of the author",
    )
    published_at: Optional[datetime] = Field(
        None,
        description="When the content was published",
    )
    created_at: datetime = Field(
        ...,
        description="When the content was created",
    )
    updated_at: datetime = Field(
        ...,
        description="When the content was last updated",
    )


class ContentResponse(ContentInDB):
    """Content schema for API responses."""
    
    pass


class ContentWithTranslations(ContentResponse):
    """Content schema with translations included."""
    
    translations: list["TranslationResponse"] = Field(
        default=[],
        description="Available translations",
    )


class ContentWithMedia(ContentResponse):
    """Content schema with media included."""
    
    media: list["MediaResponse"] = Field(
        default=[],
        description="Associated media files",
    )


class ContentFull(ContentResponse):
    """Content schema with all relationships."""
    
    translations: list["TranslationResponse"] = Field(
        default=[],
        description="Available translations",
    )
    media: list["MediaResponse"] = Field(
        default=[],
        description="Associated media files",
    )


class ContentList(BaseModel):
    """Schema for paginated content list."""
    
    items: list[ContentResponse] = Field(
        ...,
        description="List of content items",
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