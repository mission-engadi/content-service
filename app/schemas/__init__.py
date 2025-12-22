"""Pydantic schemas for request/response validation."""

from app.schemas.content import (
    ContentBase,
    ContentCreate,
    ContentUpdate,
    ContentInDB,
    ContentResponse,
    ContentWithTranslations,
    ContentWithMedia,
    ContentFull,
    ContentList,
)  # noqa: F401

from app.schemas.translation import (
    TranslationBase,
    TranslationCreate,
    TranslationUpdate,
    TranslationInDB,
    TranslationResponse,
    TranslationList,
)  # noqa: F401

from app.schemas.media import (
    MediaBase,
    MediaCreate,
    MediaUpdate,
    MediaInDB,
    MediaResponse,
    MediaList,
)  # noqa: F401

__all__ = [
    # Content schemas
    "ContentBase",
    "ContentCreate",
    "ContentUpdate",
    "ContentInDB",
    "ContentResponse",
    "ContentWithTranslations",
    "ContentWithMedia",
    "ContentFull",
    "ContentList",
    # Translation schemas
    "TranslationBase",
    "TranslationCreate",
    "TranslationUpdate",
    "TranslationInDB",
    "TranslationResponse",
    "TranslationList",
    # Media schemas
    "MediaBase",
    "MediaCreate",
    "MediaUpdate",
    "MediaInDB",
    "MediaResponse",
    "MediaList",
]
