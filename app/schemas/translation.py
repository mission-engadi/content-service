"""Translation schemas for API requests and responses.

Defines Pydantic models for translation-related operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.translation import TranslationStatus


class TranslationBase(BaseModel):
    """Base translation schema with common fields."""
    
    language: str = Field(
        ...,
        min_length=2,
        max_length=10,
        description="Target language code",
        examples=["es", "fr", "pt-br"],
    )
    translated_title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Translated title",
        examples=["Actualización de la Misión: Construyendo Esperanza en Uganda"],
    )
    translated_body: str = Field(
        ...,
        min_length=1,
        description="Translated content body",
        examples=["Este mes celebramos la finalización de..."],
    )
    translated_slug: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Translated URL-friendly slug",
        examples=["actualizacion-mision-esperanza-uganda"],
    )


class TranslationCreate(TranslationBase):
    """Schema for creating a new translation."""
    
    content_id: uuid.UUID = Field(
        ...,
        description="UUID of the original content",
    )
    translation_status: TranslationStatus = Field(
        default=TranslationStatus.PENDING,
        description="Status of the translation",
        examples=[TranslationStatus.PENDING],
    )
    translator_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the translator (optional)",
    )


class TranslationUpdate(BaseModel):
    """Schema for updating a translation.
    
    All fields are optional to support partial updates.
    """
    
    language: Optional[str] = Field(
        None,
        min_length=2,
        max_length=10,
        description="Target language code",
    )
    translated_title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Translated title",
    )
    translated_body: Optional[str] = Field(
        None,
        min_length=1,
        description="Translated content body",
    )
    translated_slug: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Translated slug",
    )
    translation_status: Optional[TranslationStatus] = Field(
        None,
        description="Status of the translation",
    )
    translator_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the translator",
    )


class TranslationInDB(TranslationBase):
    """Translation schema as stored in database."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID = Field(
        ...,
        description="Unique translation identifier",
    )
    content_id: uuid.UUID = Field(
        ...,
        description="UUID of the original content",
    )
    translator_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the translator",
    )
    translation_status: TranslationStatus = Field(
        ...,
        description="Status of the translation",
    )
    created_at: datetime = Field(
        ...,
        description="When the translation was created",
    )
    updated_at: datetime = Field(
        ...,
        description="When the translation was last updated",
    )


class TranslationResponse(TranslationInDB):
    """Translation schema for API responses."""
    
    pass


class TranslationList(BaseModel):
    """Schema for paginated translation list."""
    
    items: list[TranslationResponse] = Field(
        ...,
        description="List of translation items",
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
