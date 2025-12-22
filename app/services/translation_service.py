"""Translation service layer for business logic.

Provides CRUD operations and workflow management for translations.
"""

import uuid
from typing import Optional
from math import ceil

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.translation import Translation, TranslationStatus
from app.models.content import Content
from app.schemas.translation import TranslationCreate, TranslationUpdate
from app.core.languages import validate_language, SUPPORTED_LANGUAGES, get_missing_languages


class TranslationService:
    """Service class for translation operations."""
    
    # Valid status transitions
    STATUS_TRANSITIONS = {
        TranslationStatus.PENDING: [
            TranslationStatus.IN_PROGRESS,
            TranslationStatus.PENDING,
        ],
        TranslationStatus.IN_PROGRESS: [
            TranslationStatus.COMPLETED,
            TranslationStatus.PENDING,
            TranslationStatus.IN_PROGRESS,
        ],
        TranslationStatus.COMPLETED: [
            TranslationStatus.REVIEWED,
            TranslationStatus.IN_PROGRESS,
            TranslationStatus.PENDING,
            TranslationStatus.COMPLETED,
        ],
        TranslationStatus.REVIEWED: [
            TranslationStatus.IN_PROGRESS,
            TranslationStatus.PENDING,
            TranslationStatus.REVIEWED,
        ],
    }
    
    @staticmethod
    async def create_translation(
        db: AsyncSession,
        content_id: uuid.UUID,
        translation_data: TranslationCreate,
        translator_id: Optional[uuid.UUID] = None,
    ) -> Translation:
        """Create a new translation.
        
        Args:
            db: Database session
            content_id: UUID of the content to translate
            translation_data: Translation data from request
            translator_id: UUID of the translator
            
        Returns:
            Created translation object
            
        Raises:
            HTTPException: If content not found or translation already exists
        """
        # Validate language code
        language = validate_language(translation_data.language)
        
        # Check if content exists
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with id '{content_id}' not found",
            )
        
        # Check if translation already exists for this language
        existing = await TranslationService.get_translation_by_language(
            db, content_id, language
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Translation for language '{language}' already exists for this content",
            )
        
        # Create translation
        translation = Translation(
            content_id=content_id,
            language=language,
            translated_title=translation_data.translated_title,
            translated_body=translation_data.translated_body,
            translated_slug=translation_data.translated_slug,
            translator_id=translator_id or translation_data.translator_id,
            translation_status=translation_data.translation_status or TranslationStatus.PENDING,
        )
        
        db.add(translation)
        await db.commit()
        await db.refresh(translation)
        
        return translation
    
    @staticmethod
    async def get_translation(
        db: AsyncSession,
        translation_id: uuid.UUID,
    ) -> Optional[Translation]:
        """Get a translation by ID.
        
        Args:
            db: Database session
            translation_id: UUID of the translation
            
        Returns:
            Translation object or None if not found
        """
        result = await db.execute(
            select(Translation).where(Translation.id == translation_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_translations_for_content(
        db: AsyncSession,
        content_id: uuid.UUID,
        status_filter: Optional[TranslationStatus] = None,
    ) -> list[Translation]:
        """Get all translations for a specific content.
        
        Args:
            db: Database session
            content_id: UUID of the content
            status_filter: Optional status filter
            
        Returns:
            List of translation objects
        """
        query = select(Translation).where(Translation.content_id == content_id)
        
        if status_filter:
            query = query.where(Translation.translation_status == status_filter)
        
        query = query.order_by(Translation.language)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_translation_by_language(
        db: AsyncSession,
        content_id: uuid.UUID,
        language: str,
    ) -> Optional[Translation]:
        """Get a specific language translation for content.
        
        Args:
            db: Database session
            content_id: UUID of the content
            language: Language code
            
        Returns:
            Translation object or None if not found
        """
        language = language.lower().strip()
        
        result = await db.execute(
            select(Translation).where(
                and_(
                    Translation.content_id == content_id,
                    Translation.language == language,
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_translation(
        db: AsyncSession,
        translation_id: uuid.UUID,
        update_data: TranslationUpdate,
        user_id: uuid.UUID,
    ) -> Translation:
        """Update a translation.
        
        Args:
            db: Database session
            translation_id: UUID of the translation to update
            update_data: Updated translation data
            user_id: UUID of the user making the update
            
        Returns:
            Updated translation object
            
        Raises:
            HTTPException: If translation not found or user not authorized
        """
        # Get existing translation
        translation = await TranslationService.get_translation(db, translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with id '{translation_id}' not found",
            )
        
        # Update fields if provided
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Validate language if being updated
        if "language" in update_dict:
            update_dict["language"] = validate_language(update_dict["language"])
        
        # Validate status transition if being updated
        if "translation_status" in update_dict:
            new_status = update_dict["translation_status"]
            await TranslationService._validate_status_transition(
                translation.translation_status, new_status
            )
        
        for field, value in update_dict.items():
            setattr(translation, field, value)
        
        await db.commit()
        await db.refresh(translation)
        
        return translation
    
    @staticmethod
    async def delete_translation(
        db: AsyncSession,
        translation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        """Delete a translation.
        
        Args:
            db: Database session
            translation_id: UUID of the translation to delete
            user_id: UUID of the user deleting the translation
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If translation not found
        """
        translation = await TranslationService.get_translation(db, translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with id '{translation_id}' not found",
            )
        
        await db.delete(translation)
        await db.commit()
        
        return {"message": "Translation deleted successfully"}
    
    @staticmethod
    async def change_translation_status(
        db: AsyncSession,
        translation_id: uuid.UUID,
        new_status: TranslationStatus,
        user_id: uuid.UUID,
    ) -> Translation:
        """Change the status of a translation.
        
        Args:
            db: Database session
            translation_id: UUID of the translation
            new_status: New translation status
            user_id: UUID of the user making the change
            
        Returns:
            Updated translation object
            
        Raises:
            HTTPException: If translation not found or status transition invalid
        """
        translation = await TranslationService.get_translation(db, translation_id)
        
        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Translation with id '{translation_id}' not found",
            )
        
        # Validate status transition
        await TranslationService._validate_status_transition(
            translation.translation_status, new_status
        )
        
        translation.translation_status = new_status
        
        await db.commit()
        await db.refresh(translation)
        
        return translation
    
    @staticmethod
    async def get_available_languages(
        db: AsyncSession,
        content_id: uuid.UUID,
    ) -> dict:
        """Get available and missing languages for content.
        
        Args:
            db: Database session
            content_id: UUID of the content
            
        Returns:
            Dictionary with 'available' and 'missing' language lists
        """
        # Get all completed translations for this content
        translations = await TranslationService.get_translations_for_content(
            db, content_id, status_filter=TranslationStatus.REVIEWED
        )
        
        # If no reviewed translations, include completed ones
        if not translations:
            translations = await TranslationService.get_translations_for_content(
                db, content_id, status_filter=TranslationStatus.COMPLETED
            )
        
        # If still no translations, get all translations
        if not translations:
            translations = await TranslationService.get_translations_for_content(
                db, content_id
            )
        
        available = [t.language for t in translations]
        
        # Get content's original language
        result = await db.execute(
            select(Content.language).where(Content.id == content_id)
        )
        original_language = result.scalar_one_or_none()
        
        if original_language:
            available.append(original_language)
        
        missing = get_missing_languages(available)
        
        return {
            "available": sorted(list(set(available))),
            "missing": missing,
        }
    
    @staticmethod
    async def bulk_create_translations(
        db: AsyncSession,
        content_id: uuid.UUID,
        languages: list[str],
        user_id: uuid.UUID,
    ) -> list[Translation]:
        """Create placeholder translations for multiple languages.
        
        Args:
            db: Database session
            content_id: UUID of the content
            languages: List of language codes
            user_id: UUID of the user creating translations
            
        Returns:
            List of created translation objects
            
        Raises:
            HTTPException: If content not found or any language invalid
        """
        # Check if content exists
        content_result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = content_result.scalar_one_or_none()
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Content with id '{content_id}' not found",
            )
        
        # Validate all languages
        validated_languages = []
        for lang in languages:
            validated_languages.append(validate_language(lang))
        
        # Create translations
        created_translations = []
        
        for language in validated_languages:
            # Check if translation already exists
            existing = await TranslationService.get_translation_by_language(
                db, content_id, language
            )
            
            if existing:
                # Skip if already exists
                continue
            
            # Create placeholder translation
            translation = Translation(
                content_id=content_id,
                language=language,
                translated_title=f"[{language.upper()}] {content.title}",
                translated_body=f"Translation pending for {language}",
                translated_slug=f"{content.slug}-{language}",
                translator_id=user_id,
                translation_status=TranslationStatus.PENDING,
            )
            
            db.add(translation)
            created_translations.append(translation)
        
        await db.commit()
        
        # Refresh all created translations
        for translation in created_translations:
            await db.refresh(translation)
        
        return created_translations
    
    @staticmethod
    async def _validate_status_transition(
        current_status: TranslationStatus,
        new_status: TranslationStatus,
    ) -> None:
        """Validate if a status transition is allowed.
        
        Args:
            current_status: Current translation status
            new_status: Desired new status
            
        Raises:
            HTTPException: If transition is not allowed
        """
        allowed_transitions = TranslationService.STATUS_TRANSITIONS.get(
            current_status, []
        )
        
        if new_status not in allowed_transitions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition from '{current_status}' to '{new_status}'. "
                    f"Allowed transitions: {[s.value for s in allowed_transitions]}"
                ),
            )
