"""Pytest configuration and fixtures.

This file contains shared fixtures used across all tests.
"""

import asyncio
import io
import os
import tempfile
from datetime import datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import create_access_token
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app
from app.models.content import Content, ContentStatus, ContentType
from app.models.media import Media, MediaType
from app.models.translation import Translation, TranslationStatus

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db"

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# Create session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test.
    
    This fixture:
    1. Creates all tables before the test
    2. Provides a database session
    3. Rolls back changes after the test
    4. Drops all tables
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator:
    """Create a test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ===== Authentication Fixtures =====

@pytest.fixture
def test_user_id() -> str:
    """Generate a consistent test user ID."""
    return str(uuid4())


@pytest.fixture
def auth_token(test_user_id: str) -> str:
    """Create a test JWT token."""
    return create_access_token(
        subject=test_user_id,
        additional_claims={
            "email": "test@example.com",
            "roles": ["user"],
        },
    )


@pytest.fixture
def admin_token() -> str:
    """Create a test JWT token with admin role."""
    return create_access_token(
        subject=str(uuid4()),
        additional_claims={
            "email": "admin@example.com",
            "roles": ["admin", "user"],
        },
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers with test token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token: str) -> dict:
    """Create authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


# ===== Content Fixtures =====

@pytest_asyncio.fixture
async def sample_content(db_session: AsyncSession, test_user_id: str) -> Content:
    """Create a sample content item."""
    content = Content(
        title="Test Article",
        slug="test-article",
        content_type=ContentType.ARTICLE,
        body="This is a test article body.",
        status=ContentStatus.DRAFT,
        author_id=test_user_id,
        language="en",
        meta_description="Test article description",
        tags=["test", "article"],
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    return content


@pytest_asyncio.fixture
async def published_content(db_session: AsyncSession, test_user_id: str) -> Content:
    """Create a published content item."""
    content = Content(
        title="Published Article",
        slug="published-article",
        content_type=ContentType.ARTICLE,
        body="This is a published article.",
        status=ContentStatus.PUBLISHED,
        author_id=test_user_id,
        language="en",
        published_at=datetime.utcnow(),
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    return content


@pytest_asyncio.fixture
async def multiple_contents(db_session: AsyncSession, test_user_id: str) -> list[Content]:
    """Create multiple content items for testing list operations."""
    contents = []
    for i in range(5):
        content = Content(
            title=f"Article {i}",
            slug=f"article-{i}",
            content_type=ContentType.ARTICLE,
            body=f"Article body {i}",
            status=ContentStatus.DRAFT if i % 2 == 0 else ContentStatus.PUBLISHED,
            author_id=test_user_id,
            language="en",
        )
        db_session.add(content)
        contents.append(content)
    
    await db_session.commit()
    for content in contents:
        await db_session.refresh(content)
    
    return contents


# ===== Translation Fixtures =====

@pytest_asyncio.fixture
async def sample_translation(db_session: AsyncSession, sample_content: Content) -> Translation:
    """Create a sample translation."""
    translation = Translation(
        content_id=sample_content.id,
        language="es",
        title="Artículo de Prueba",
        body="Este es un cuerpo de artículo de prueba.",
        status=TranslationStatus.PENDING,
        meta_description="Descripción del artículo de prueba",
    )
    db_session.add(translation)
    await db_session.commit()
    await db_session.refresh(translation)
    return translation


@pytest_asyncio.fixture
async def multiple_translations(
    db_session: AsyncSession, 
    sample_content: Content
) -> list[Translation]:
    """Create multiple translations for a content item."""
    translations = []
    languages = [("es", "Spanish"), ("fr", "French"), ("pt-br", "Portuguese")]
    
    for lang, name in languages:
        translation = Translation(
            content_id=sample_content.id,
            language=lang,
            title=f"Test in {name}",
            body=f"Content in {name}",
            status=TranslationStatus.PENDING,
        )
        db_session.add(translation)
        translations.append(translation)
    
    await db_session.commit()
    for translation in translations:
        await db_session.refresh(translation)
    
    return translations


# ===== Media Fixtures =====

@pytest.fixture
def test_image_file() -> io.BytesIO:
    """Create a test image file."""
    image = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    img_bytes.name = 'test_image.png'
    return img_bytes


@pytest.fixture
def test_document_file() -> io.BytesIO:
    """Create a test document file."""
    content = b"This is a test document content."
    doc_bytes = io.BytesIO(content)
    doc_bytes.seek(0)
    doc_bytes.name = 'test_document.txt'
    return doc_bytes


@pytest_asyncio.fixture
async def sample_media(
    db_session: AsyncSession, 
    test_user_id: str
) -> Media:
    """Create a sample media item."""
    media = Media(
        filename="test_image.png",
        original_filename="test_image.png",
        file_path="/uploads/2024/12/test_image.png",
        file_size=1024,
        mime_type="image/png",
        media_type=MediaType.IMAGE,
        uploaded_by=test_user_id,
        width=100,
        height=100,
    )
    db_session.add(media)
    await db_session.commit()
    await db_session.refresh(media)
    return media


@pytest_asyncio.fixture
async def content_with_media(
    db_session: AsyncSession,
    sample_content: Content,
    sample_media: Media,
) -> Content:
    """Create content with associated media."""
    sample_content.featured_image_id = sample_media.id
    await db_session.commit()
    await db_session.refresh(sample_content)
    return sample_content


# ===== Temporary Directory Fixture =====

@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for file uploads during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override the upload directory setting
        original_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = tmpdir
        yield tmpdir
        # Restore original setting
        settings.UPLOAD_DIR = original_upload_dir
