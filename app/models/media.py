"""Media model for managing media files.

Represents media files (images, videos, audio, documents) associated with content.
"""

import uuid
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.content import Content


class MediaType(str, enum.Enum):
    """Enum for media types."""
    
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class Media(Base):
    """Media model for managing media files.
    
    Attributes:
        id: Unique media identifier (UUID)
        content_id: UUID of the associated content (foreign key, nullable)
        media_type: Type of media (image, video, audio, document)
        filename: Original filename
        url: Public URL to access the media
        storage_path: Path in storage system (e.g., S3)
        file_size: Size of the file in bytes
        mime_type: MIME type of the file
        width: Width in pixels (for images/videos)
        height: Height in pixels (for images/videos)
        duration: Duration in seconds (for video/audio)
        meta: Additional metadata as JSON (stored as 'metadata' in database)
        uploaded_by: UUID of the user who uploaded (from Auth Service)
        created_at: When the media was created (from Base)
        content: Relationship to associated content
    """
    
    __tablename__ = "media"
    
    # Override id from base class to use UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional foreign key to content",
    )
    
    media_type: Mapped[MediaType] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    
    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    
    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        index=True,
    )
    
    storage_path: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Path in storage system (e.g., S3 key)",
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes",
    )
    
    mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Width in pixels (for images/videos)",
    )
    
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Height in pixels (for images/videos)",
    )
    
    duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Duration in seconds (for video/audio)",
    )
    
    meta: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSONB,
        nullable=True,
        default={},
        comment="Additional metadata as JSON",
    )
    
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Foreign key to Auth Service users table",
    )
    
    # Relationships
    content: Mapped[Optional["Content"]] = relationship(
        "Content",
        back_populates="media",
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_media_type_content", "media_type", "content_id"),
        Index("idx_uploaded_by_created", "uploaded_by", "created_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of Media."""
        return (
            f"<Media(id={self.id}, filename='{self.filename}', "
            f"type={self.media_type}, content_id={self.content_id})>"
        )
