"""Translation model for managing content translations.

Represents translations of content into different languages.
"""

import uuid
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.content import Content


class TranslationStatus(str, enum.Enum):
    """Enum for translation status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"


class Translation(Base):
    """Translation model for multi-language content support.
    
    Attributes:
        id: Unique translation identifier (UUID)
        content_id: UUID of the original content (foreign key)
        language: Target language code (en, es, fr, pt-br)
        translated_title: Translated title
        translated_body: Translated content body
        translated_slug: Translated URL-friendly slug
        translator_id: UUID of the translator (optional, from Auth Service)
        translation_status: Status of the translation
        created_at: When the translation was created (from Base)
        updated_at: When the translation was last updated (from Base)
        content: Relationship to the original content
    """
    
    __tablename__ = "translations"
    
    # Override id from base class to use UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Language code: en, es, fr, pt-br",
    )
    
    translated_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    
    translated_body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    translated_slug: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    
    translator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Foreign key to Auth Service users table",
    )
    
    translation_status: Mapped[TranslationStatus] = mapped_column(
        SQLEnum(TranslationStatus, name="translation_status_enum"),
        nullable=False,
        default=TranslationStatus.PENDING,
        index=True,
    )
    
    # Relationships
    content: Mapped["Content"] = relationship(
        "Content",
        back_populates="translations",
    )
    
    # Indexes and Constraints
    __table_args__ = (
        Index("idx_content_language", "content_id", "language", unique=True),
        Index("idx_translation_status", "translation_status"),
        Index("idx_language_status", "language", "translation_status"),
    )
    
    def __repr__(self) -> str:
        """String representation of Translation."""
        return (
            f"<Translation(id={self.id}, content_id={self.content_id}, "
            f"language='{self.language}', status={self.translation_status})>"
        )
