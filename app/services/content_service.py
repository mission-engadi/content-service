"""Content service layer for business logic.

Provides CRUD operations and business logic for content management.
"""

import uuid
from datetime import datetime
from typing import Optional
from math import ceil

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.content import Content, ContentStatus, ContentType
from app.schemas.content import ContentCreate, ContentUpdate


class ContentService:
    """Service class for content operations."""
    
    @staticmethod
    async def create_content(
        db: AsyncSession,
        content_data: ContentCreate,
        author_id: uuid.UUID,
    ) -> Content:
        """Create new content.
        
        Args:
            db: Database session
            content_data: Content data from request
            author_id: UUID of the content author
        
        Returns:
            Created content object
        
        Raises:
            HTTPException: If slug already exists
        """
        # Check if slug already exists
        existing = await ContentService.get_content_by_slug(
            db, content_data.slug, content_data.language
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content with slug '{content_data.slug}' already exists for language '{content_data.language}'",
            )
        
        # Create content
        db_content = Content(
            **content_data.model_dump(),
            author_id=author_id,
        )
        
        db.add(db_content)
        await db.flush()
        await db.refresh(db_content)
        
        return db_content
    
    @staticmethod
    async def get_content(
        db: AsyncSession,
        content_id: uuid.UUID,
        include_relations: bool = False,
    ) -> Optional[Content]:
        """Get content by ID.
        
        Args:
            db: Database session
            content_id: UUID of the content
            include_relations: Whether to include translations and media
        
        Returns:
            Content object or None if not found
        """
        query = select(Content).where(Content.id == content_id)
        
        if include_relations:
            query = query.options(
                selectinload(Content.translations),
                selectinload(Content.media),
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_content_by_slug(
        db: AsyncSession,
        slug: str,
        language: str = "en",
        include_relations: bool = False,
    ) -> Optional[Content]:
        """Get content by slug and language.
        
        Args:
            db: Database session
            slug: Content slug
            language: Language code
            include_relations: Whether to include translations and media
        
        Returns:
            Content object or None if not found
        """
        query = select(Content).where(
            and_(
                Content.slug == slug,
                Content.language == language,
            )
        )
        
        if include_relations:
            query = query.options(
                selectinload(Content.translations),
                selectinload(Content.media),
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_content(
        db: AsyncSession,
        content_type: Optional[ContentType] = None,
        status: Optional[ContentStatus] = None,
        language: Optional[str] = None,
        tags: Optional[list[str]] = None,
        author_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
        published_only: bool = False,
    ) -> tuple[list[Content], int]:
        """List content with filters and pagination.
        
        Args:
            db: Database session
            content_type: Filter by content type
            status: Filter by status
            language: Filter by language
            tags: Filter by tags (any match)
            author_id: Filter by author
            search: Search in title and body
            skip: Number of items to skip
            limit: Maximum number of items to return
            published_only: Only return published content
        
        Returns:
            Tuple of (content list, total count)
        """
        # Build query
        query = select(Content)
        count_query = select(func.count(Content.id))
        
        # Apply filters
        filters = []
        
        if content_type:
            filters.append(Content.content_type == content_type)
        
        if status:
            filters.append(Content.status == status)
        elif published_only:
            filters.append(Content.status == ContentStatus.PUBLISHED)
        
        if language:
            filters.append(Content.language == language)
        
        if author_id:
            filters.append(Content.author_id == author_id)
        
        if tags:
            # Match any of the provided tags
            filters.append(Content.tags.overlap(tags))
        
        if search:
            # Search in title and body
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    Content.title.ilike(search_pattern),
                    Content.body.ilike(search_pattern),
                )
            )
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()
        
        # Apply ordering (most recent published first, then most recent updated)
        query = query.order_by(
            Content.published_at.desc().nullslast(),
            Content.updated_at.desc(),
        )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    @staticmethod
    async def update_content(
        db: AsyncSession,
        content_id: uuid.UUID,
        update_data: ContentUpdate,
        user_id: uuid.UUID,
    ) -> Content:
        """Update content.
        
        Args:
            db: Database session
            content_id: UUID of the content to update
            update_data: Update data
            user_id: UUID of the user performing the update
        
        Returns:
            Updated content object
        
        Raises:
            HTTPException: If content not found or user not authorized
        """
        # Get content
        content = await ContentService.get_content(db, content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found",
            )
        
        # Check authorization (only author can update)
        # TODO: Add admin/editor role check
        if content.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this content",
            )
        
        # Check if slug is being changed and if it already exists
        if update_data.slug and update_data.slug != content.slug:
            language = update_data.language or content.language
            existing = await ContentService.get_content_by_slug(
                db, update_data.slug, language
            )
            if existing and existing.id != content_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Content with slug '{update_data.slug}' already exists",
                )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(content, field, value)
        
        await db.flush()
        await db.refresh(content)
        
        return content
    
    @staticmethod
    async def delete_content(
        db: AsyncSession,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Soft delete content by setting status to archived.
        
        Args:
            db: Database session
            content_id: UUID of the content to delete
            user_id: UUID of the user performing the deletion
        
        Raises:
            HTTPException: If content not found or user not authorized
        """
        # Get content
        content = await ContentService.get_content(db, content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found",
            )
        
        # Check authorization (only author can delete)
        # TODO: Add admin role check
        if content.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this content",
            )
        
        # Soft delete by setting status to archived
        content.status = ContentStatus.ARCHIVED
        
        await db.flush()
    
    @staticmethod
    async def change_status(
        db: AsyncSession,
        content_id: uuid.UUID,
        new_status: ContentStatus,
        user_id: uuid.UUID,
    ) -> Content:
        """Change content status.
        
        Args:
            db: Database session
            content_id: UUID of the content
            new_status: New status to set
            user_id: UUID of the user performing the change
        
        Returns:
            Updated content object
        
        Raises:
            HTTPException: If content not found or user not authorized
        """
        # Get content
        content = await ContentService.get_content(db, content_id)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Content not found",
            )
        
        # Check authorization
        # TODO: Add role-based checks for different status transitions
        if content.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change status of this content",
            )
        
        # Validate status transition
        valid_transitions = {
            ContentStatus.DRAFT: [ContentStatus.REVIEW, ContentStatus.PUBLISHED],
            ContentStatus.REVIEW: [ContentStatus.DRAFT, ContentStatus.PUBLISHED, ContentStatus.ARCHIVED],
            ContentStatus.PUBLISHED: [ContentStatus.ARCHIVED],
            ContentStatus.ARCHIVED: [ContentStatus.DRAFT],
        }
        
        if new_status not in valid_transitions.get(content.status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {content.status} to {new_status}",
            )
        
        # Update status
        content.status = new_status
        
        # If publishing, set published_at timestamp
        if new_status == ContentStatus.PUBLISHED and not content.published_at:
            content.published_at = datetime.utcnow()
        
        await db.flush()
        await db.refresh(content)
        
        return content
    
    @staticmethod
    async def publish_content(
        db: AsyncSession,
        content_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Content:
        """Publish content.
        
        Args:
            db: Database session
            content_id: UUID of the content to publish
            user_id: UUID of the user performing the publish
        
        Returns:
            Published content object
        
        Raises:
            HTTPException: If content not found or user not authorized
        """
        return await ContentService.change_status(
            db, content_id, ContentStatus.PUBLISHED, user_id
        )
    
    @staticmethod
    async def get_content_with_translations(
        db: AsyncSession,
        content_id: uuid.UUID,
    ) -> Optional[Content]:
        """Get content with all translations.
        
        Args:
            db: Database session
            content_id: UUID of the content
        
        Returns:
            Content with translations or None if not found
        """
        return await ContentService.get_content(db, content_id, include_relations=True)
    
    @staticmethod
    async def get_content_with_media(
        db: AsyncSession,
        content_id: uuid.UUID,
    ) -> Optional[Content]:
        """Get content with associated media.
        
        Args:
            db: Database session
            content_id: UUID of the content
        
        Returns:
            Content with media or None if not found
        """
        return await ContentService.get_content(db, content_id, include_relations=True)
