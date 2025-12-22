"""Storage management for media files.

Handles file storage operations with support for local filesystem.
Designed to be easily extended for cloud storage (S3, Azure, etc.).
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple
from datetime import datetime

from fastapi import UploadFile

from app.core.config import settings


class StorageManager:
    """Manager for file storage operations."""
    
    def __init__(self):
        """Initialize storage manager."""
        self.base_path = Path(settings.UPLOAD_DIR)
        self._ensure_base_directory()
    
    def _ensure_base_directory(self) -> None:
        """Ensure base upload directory exists."""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename to avoid collisions.
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            Unique filename
        """
        # Extract extension
        name, ext = os.path.splitext(original_filename)
        
        # Generate unique ID
        unique_id = uuid.uuid4().hex[:12]
        
        # Create filename: original_name_uniqueid.ext
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))[:50]
        return f"{safe_name}_{unique_id}{ext}"
    
    def get_storage_path(self, filename: str) -> str:
        """Get storage path with year/month structure.
        
        Args:
            filename: Filename to store
            
        Returns:
            Relative storage path (e.g., uploads/2024/12/filename.jpg)
        """
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        return os.path.join("uploads", year, month, filename)
    
    def get_full_path(self, storage_path: str) -> Path:
        """Get full filesystem path from storage path.
        
        Args:
            storage_path: Relative storage path
            
        Returns:
            Full filesystem path
        """
        return self.base_path / storage_path
    
    def get_file_url(self, storage_path: str) -> str:
        """Get public URL for file.
        
        Args:
            storage_path: Relative storage path
            
        Returns:
            Public URL
        """
        # For local storage, return API endpoint URL
        # In production, this would return CDN URL
        base_url = settings.BASE_URL.rstrip('/')
        return f"{base_url}/media/files/{storage_path}"
    
    async def save_file(self, file: UploadFile) -> Tuple[str, str]:
        """Save uploaded file to storage.
        
        Args:
            file: Uploaded file
            
        Returns:
            Tuple of (storage_path, file_url)
            
        Raises:
            Exception: If file save fails
        """
        # Generate unique filename
        unique_filename = self.generate_unique_filename(file.filename)
        
        # Get storage path
        storage_path = self.get_storage_path(unique_filename)
        
        # Get full path
        full_path = self.get_full_path(storage_path)
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        try:
            with open(full_path, "wb") as buffer:
                # Read and write in chunks to handle large files
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    buffer.write(chunk)
            
            # Reset file pointer for potential reuse
            await file.seek(0)
            
        except Exception as e:
            # Clean up on error
            if full_path.exists():
                full_path.unlink()
            raise Exception(f"Failed to save file: {e}")
        
        # Get public URL
        file_url = self.get_file_url(storage_path)
        
        return storage_path, file_url
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage.
        
        Args:
            storage_path: Relative storage path
            
        Returns:
            True if deleted, False if file doesn't exist
            
        Raises:
            Exception: If deletion fails
        """
        full_path = self.get_full_path(storage_path)
        
        if not full_path.exists():
            return False
        
        try:
            full_path.unlink()
            
            # Clean up empty directories
            try:
                full_path.parent.rmdir()
                full_path.parent.parent.rmdir()
            except OSError:
                # Directory not empty, that's fine
                pass
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete file: {e}")
    
    def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in storage.
        
        Args:
            storage_path: Relative storage path
            
        Returns:
            True if file exists
        """
        full_path = self.get_full_path(storage_path)
        return full_path.exists()
