"""Translation management endpoints.

Provides REST API endpoints for managing content translations.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_active_user, get_optional_user, CurrentUser
from app.schemas.translation import (
    TranslationCreate,
    TranslationUpdate,
    TranslationResponse,
)
from app.models.translation import TranslationStatus
from app.services.translation_service import TranslationService
from app.core.languages import SUPPORTED_LANGUAGES

router = APIRouter()


@router.post(
    "/{content_id}/translations",
    response_model=TranslationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new translation",
    description="Create a new translation for a specific content. Requires authentication.",
)
async def create_translation(
    content_id: uuid.UUID,
    translation_data: TranslationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> TranslationResponse:
    """Create a new translation for content.
    
    Args:
        content_id: UUID of the content to translate
        translation_data: Translation data (language, title, body, slug)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Created translation object
        
    Raises:
        HTTPException: If content not found or translation already exists
    """
    # Ensure content_id in translation_data matches path parameter
    translation_data.content_id = content_id
    
    translation = await TranslationService.create_translation(
        db=db,
        content_id=content_id,
        translation_data=translation_data,
        translator_id=current_user.user_id,
    )
    
    return TranslationResponse.model_validate(translation)


@router.get(
    "/{content_id}/translations",
    response_model=list[TranslationResponse],
    summary="Get all translations for content",
    description="Get all translations for a specific content. Public endpoint returns only completed/reviewed translations.",
)
async def get_content_translations(
    content_id: uuid.UUID,
    status_filter: Optional[TranslationStatus] = Query(
        None,
        description="Filter translations by status",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
) -> list[TranslationResponse]:
    """Get all translations for a specific content.
    
    Args:
        content_id: UUID of the content
        status_filter: Optional status filter
        db: Database session
        current_user: Optional authenticated user
        
    Returns:
        List of translation objects
    """
    # For non-authenticated users, only return completed or reviewed translations
    if not current_user and not status_filter:
        status_filter = TranslationStatus.REVIEWED
    
    translations = await TranslationService.get_translations_for_content(
        db=db,
        content_id=content_id,
        status_filter=status_filter,
    )
    
    # If no reviewed translations found for public, try completed
    if not current_user and not translations and status_filter == TranslationStatus.REVIEWED:
        translations = await TranslationService.get_translations_for_content(
            db=db,
            content_id=content_id,
            status_filter=TranslationStatus.COMPLETED,
        )
    
    return [TranslationResponse.model_validate(t) for t in translations]


@router.get(
    "/{content_id}/translations/{language}",
    response_model=TranslationResponse,
    summary="Get translation by language",
    description="Get a specific language translation for content. Returns 404 if not found.",
)
async def get_translation_by_language(
    content_id: uuid.UUID,
    language: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
) -> TranslationResponse:
    """Get a specific language translation for content.
    
    Args:
        content_id: UUID of the content
        language: Language code (en, es, fr, pt-br)
        db: Database session
        current_user: Optional authenticated user
        
    Returns:
        Translation object
        
    Raises:
        HTTPException: If translation not found
    """
    translation = await TranslationService.get_translation_by_language(
        db=db,
        content_id=content_id,
        language=language,
    )
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation for language '{language}' not found for this content",
        )
    
    # For non-authenticated users, only return completed or reviewed translations
    if not current_user:
        if translation.translation_status not in [
            TranslationStatus.COMPLETED,
            TranslationStatus.REVIEWED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation for language '{language}' not found for this content",
            )
    
    return TranslationResponse.model_validate(translation)


@router.get(
    "/translations/{translation_id}",
    response_model=TranslationResponse,
    summary="Get translation by ID",
    description="Get a translation by its unique identifier.",
)
async def get_translation(
    translation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
) -> TranslationResponse:
    """Get a translation by ID.
    
    Args:
        translation_id: UUID of the translation
        db: Database session
        current_user: Optional authenticated user
        
    Returns:
        Translation object
        
    Raises:
        HTTPException: If translation not found
    """
    translation = await TranslationService.get_translation(
        db=db,
        translation_id=translation_id,
    )
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation with id '{translation_id}' not found",
        )
    
    # For non-authenticated users, only return completed or reviewed translations
    if not current_user:
        if translation.translation_status not in [
            TranslationStatus.COMPLETED,
            TranslationStatus.REVIEWED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with id '{translation_id}' not found",
            )
    
    return TranslationResponse.model_validate(translation)


@router.put(
    "/translations/{translation_id}",
    response_model=TranslationResponse,
    summary="Update a translation",
    description="Update a translation. Requires authentication. Only translator or admin can update.",
)
async def update_translation(
    translation_id: uuid.UUID,
    update_data: TranslationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> TranslationResponse:
    """Update a translation.
    
    Args:
        translation_id: UUID of the translation to update
        update_data: Updated translation data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated translation object
        
    Raises:
        HTTPException: If translation not found or user not authorized
    """
    # Get translation to check ownership
    translation = await TranslationService.get_translation(db, translation_id)
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation with id '{translation_id}' not found",
        )
    
    # Check authorization (translator or superuser can update)
    if not current_user.is_superuser:
        if translation.translator_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this translation",
            )
    
    updated_translation = await TranslationService.update_translation(
        db=db,
        translation_id=translation_id,
        update_data=update_data,
        user_id=current_user.user_id,
    )
    
    return TranslationResponse.model_validate(updated_translation)


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a translation",
    description="Delete a translation. Requires authentication. Only translator or admin can delete.",
)
async def delete_translation(
    translation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> dict:
    """Delete a translation.
    
    Args:
        translation_id: UUID of the translation to delete
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If translation not found or user not authorized
    """
    # Get translation to check ownership
    translation = await TranslationService.get_translation(db, translation_id)
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation with id '{translation_id}' not found",
        )
    
    # Check authorization (translator or superuser can delete)
    if not current_user.is_superuser:
        if translation.translator_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this translation",
            )
    
    return await TranslationService.delete_translation(
        db=db,
        translation_id=translation_id,
        user_id=current_user.user_id,
    )


@router.post(
    "/translations/{translation_id}/status",
    response_model=TranslationResponse,
    summary="Change translation status",
    description="Change the status of a translation. Validates status transitions.",
)
async def change_translation_status(
    translation_id: uuid.UUID,
    new_status: TranslationStatus = Query(
        ...,
        description="New translation status",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> TranslationResponse:
    """Change the status of a translation.
    
    Args:
        translation_id: UUID of the translation
        new_status: New translation status
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated translation object
        
    Raises:
        HTTPException: If translation not found or status transition invalid
    """
    # Get translation to check ownership
    translation = await TranslationService.get_translation(db, translation_id)
    
    if not translation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Translation with id '{translation_id}' not found",
        )
    
    # Check authorization (translator or superuser can change status)
    if not current_user.is_superuser:
        if translation.translator_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to change this translation's status",
            )
    
    updated_translation = await TranslationService.change_translation_status(
        db=db,
        translation_id=translation_id,
        new_status=new_status,
        user_id=current_user.user_id,
    )
    
    return TranslationResponse.model_validate(updated_translation)


@router.get(
    "/{content_id}/languages",
    summary="Get available languages",
    description="Get list of available and missing languages for content.",
)
async def get_available_languages(
    content_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get available and missing languages for content.
    
    Args:
        content_id: UUID of the content
        db: Database session
        
    Returns:
        Dictionary with 'available' and 'missing' language lists
    """
    return await TranslationService.get_available_languages(
        db=db,
        content_id=content_id,
    )


@router.post(
    "/{content_id}/translations/bulk",
    response_model=list[TranslationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create bulk translations",
    description="Create placeholder translations for multiple languages at once.",
)
async def create_bulk_translations(
    content_id: uuid.UUID,
    languages: list[str] = Query(
        ...,
        description="List of language codes to create translations for",
        example=["es", "fr", "pt-br"],
    ),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user),
) -> list[TranslationResponse]:
    """Create placeholder translations for multiple languages.
    
    Args:
        content_id: UUID of the content
        languages: List of language codes
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of created translation objects
        
    Raises:
        HTTPException: If content not found or any language invalid
    """
    translations = await TranslationService.bulk_create_translations(
        db=db,
        content_id=content_id,
        languages=languages,
        user_id=current_user.user_id,
    )
    
    return [TranslationResponse.model_validate(t) for t in translations]
