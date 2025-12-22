"""Content API endpoints.

Provides REST API endpoints for content management with CRUD operations,
workflow management, and multi-language support.
"""

import uuid
from typing import Optional
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import CurrentUser, get_current_active_user, get_optional_user
from app.dependencies.database import get_db
from app.models.content import ContentType, ContentStatus
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentFull,
    ContentList,
)
from app.services.content_service import ContentService

router = APIRouter()


@router.post(
    "",
    response_model=ContentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new content",
    description="Create a new content item. Requires authentication. Author is automatically set from the authenticated user.",
)
async def create_content(
    content_data: ContentCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ContentResponse:
    """Create new content.
    
    Args:
        content_data: Content creation data
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Created content
    """
    content = await ContentService.create_content(
        db=db,
        content_data=content_data,
        author_id=current_user.user_id,
    )
    
    return ContentResponse.model_validate(content)


@router.get(
    "/{content_id}",
    response_model=ContentFull,
    summary="Get content by ID",
    description="Get a content item by its ID. Includes translations and media. Public endpoint - authentication optional. Only published content is returned for unauthenticated users.",
)
async def get_content_by_id(
    content_id: uuid.UUID,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ContentFull:
    """Get content by ID with all related data.
    
    Args:
        content_id: UUID of the content
        current_user: Optional authenticated user
        db: Database session
    
    Returns:
        Content with translations and media
    
    Raises:
        HTTPException: If content not found or not accessible
    """
    content = await ContentService.get_content_with_translations(db, content_id)
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    # Check access permissions
    # Non-authenticated users can only see published content
    if not current_user and content.status != ContentStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    # Authenticated users can see their own content regardless of status
    # or published content from others
    if current_user:
        is_author = content.author_id == current_user.user_id
        is_published = content.status == ContentStatus.PUBLISHED
        
        if not (is_author or is_published or current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this content",
            )
    
    return ContentFull.model_validate(content)


@router.get(
    "/slug/{slug}",
    response_model=ContentFull,
    summary="Get content by slug",
    description="Get a content item by its slug and language. Public endpoint - authentication optional.",
)
async def get_content_by_slug(
    slug: str,
    language: str = Query(default="en", description="Content language code"),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ContentFull:
    """Get content by slug and language.
    
    Args:
        slug: Content slug
        language: Language code (default: en)
        current_user: Optional authenticated user
        db: Database session
    
    Returns:
        Content with translations and media
    
    Raises:
        HTTPException: If content not found or not accessible
    """
    content = await ContentService.get_content_by_slug(
        db, slug, language, include_relations=True
    )
    
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content with slug '{slug}' not found for language '{language}'",
        )
    
    # Check access permissions (same logic as get by ID)
    if not current_user and content.status != ContentStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    
    if current_user:
        is_author = content.author_id == current_user.user_id
        is_published = content.status == ContentStatus.PUBLISHED
        
        if not (is_author or is_published or current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this content",
            )
    
    return ContentFull.model_validate(content)


@router.get(
    "",
    response_model=ContentList,
    summary="List content",
    description="List content with filters and pagination. Public endpoint - authentication optional. Unauthenticated users only see published content.",
)
async def list_content(
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    status_filter: Optional[ContentStatus] = Query(None, alias="status", description="Filter by status"),
    language: Optional[str] = Query(None, description="Filter by language code"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    author_id: Optional[uuid.UUID] = Query(None, description="Filter by author UUID"),
    search: Optional[str] = Query(None, description="Search in title and body"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ContentList:
    """List content with filters and pagination.
    
    Args:
        content_type: Filter by content type
        status_filter: Filter by status
        language: Filter by language
        tags: Comma-separated tags to filter
        author_id: Filter by author
        search: Search query
        page: Page number (1-based)
        page_size: Items per page
        current_user: Optional authenticated user
        db: Database session
    
    Returns:
        Paginated list of content
    """
    # Parse tags if provided
    tags_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Determine if we should only show published content
    # Unauthenticated users always see only published content
    # Authenticated users can see all statuses if they filter by status
    # or their own content
    published_only = not current_user
    
    # If user is filtering by their own content, allow all statuses
    if current_user and author_id == current_user.user_id:
        published_only = False
    
    # If superuser, allow all
    if current_user and current_user.is_superuser:
        published_only = False
    
    # Get content list
    items, total = await ContentService.list_content(
        db=db,
        content_type=content_type,
        status=status_filter,
        language=language,
        tags=tags_list,
        author_id=author_id,
        search=search,
        skip=skip,
        limit=page_size,
        published_only=published_only,
    )
    
    # Calculate pagination
    pages = ceil(total / page_size) if total > 0 else 0
    
    return ContentList(
        items=[ContentResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.put(
    "/{content_id}",
    response_model=ContentResponse,
    summary="Update content",
    description="Update a content item. Requires authentication. Only the author can update their content.",
)
async def update_content(
    content_id: uuid.UUID,
    update_data: ContentUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ContentResponse:
    """Update content.
    
    Args:
        content_id: UUID of the content to update
        update_data: Update data
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Updated content
    
    Raises:
        HTTPException: If content not found or user not authorized
    """
    content = await ContentService.update_content(
        db=db,
        content_id=content_id,
        update_data=update_data,
        user_id=current_user.user_id,
    )
    
    return ContentResponse.model_validate(content)


@router.delete(
    "/{content_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete content",
    description="Soft delete content by setting status to archived. Requires authentication. Only the author can delete their content.",
)
async def delete_content(
    content_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete (archive) content.
    
    Args:
        content_id: UUID of the content to delete
        current_user: Authenticated user
        db: Database session
    
    Raises:
        HTTPException: If content not found or user not authorized
    """
    await ContentService.delete_content(
        db=db,
        content_id=content_id,
        user_id=current_user.user_id,
    )


@router.post(
    "/{content_id}/publish",
    response_model=ContentResponse,
    summary="Publish content",
    description="Publish content by changing status to published. Requires authentication. Only the author can publish their content.",
)
async def publish_content(
    content_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ContentResponse:
    """Publish content.
    
    Args:
        content_id: UUID of the content to publish
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Published content
    
    Raises:
        HTTPException: If content not found, user not authorized, or invalid status transition
    """
    content = await ContentService.publish_content(
        db=db,
        content_id=content_id,
        user_id=current_user.user_id,
    )
    
    return ContentResponse.model_validate(content)


@router.post(
    "/{content_id}/status",
    response_model=ContentResponse,
    summary="Change content status",
    description="Change content status with workflow validation. Requires authentication. Only the author can change status.",
)
async def change_content_status(
    content_id: uuid.UUID,
    new_status: ContentStatus = Query(..., description="New status to set"),
    current_user: CurrentUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ContentResponse:
    """Change content status.
    
    Args:
        content_id: UUID of the content
        new_status: New status to set
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Updated content
    
    Raises:
        HTTPException: If content not found, user not authorized, or invalid status transition
    """
    content = await ContentService.change_status(
        db=db,
        content_id=content_id,
        new_status=new_status,
        user_id=current_user.user_id,
    )
    
    return ContentResponse.model_validate(content)
