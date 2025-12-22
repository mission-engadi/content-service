"""Media management API endpoints.

Provides endpoints for uploading, downloading, and managing media files.
"""

import uuid
from typing import Optional, List
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user, get_optional_user, CurrentUser
from app.schemas.media import MediaResponse, MediaList, MediaUpdate
from app.models.media import MediaType
from app.services.media_service import MediaService
from app.core.storage import StorageManager
from app.core.config import settings

router = APIRouter()


@router.post(
    "/upload",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload media file",
    description="Upload a media file (image, video, audio, document) with optional content association",
)
async def upload_media(
    file: UploadFile = File(..., description="File to upload"),
    media_type: MediaType = Form(..., description="Type of media"),
    content_id: Optional[str] = Form(None, description="Optional content ID to associate with"),
    metadata: Optional[str] = Form(None, description="Optional metadata as JSON string"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MediaResponse:
    """Upload a media file.
    
    Requires authentication. Validates file type and size, processes the file
    (e.g., resizes images, generates thumbnails), and stores it.
    
    Args:
        file: File to upload
        media_type: Type of media (image, video, audio, document)
        content_id: Optional content ID to associate with
        metadata: Optional metadata as JSON string
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created media record with URL
        
    Raises:
        HTTPException: If file validation fails or upload fails
    """
    # Parse content_id if provided
    parsed_content_id = None
    if content_id:
        try:
            parsed_content_id = uuid.UUID(content_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content_id format"
            )
    
    # Parse metadata if provided
    parsed_metadata = None
    if metadata:
        try:
            import json
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON format"
            )
    
    # Upload media
    service = MediaService(db)
    media = await service.upload_media(
        file=file,
        media_type=media_type,
        user_id=current_user.user_id,
        content_id=parsed_content_id,
        metadata=parsed_metadata,
    )
    
    return MediaResponse.model_validate(media)


@router.post(
    "/content/{content_id}/upload",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload media for content",
    description="Upload a media file and associate it with specific content",
)
async def upload_media_for_content(
    content_id: uuid.UUID,
    file: UploadFile = File(..., description="File to upload"),
    media_type: MediaType = Form(..., description="Type of media"),
    metadata: Optional[str] = Form(None, description="Optional metadata as JSON string"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MediaResponse:
    """Upload a media file for specific content.
    
    Requires authentication. Automatically associates the media with the specified content.
    
    Args:
        content_id: Content ID to associate with
        file: File to upload
        media_type: Type of media
        metadata: Optional metadata as JSON string
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created media record
    """
    # Parse metadata if provided
    parsed_metadata = None
    if metadata:
        try:
            import json
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON format"
            )
    
    # Upload media
    service = MediaService(db)
    media = await service.upload_media(
        file=file,
        media_type=media_type,
        user_id=current_user.user_id,
        content_id=content_id,
        metadata=parsed_metadata,
    )
    
    return MediaResponse.model_validate(media)


@router.get(
    "/{media_id}",
    response_model=MediaResponse,
    summary="Get media by ID",
    description="Retrieve media metadata by ID",
)
async def get_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MediaResponse:
    """Get media metadata by ID.
    
    Public endpoint. Returns media metadata including URL.
    
    Args:
        media_id: Media ID
        db: Database session
        
    Returns:
        Media record
        
    Raises:
        HTTPException: If media not found
    """
    service = MediaService(db)
    media = await service.get_media(media_id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    return MediaResponse.model_validate(media)


@router.get(
    "/{media_id}/download",
    response_class=FileResponse,
    summary="Download media file",
    description="Download the actual media file",
)
async def download_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download media file.
    
    Public endpoint. Returns the actual file with proper content-type headers.
    
    Args:
        media_id: Media ID
        db: Database session
        
    Returns:
        File response with the media file
        
    Raises:
        HTTPException: If media not found or file doesn't exist
    """
    service = MediaService(db)
    media = await service.get_media(media_id)
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    # Get file path
    storage = StorageManager()
    file_path = storage.get_full_path(media.storage_path)
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found in storage"
        )
    
    # Return file
    return FileResponse(
        path=file_path,
        filename=media.filename,
        media_type=media.mime_type,
    )


@router.get(
    "/content/{content_id}/media",
    response_model=List[MediaResponse],
    summary="Get all media for content",
    description="Retrieve all media files associated with specific content",
)
async def get_content_media(
    content_id: uuid.UUID,
    media_type: Optional[MediaType] = Query(None, description="Filter by media type"),
    db: AsyncSession = Depends(get_db),
) -> List[MediaResponse]:
    """Get all media for specific content.
    
    Public endpoint. Returns list of media associated with the content.
    
    Args:
        content_id: Content ID
        media_type: Optional filter by media type
        db: Database session
        
    Returns:
        List of media records
    """
    service = MediaService(db)
    media_list = await service.get_media_for_content(
        content_id=content_id,
        media_type=media_type,
    )
    
    return [MediaResponse.model_validate(m) for m in media_list]


@router.get(
    "/",
    response_model=MediaList,
    summary="List all media",
    description="List all media files with pagination and filters",
)
async def list_media(
    media_type: Optional[MediaType] = Query(None, description="Filter by media type"),
    uploaded_by: Optional[uuid.UUID] = Query(None, description="Filter by uploader"),
    content_id: Optional[uuid.UUID] = Query(None, description="Filter by content ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MediaList:
    """List all media with pagination and filters.
    
    Requires authentication. Returns paginated list of media.
    
    Args:
        media_type: Filter by media type
        uploaded_by: Filter by uploader
        content_id: Filter by content ID
        page: Page number (1-based)
        page_size: Items per page
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Paginated list of media
    """
    skip = (page - 1) * page_size
    
    service = MediaService(db)
    media_list, total = await service.list_media(
        media_type=media_type,
        uploaded_by=uploaded_by,
        content_id=content_id,
        skip=skip,
        limit=page_size,
    )
    
    # Calculate total pages
    pages = (total + page_size - 1) // page_size
    
    return MediaList(
        items=[MediaResponse.model_validate(m) for m in media_list],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.put(
    "/{media_id}",
    response_model=MediaResponse,
    summary="Update media metadata",
    description="Update media metadata (filename, metadata only, not the file itself)",
)
async def update_media(
    media_id: uuid.UUID,
    update_data: MediaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> MediaResponse:
    """Update media metadata.
    
    Requires authentication. Only the uploader can update their media.
    
    Args:
        media_id: Media ID
        update_data: Update data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated media record
        
    Raises:
        HTTPException: If media not found or user doesn't have permission
    """
    service = MediaService(db)
    media = await service.update_media(
        media_id=media_id,
        update_data=update_data,
        user_id=current_user.user_id,
    )
    
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    return MediaResponse.model_validate(media)


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete media",
    description="Delete media file and database record",
)
async def delete_media(
    media_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """Delete media.
    
    Requires authentication. Only the uploader can delete their media.
    Deletes both the file from storage and the database record.
    
    Args:
        media_id: Media ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If media not found or user doesn't have permission
    """
    service = MediaService(db)
    deleted = await service.delete_media(
        media_id=media_id,
        user_id=current_user.user_id,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found"
        )
    
    return {"message": "Media deleted successfully"}


# Additional endpoint for serving static files
@router.get(
    "/files/{file_path:path}",
    response_class=FileResponse,
    summary="Serve media file",
    description="Serve media file from storage (internal endpoint)",
    include_in_schema=False,  # Hide from docs
)
async def serve_media_file(
    file_path: str,
) -> FileResponse:
    """Serve media file from storage.
    
    Internal endpoint for serving files. Not shown in API docs.
    
    Args:
        file_path: Relative file path in storage
        
    Returns:
        File response
        
    Raises:
        HTTPException: If file not found
    """
    storage = StorageManager()
    full_path = storage.get_full_path(file_path)
    
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(path=full_path)
