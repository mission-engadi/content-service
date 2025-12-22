"""File processing utilities for media handling.

Provides file validation, image processing, thumbnail generation,
and metadata extraction.
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import UploadFile
from PIL import Image
import magic

from app.models.media import MediaType
from app.core.config import settings


# File type configurations
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
}

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/aac",
    "audio/webm",
}

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
}

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB

# Image processing settings
MAX_IMAGE_WIDTH = 2048
MAX_IMAGE_HEIGHT = 2048
THUMBNAIL_SIZE = (300, 300)
IMAGE_QUALITY = 85


def get_mime_type(file: UploadFile) -> str:
    """Get MIME type of uploaded file.
    
    Args:
        file: Uploaded file
        
    Returns:
        MIME type string
    """
    # Try to get from content_type first
    if file.content_type:
        return file.content_type
    
    # Fall back to guessing from filename
    mime_type, _ = mimetypes.guess_type(file.filename)
    return mime_type or "application/octet-stream"


def get_allowed_types(media_type: MediaType) -> set:
    """Get allowed MIME types for media type.
    
    Args:
        media_type: Type of media
        
    Returns:
        Set of allowed MIME types
    """
    type_mapping = {
        MediaType.IMAGE: ALLOWED_IMAGE_TYPES,
        MediaType.VIDEO: ALLOWED_VIDEO_TYPES,
        MediaType.AUDIO: ALLOWED_AUDIO_TYPES,
        MediaType.DOCUMENT: ALLOWED_DOCUMENT_TYPES,
    }
    return type_mapping.get(media_type, set())


def get_max_size(media_type: MediaType) -> int:
    """Get maximum file size for media type.
    
    Args:
        media_type: Type of media
        
    Returns:
        Maximum size in bytes
    """
    size_mapping = {
        MediaType.IMAGE: MAX_IMAGE_SIZE,
        MediaType.VIDEO: MAX_VIDEO_SIZE,
        MediaType.AUDIO: MAX_AUDIO_SIZE,
        MediaType.DOCUMENT: MAX_DOCUMENT_SIZE,
    }
    return size_mapping.get(media_type, MAX_DOCUMENT_SIZE)


def validate_file(file: UploadFile, media_type: MediaType) -> bool:
    """Validate uploaded file.
    
    Args:
        file: Uploaded file
        media_type: Expected media type
        
    Returns:
        True if valid, False otherwise
    """
    # Check MIME type
    mime_type = get_mime_type(file)
    allowed_types = get_allowed_types(media_type)
    
    if mime_type not in allowed_types:
        return False
    
    # Check file size (if we can get it)
    # Note: Size validation is also done in the service layer
    # after the full file is read
    
    return True


def extract_image_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from image file.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Dictionary with metadata (width, height, format, etc.)
    """
    metadata = {}
    
    try:
        with Image.open(file_path) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            metadata["mode"] = img.mode
            
            # Get EXIF data if available
            if hasattr(img, "_getexif") and img._getexif():
                exif_data = img._getexif()
                if exif_data:
                    metadata["exif"] = {k: v for k, v in exif_data.items() if isinstance(v, (str, int, float))}
    
    except Exception as e:
        print(f"Failed to extract image metadata: {e}")
    
    return metadata


async def process_image(
    file_path: Path,
    max_width: int = MAX_IMAGE_WIDTH,
    max_height: int = MAX_IMAGE_HEIGHT,
) -> Path:
    """Process and optimize image.
    
    Resizes image if it exceeds maximum dimensions while maintaining aspect ratio.
    Optimizes image quality for web.
    
    Args:
        file_path: Path to image file
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        
    Returns:
        Path to processed image (same as input if no processing needed)
    """
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == "RGBA":
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            # Check if resizing is needed
            if img.width > max_width or img.height > max_height:
                # Calculate new dimensions maintaining aspect ratio
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            img.save(file_path, quality=IMAGE_QUALITY, optimize=True)
    
    except Exception as e:
        print(f"Failed to process image: {e}")
    
    return file_path


async def generate_thumbnail(
    file_path: Path,
    size: tuple = THUMBNAIL_SIZE,
) -> Optional[str]:
    """Generate thumbnail for image.
    
    Args:
        file_path: Path to image file
        size: Thumbnail size (width, height)
        
    Returns:
        Path to thumbnail file or None if generation fails
    """
    try:
        # Generate thumbnail filename
        file_stem = file_path.stem
        file_ext = file_path.suffix
        thumbnail_filename = f"{file_stem}_thumb{file_ext}"
        thumbnail_path = file_path.parent / thumbnail_filename
        
        # Create thumbnail
        with Image.open(file_path) as img:
            # Convert to RGB if needed
            if img.mode == "RGBA":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, quality=IMAGE_QUALITY, optimize=True)
        
        # Return relative path from uploads directory
        # Extract the storage path portion
        uploads_idx = str(thumbnail_path).find("uploads")
        if uploads_idx >= 0:
            return str(thumbnail_path)[uploads_idx:]
        return str(thumbnail_path)
    
    except Exception as e:
        print(f"Failed to generate thumbnail: {e}")
        return None
