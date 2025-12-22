"""Content model for managing missions content.

Represents main content items like stories, updates, testimonials, prayer requests, and blog posts.
"""

import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.translation import Translation
    from app.models.media import Media


class ContentType(str, enum.Enum):
    """Enum for content types."""
    
    STORY = "story"
    UPDATE = "update"
    TESTIMONIAL = "testimonial"
    PRAYER_REQUEST = "prayer_request"
    BLOG_POST = "blog_post"


class ContentStatus(str, enum.Enum):
    """Enum for content status."""
    
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Content(Base):
    """Content model for managing missions content.
    
    Attributes:
        id: Unique content identifier (UUID)
        title: Content title
        slug: URL-friendly slug (unique, indexed)
        body: Main content body (text/markdown)
        content_type: Type of content (story, update, testimonial, etc.)
        status: Publication status (draft, review, published, archived)
        author_id: UUID of the author (foreign key to Auth Service users)
        language: Content language code (default 'en')
        featured_image_url: URL to featured image
        tags: Array of tags for categorization
        meta: Additional metadata as JSON (stored as 'metadata' in database)
        published_at: When the content was published
        created_at: When the content was created (from Base)
        updated_at: When the content was last updated (from Base)
        translations: Relationship to translations
        media: Relationship to associated media
    """
    
    __tablename__ = "content"
    
    # Override id from base class to use UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )
    
    slug: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        nullable=False,
    )
    
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    content_type: Mapped[ContentType] = mapped_column(
        SQLEnum(ContentType, name="content_type_enum"),
        nullable=False,
        index=True,
    )
    
    status: Mapped[ContentStatus] = mapped_column(
        SQLEnum(ContentStatus, name="content_status_enum"),
        nullable=False,
        default=ContentStatus.DRAFT,
        index=True,
    )
    
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Foreign key to Auth Service users table",
    )
    
    language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="en",
        index=True,
    )
    
    featured_image_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )
    
    tags: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        default=[],
    )
    
    meta: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSONB,
        nullable=True,
        default={},
    )
    
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    
    # Relationships
    translations: Mapped[list["Translation"]] = relationship(
        "Translation",
        back_populates="content",
        cascade="all, delete-orphan",
    )
    
    media: Mapped[list["Media"]] = relationship(
        "Media",
        back_populates="content",
        cascade="all, delete-orphan",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_content_type_status", "content_type", "status"),
        Index("idx_language_status", "language", "status"),
        Index("idx_author_status", "author_id", "status"),
        Index("idx_published_at_desc", published_at.desc()),
    )
    
    def __repr__(self) -> str:
        """String representation of Content."""
        return (
            f"<Content(id={self.id}, title='{self.title}', "
            f"type={self.content_type}, status={self.status})>"
        )
