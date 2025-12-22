"""Media service layer for business logic.

Handles media upload, processing, storage, and retrieval operations.
"""

import uuid
import os
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import UploadFile, HTTPException, status

from app.models.media import Media, MediaType
from app.schemas.media import MediaCreate, MediaUpdate
from app.core.storage import StorageManager
from app.core.file_processing import (
    validate_file,
    process_image,
    generate_thumbnail,
    extract_image_metadata,
    get_mime_type,
)
from app.core.config import settings


class MediaService:
    """Service for managing media operations."""
    
    def __init__(self, db: AsyncSession):
        """Initialize media service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.storage = StorageManager()
    
    async def upload_media(
        self,
        file: UploadFile,
        media_type: MediaType,
        user_id: uuid.UUID,
        content_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Media:
        """Upload and process media file.
        
        Args:
            file: Uploaded file
            media_type: Type of media (image, video, audio, document)
            user_id: User uploading the media
            content_id: Optional content to associate with
            metadata: Additional metadata
            
        Returns:
            Created media record
            
        Raises:
            HTTPException: If file validation or processing fails
        """
        # Validate file
        if not validate_file(file, media_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for {media_type.value}"
            )
        
        try:
            # Save file to storage
            storage_path, file_url = await self.storage.save_file(file)
            
            # Get file size
            file.file.seek(0, os.SEEK_END)
            file_size = file.file.tell()
            file.file.seek(0)
            
            # Get MIME type
            mime_type = get_mime_type(file)
            
            # Initialize dimensions and duration
            width = None
            height = None
            duration = None
            
            # Process based on media type
            if media_type == MediaType.IMAGE:
                # Process image (resize/optimize)
                full_path = self.storage.get_full_path(storage_path)
                processed_path = await process_image(full_path)
                
                # Extract image metadata
                image_metadata = extract_image_metadata(processed_path)
                width = image_metadata.get("width")
                height = image_metadata.get("height")
                
                # Generate thumbnail
                thumbnail_path = await generate_thumbnail(processed_path)
                if metadata is None:
                    metadata = {}
                metadata["thumbnail_path"] = thumbnail_path
            
            # Create media record
            media_data = {
                "content_id": content_id,
                "media_type": media_type,
                "filename": file.filename,
                "url": file_url,
                "storage_path": storage_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "width": width,
                "height": height,
                "duration": duration,
                "meta": metadata or {},
                "uploaded_by": user_id,
            }
            
            media = Media(**media_data)
            self.db.add(media)
            await self.db.commit()
            await self.db.refresh(media)
            
            return media
            
        except Exception as e:
            # Clean up uploaded file on error
            if 'storage_path' in locals():
                await self.storage.delete_file(storage_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload media: {str(e)}"
            )
    
    async def get_media(self, media_id: uuid.UUID) -> Optional[Media]:
        """Get media by ID.
        
        Args:
            media_id: Media ID
            
        Returns:
            Media record or None if not found
        """
        result = await self.db.execute(
            select(Media)
            .where(Media.id == media_id)
            .options(selectinload(Media.content))
        )
        return result.scalar_one_or_none()
    
    async def get_media_for_content(
        self,
        content_id: uuid.UUID,
        media_type: Optional[MediaType] = None,
    ) -> List[Media]:
        """Get all media for a specific content.
        
        Args:
            content_id: Content ID
            media_type: Optional filter by media type
            
        Returns:
            List of media records
        """
        query = select(Media).where(Media.content_id == content_id)
        
        if media_type:
            query = query.where(Media.media_type == media_type)
        
        query = query.order_by(Media.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_media(
        self,
        media_type: Optional[MediaType] = None,
        uploaded_by: Optional[uuid.UUID] = None,
        content_id: Optional[uuid.UUID] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Media], int]:
        """List media with filters and pagination.
        
        Args:
            media_type: Filter by media type
            uploaded_by: Filter by uploader
            content_id: Filter by content ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple of (media list, total count)
        """
        # Build filters
        filters = []
        if media_type:
            filters.append(Media.media_type == media_type)
        if uploaded_by:
            filters.append(Media.uploaded_by == uploaded_by)
        if content_id:
            filters.append(Media.content_id == content_id)
        
        # Count query
        count_query = select(func.count(Media.id))
        if filters:
            count_query = count_query.where(and_(*filters))
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Data query
        query = select(Media)
        if filters:
            query = query.where(and_(*filters))
        
        query = (
            query
            .order_by(Media.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        media_list = list(result.scalars().all())
        
        return media_list, total
    
    async def update_media(
        self,
        media_id: uuid.UUID,
        update_data: MediaUpdate,
        user_id: uuid.UUID,
    ) -> Optional[Media]:
        """Update media metadata.
        
        Args:
            media_id: Media ID
            update_data: Update data
            user_id: User making the update
            
        Returns:
            Updated media or None if not found
            
        Raises:
            HTTPException: If user doesn't have permission
        """
        media = await self.get_media(media_id)
        
        if not media:
            return None
        
        # Check permission (only uploader can update)
        if media.uploaded_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this media"
            )
        
        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, value in update_dict.items():
            # Map metadata field to meta (database column)
            if field == "metadata":
                setattr(media, "meta", value)
            else:
                setattr(media, field, value)
        
        await self.db.commit()
        await self.db.refresh(media)
        
        return media
    
    async def delete_media(
        self,
        media_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete media file and record.
        
        Args:
            media_id: Media ID
            user_id: User making the deletion
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            HTTPException: If user doesn't have permission
        """
        media = await self.get_media(media_id)
        
        if not media:
            return False
        
        # Check permission (only uploader can delete)
        if media.uploaded_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this media"
            )
        
        # Delete file from storage
        if media.storage_path:
            try:
                await self.storage.delete_file(media.storage_path)
            except Exception as e:
                # Log error but continue with database deletion
                print(f"Failed to delete file from storage: {e}")
        
        # Delete thumbnail if exists
        if media.meta and "thumbnail_path" in media.meta:
            try:
                await self.storage.delete_file(media.meta["thumbnail_path"])
            except Exception:
                pass
        
        # Delete database record
        await self.db.delete(media)
        await self.db.commit()
        
        return True
