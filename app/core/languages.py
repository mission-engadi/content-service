"""Language utilities for multi-language content support.

Defines supported languages, validation functions, and language-related utilities.
"""

from typing import Optional
from fastapi import HTTPException, status


# Supported language codes
SUPPORTED_LANGUAGES = ["en", "es", "fr", "pt-br"]

# Language names mapping
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "pt-br": "Portuguese - Brazil (Português)",
}


def validate_language(language: str) -> str:
    """Validate a language code against supported languages.
    
    Args:
        language: Language code to validate
        
    Returns:
        Validated language code (lowercase)
        
    Raises:
        HTTPException: If language is not supported
    """
    language_lower = language.lower().strip()
    
    if language_lower not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Language '{language}' is not supported. "
                f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
            ),
        )
    
    return language_lower


def get_language_name(language: str) -> str:
    """Get the display name for a language code.
    
    Args:
        language: Language code (e.g., 'en', 'es')
        
    Returns:
        Language display name (e.g., 'English', 'Spanish')
        
    Raises:
        ValueError: If language is not supported
    """
    language_lower = language.lower().strip()
    
    if language_lower not in LANGUAGE_NAMES:
        raise ValueError(f"Language '{language}' is not supported")
    
    return LANGUAGE_NAMES[language_lower]


def get_missing_languages(
    available_languages: list[str],
    include_all: bool = True
) -> list[str]:
    """Get list of missing languages for content.
    
    Args:
        available_languages: List of languages already available
        include_all: If True, return all supported languages. If False, exclude 'en'
        
    Returns:
        List of missing language codes
    """
    available_set = set(lang.lower().strip() for lang in available_languages)
    
    if include_all:
        supported = set(SUPPORTED_LANGUAGES)
    else:
        # Exclude English as it's typically the original language
        supported = set(lang for lang in SUPPORTED_LANGUAGES if lang != "en")
    
    missing = supported - available_set
    return sorted(list(missing))


def is_language_supported(language: str) -> bool:
    """Check if a language is supported.
    
    Args:
        language: Language code to check
        
    Returns:
        True if language is supported, False otherwise
    """
    return language.lower().strip() in SUPPORTED_LANGUAGES


def normalize_language_code(language: str) -> Optional[str]:
    """Normalize a language code to standard format.
    
    Args:
        language: Language code to normalize
        
    Returns:
        Normalized language code or None if invalid
    """
    language_lower = language.lower().strip()
    
    # Handle common variations
    variations = {
        "pt": "pt-br",
        "pt_br": "pt-br",
        "ptbr": "pt-br",
        "portuguese": "pt-br",
        "spanish": "es",
        "french": "fr",
        "english": "en",
    }
    
    # Try direct match first
    if language_lower in SUPPORTED_LANGUAGES:
        return language_lower
    
    # Try variations
    if language_lower in variations:
        return variations[language_lower]
    
    return None
