# Content Service Development Guide

Comprehensive guide for developers working on the Content Service.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Project Architecture](#project-architecture)
4. [Code Organization](#code-organization)
5. [Database Design](#database-design)
6. [Adding New Features](#adding-new-features)
7. [Testing Guidelines](#testing-guidelines)
8. [Code Style](#code-style)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional)
- Git
- IDE (VS Code, PyCharm, or similar)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd content_service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Running the Service

```bash
# Start with auto-reload (development mode)
./start.sh

# Or manually with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Check service status
./status.sh

# Stop service
./stop.sh
```

## Development Environment

### Recommended IDE Extensions (VS Code)

- Python
- Pylance
- Python Docstring Generator
- GitLens
- Better Comments
- Thunder Client (API testing)

### IDE Configuration

**.vscode/settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/content_db
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service
SERVICE_NAME=content_service
SERVICE_PORT=8002
LOG_LEVEL=INFO

# Storage
UPLOAD_DIR=/path/to/uploads
BASE_URL=http://localhost:8002
MAX_UPLOAD_SIZE=104857600

# Features
ENABLE_CORS=true
CORS_ORIGINS=["http://localhost:3000"]
```

## Project Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│          API Layer (FastAPI)        │  ← HTTP Requests/Responses
├─────────────────────────────────────┤
│         Service Layer (Logic)       │  ← Business Logic
├─────────────────────────────────────┤
│         Repository Layer (DB)       │  ← Database Operations
├─────────────────────────────────────┤
│      Database (PostgreSQL)          │  ← Data Storage
└─────────────────────────────────────┘
```

### Component Responsibilities

**API Layer** (`app/api/v1/endpoints/`)
- Handle HTTP requests/responses
- Validate input data
- Call service layer
- Format responses
- Handle errors

**Service Layer** (`app/services/`)
- Business logic
- Data validation
- Permission checks
- Complex operations
- Transaction management

**Models** (`app/models/`)
- Database schemas
- ORM mappings
- Relationships
- Constraints

**Schemas** (`app/schemas/`)
- Request/response validation
- Data serialization
- API contracts

## Code Organization

### File Structure

```
app/
├── api/
│   └── v1/
│       ├── endpoints/       # API route handlers
│       │   ├── content.py
│       │   ├── translations.py
│       │   ├── media.py
│       │   └── health.py
│       └── api.py          # Route aggregation
├── core/
│   ├── config.py          # Configuration
│   ├── security.py        # Auth/JWT
│   ├── languages.py       # Language utilities
│   ├── storage.py         # File storage
│   └── file_processing.py # Media processing
├── models/                # Database models
│   ├── content.py
│   ├── translation.py
│   └── media.py
├── schemas/              # Pydantic schemas
│   ├── content.py
│   ├── translation.py
│   └── media.py
├── services/            # Business logic
│   ├── content_service.py
│   ├── translation_service.py
│   └── media_service.py
├── dependencies/        # FastAPI dependencies
│   ├── auth.py
│   └── database.py
├── db/                 # Database setup
│   ├── base.py
│   └── session.py
└── main.py            # Application entry
```

### Module Dependencies

```
main.py
  ↓
api/ → dependencies/ → services/ → models/
         ↓               ↓
       core/           schemas/
         ↓
       config/
```

## Database Design

### Entity Relationship Diagram

```
┌──────────┐         ┌──────────────┐
│ Content  │─────────│ Translation  │
│          │1      * │              │
├──────────┤         ├──────────────┤
│ id       │         │ id           │
│ title    │         │ content_id   │
│ slug     │         │ language     │
│ type     │         │ title        │
│ body     │         │ body         │
│ status   │         │ status       │
│ language │         └──────────────┘
│ author_id│
└────┬─────┘
     │
     │ 1
     │ *
┌────┴─────┐
│  Media   │
├──────────┤
│ id       │
│ filename │
│ type     │
│ size     │
│ uploader │
└──────────┘
```

### Key Tables

**content:**
- Stores all content items
- Supports multiple content types
- Has status workflow
- Links to author and featured image

**translation:**
- One-to-many with content
- Tracks translation status
- Supports multiple languages
- Has its own workflow

**media:**
- Stores file metadata
- Tracks upload info
- Can be linked to content
- Supports various file types

## Adding New Features

### Adding a New Endpoint

1. **Define the model** (`app/models/new_model.py`):
```python
from sqlalchemy import Column, String, UUID
from app.db.base_class import Base

class NewModel(Base):
    __tablename__ = "new_table"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    # ... more fields
```

2. **Create schemas** (`app/schemas/new_schema.py`):
```python
from pydantic import BaseModel, Field
from uuid import UUID

class NewModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class NewModelResponse(BaseModel):
    id: UUID
    name: str
    
    class Config:
        from_attributes = True
```

3. **Implement service** (`app/services/new_service.py`):
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.new_model import NewModel
from app.schemas.new_schema import NewModelCreate

async def create_new_model(
    db: AsyncSession,
    data: NewModelCreate,
) -> NewModel:
    model = NewModel(**data.dict())
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model
```

4. **Create endpoints** (`app/api/v1/endpoints/new_endpoint.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db
from app.dependencies.auth import get_current_user
from app.schemas.new_schema import NewModelCreate, NewModelResponse
from app.services import new_service

router = APIRouter()

@router.post("", response_model=NewModelResponse, status_code=201)
async def create_model(
    data: NewModelCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return await new_service.create_new_model(db, data)
```

5. **Register routes** (`app/api/v1/api.py`):
```python
from app.api.v1.endpoints import new_endpoint

api_router.include_router(
    new_endpoint.router,
    prefix="/new-models",
    tags=["new-models"],
)
```

6. **Create migration**:
```bash
alembic revision --autogenerate -m "Add new_table"
alembic upgrade head
```

7. **Write tests** (`tests/integration/test_new_endpoint.py`):
```python
def test_create_new_model(client, auth_headers):
    response = client.post(
        "/api/v1/new-models",
        json={"name": "Test"},
        headers=auth_headers
    )
    assert response.status_code == 201
```

### Adding New Service Method

```python
async def new_method(
    db: AsyncSession,
    param: str,
) -> Result:
    """
    Method description.
    
    Args:
        db: Database session
        param: Parameter description
        
    Returns:
        Result description
        
    Raises:
        ValueError: When condition occurs
    """
    # Implementation
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── integration/             # API integration tests
│   ├── test_content.py
│   ├── test_translations.py
│   └── test_media.py
└── unit/                    # Unit tests
    └── test_security.py
```

### Writing Tests

**Integration Test Example:**
```python
class TestEndpoint:
    """Tests for endpoint functionality."""
    
    def test_success_case(self, client, auth_headers):
        """Test successful operation."""
        response = client.post(
            "/api/v1/endpoint",
            json={"data": "value"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        result = response.json()
        assert result["data"] == "value"
    
    def test_error_case(self, client):
        """Test error handling."""
        response = client.post("/api/v1/endpoint")
        assert response.status_code == 401
```

**Unit Test Example:**
```python
def test_function():
    """Test specific function."""
    result = my_function(input_value)
    assert result == expected_value
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/integration/test_content.py -v

# Run specific test
pytest tests/integration/test_content.py::TestCreateContent::test_success -v

# Run tests matching pattern
pytest -k "test_create"
```

### Test Fixtures

Common fixtures in `conftest.py`:
- `client`: Test client
- `db_session`: Database session
- `auth_headers`: Authentication headers
- `sample_content`: Sample content item
- `sample_translation`: Sample translation
- `sample_media`: Sample media file

## Code Style

### Style Guide

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions focused
- Maximum line length: 100 characters

### Formatting

```bash
# Format code
black app tests

# Check formatting
black --check app tests

# Sort imports
isort app tests
```

### Linting

```bash
# Run flake8
flake8 app tests

# Run mypy (type checking)
mypy app
```

### Docstring Format

```python
def function(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When this happens
        HTTPException: When that happens
    """
    pass
```

## Best Practices

### Database Operations

```python
# Good: Use async/await
async def get_item(db: AsyncSession, id: UUID):
    result = await db.execute(select(Model).where(Model.id == id))
    return result.scalar_one_or_none()

# Bad: Synchronous operations
def get_item(db: Session, id: UUID):
    return db.query(Model).filter(Model.id == id).first()
```

### Error Handling

```python
# Good: Specific exceptions
from fastapi import HTTPException

async def get_content(db: AsyncSession, id: UUID):
    content = await db.get(Content, id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content

# Bad: Generic exception
async def get_content(db: AsyncSession, id: UUID):
    try:
        return await db.get(Content, id)
    except:
        raise Exception("Error")
```

### Service Layer

```python
# Good: Business logic in service
async def publish_content(db: AsyncSession, content_id: UUID):
    content = await get_content(db, content_id)
    if content.status != ContentStatus.DRAFT:
        raise ValueError("Only draft content can be published")
    
    content.status = ContentStatus.PUBLISHED
    content.published_at = datetime.utcnow()
    await db.commit()
    return content

# Bad: Business logic in endpoint
@router.post("/{id}/publish")
async def publish(id: UUID, db: AsyncSession = Depends(get_db)):
    content = await db.get(Content, id)
    content.status = "published"
    await db.commit()
```

### Authentication

```python
# Good: Use dependency injection
@router.post("/protected")
async def protected_endpoint(
    current_user = Depends(get_current_user)
):
    # User is authenticated
    pass

# Bad: Manual token parsing
@router.post("/protected")
async def protected_endpoint(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    # Manual verification...
```

## Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l | grep content_db

# Recreate database
sudo -u postgres psql -c "DROP DATABASE IF EXISTS content_db;"
sudo -u postgres psql -c "CREATE DATABASE content_db;"
```

**Migration issues:**
```bash
# Check current version
alembic current

# Show migration history
alembic history

# Reset migrations (WARNING: destroys data)
alembic downgrade base
alembic upgrade head
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Test failures:**
```bash
# Run tests with verbose output
pytest -vv

# Run specific failing test
pytest tests/path/to/test.py::test_name -vv

# Check test database
sudo -u postgres psql -l | grep test_db
```

### Debug Mode

Enable debug logging in `.env`:
```bash
LOG_LEVEL=DEBUG
```

View logs:
```bash
tail -f content_service.log
```

### Performance Profiling

```python
# Add timing to endpoints
import time

@router.get("/slow")
async def slow_endpoint():
    start = time.time()
    # ... operation
    duration = time.time() - start
    print(f"Operation took {duration:.2f}s")
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [Pydantic Documentation](https://docs.pydantic.dev)
- [Alembic Documentation](https://alembic.sqlalchemy.org)
- [Pytest Documentation](https://docs.pytest.org)

---

**Last Updated:** December 22, 2024
**Document Version:** 1.0
