# Content Service

> Multi-language content management system for Mission Engadi platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.108+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Part of the [Mission Engadi](https://engadi.org) microservices architecture - A comprehensive content management system for educational missions content with full multi-language support, media handling, and workflow management.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)

## 🎯 Overview

The Content Service is the central content management system for the Mission Engadi platform. It provides:

- **Content Management**: Create, read, update, delete, and publish various types of content (articles, lessons, videos, resources)
- **Multi-Language Support**: Full translation workflow with support for English, Spanish, French, and Portuguese
- **Media Handling**: Upload, process, and manage images, videos, audio, and documents
- **Workflow Management**: Status-based workflows for content and translations (draft → review → published)
- **RESTful API**: 25 comprehensive API endpoints with automatic OpenAPI documentation

### Key Capabilities

- **8 Content Management Endpoints**: Full CRUD operations plus publishing and status management
- **9 Translation Management Endpoints**: Complete translation workflow including bulk operations
- **8 Media Handling Endpoints**: Media upload, processing, retrieval, and management
- **JWT Authentication**: Secure API access with role-based permissions
- **Async Architecture**: High-performance async/await with SQLAlchemy and PostgreSQL

## ✨ Features

### Content Management
- ✅ Create and manage multiple content types (articles, lessons, videos, resources)
- ✅ Slug-based URLs for SEO-friendly content access
- ✅ Rich metadata support (tags, descriptions, categories)
- ✅ Content status workflow (draft, review, published, archived)
- ✅ Featured image support
- ✅ Author tracking and permissions

### Translation System
- ✅ Support for 4 languages: English (en), Spanish (es), French (fr), Portuguese (pt-br)
- ✅ Translation status workflow (pending, in_progress, completed, reviewed)
- ✅ Individual translation CRUD operations
- ✅ Bulk translation creation
- ✅ Language availability tracking
- ✅ Content retrieval with language parameter

### Media Management
- ✅ Multi-format support (images, videos, audio, documents)
- ✅ Automatic image resizing (max 2048x2048)
- ✅ Thumbnail generation (300x300)
- ✅ MIME type detection and validation
- ✅ File size limits by type
- ✅ Organized storage structure (YYYY/MM/filename)
- ✅ Media metadata management

### Technical Features
- ✅ **Fast**: Fully asynchronous with uvicorn and asyncpg
- ✅ **Secure**: JWT authentication with role-based access control
- ✅ **Validated**: Pydantic models for request/response validation
- ✅ **Tested**: 80%+ test coverage with comprehensive integration tests
- ✅ **Documented**: Auto-generated OpenAPI/Swagger documentation
- ✅ **Monitored**: Health check and readiness endpoints
- ✅ **Versioned**: Git version control with clear commit history

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for caching)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd content_service
```

2. **Start the service:**
```bash
./start.sh
```

That's it! The start script will:
- Create virtual environment
- Install dependencies
- Start PostgreSQL and Redis
- Run database migrations
- Create uploads directory
- Start the service on http://localhost:8002

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/content_db

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Service
SERVICE_NAME=content_service
SERVICE_PORT=8002

# Storage
UPLOAD_DIR=/home/ubuntu/content_service/uploads
MAX_UPLOAD_SIZE=104857600  # 100MB
```

### Management Scripts

- **Start service**: `./start.sh`
- **Stop service**: `./stop.sh`
- **Restart service**: `./restart.sh`
- **Check status**: `./status.sh`

## 📡 API Endpoints

### Content Endpoints (8)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/content` | Create new content | ✅ |
| GET | `/api/v1/content/{id}` | Get content by ID | ❌ |
| GET | `/api/v1/content/slug/{slug}` | Get content by slug | ❌ |
| GET | `/api/v1/content` | List content with filters | ❌ |
| PUT | `/api/v1/content/{id}` | Update content | ✅ |
| DELETE | `/api/v1/content/{id}` | Delete content (soft) | ✅ |
| POST | `/api/v1/content/{id}/publish` | Publish content | ✅ |
| POST | `/api/v1/content/{id}/status` | Change content status | ✅ |

### Translation Endpoints (9)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/content/{id}/translations` | Create translation | ✅ |
| GET | `/api/v1/content/{id}/translations` | List translations | ❌ |
| GET | `/api/v1/content/{id}/translations/{lang}` | Get by language | ❌ |
| GET | `/api/v1/translations/{id}` | Get translation by ID | ❌ |
| PUT | `/api/v1/translations/{id}` | Update translation | ✅ |
| DELETE | `/api/v1/translations/{id}` | Delete translation | ✅ |
| POST | `/api/v1/translations/{id}/status` | Change status | ✅ |
| GET | `/api/v1/content/{id}/languages` | Get available languages | ❌ |
| POST | `/api/v1/content/{id}/translations/bulk` | Bulk create translations | ✅ |

### Media Endpoints (8)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/media/upload` | Upload media file | ✅ |
| POST | `/api/v1/media/content/{id}/upload` | Upload for content | ✅ |
| GET | `/api/v1/media/{id}` | Get media metadata | ❌ |
| GET | `/api/v1/media/{id}/download` | Download media file | ❌ |
| GET | `/api/v1/media/content/{id}/media` | List content media | ❌ |
| GET | `/api/v1/media` | List all media | ❌ |
| PUT | `/api/v1/media/{id}` | Update media metadata | ✅ |
| DELETE | `/api/v1/media/{id}` | Delete media | ✅ |

### Documentation & Health

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc
- **Health Check**: http://localhost:8002/api/v1/health

## 📁 Project Structure

```
content_service/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── content.py       # Content endpoints
│   │       │   ├── translations.py  # Translation endpoints
│   │       │   ├── media.py         # Media endpoints
│   │       │   └── health.py        # Health checks
│   │       └── api.py               # API router aggregation
│   ├── core/
│   │   ├── config.py                # Configuration settings
│   │   ├── security.py              # JWT & authentication
│   │   ├── languages.py             # Language utilities
│   │   ├── storage.py               # File storage management
│   │   └── file_processing.py      # Media processing
│   ├── models/
│   │   ├── content.py               # Content database models
│   │   ├── translation.py           # Translation models
│   │   └── media.py                 # Media models
│   ├── schemas/
│   │   ├── content.py               # Content Pydantic schemas
│   │   ├── translation.py           # Translation schemas
│   │   └── media.py                 # Media schemas
│   ├── services/
│   │   ├── content_service.py       # Content business logic
│   │   ├── translation_service.py   # Translation logic
│   │   └── media_service.py         # Media logic
│   ├── dependencies/
│   │   ├── auth.py                  # Auth dependencies
│   │   └── database.py              # DB dependencies
│   ├── db/
│   │   ├── base.py                  # Database base
│   │   └── session.py               # Session management
│   └── main.py                      # Application entry point
├── tests/
│   ├── conftest.py                  # Test fixtures
│   ├── integration/
│   │   ├── test_content.py          # Content endpoint tests
│   │   ├── test_translations.py     # Translation tests
│   │   ├── test_media.py            # Media tests
│   │   └── test_auth_integration.py # Auth tests
│   └── unit/
│       └── test_security.py         # Security unit tests
├── migrations/                      # Alembic migrations
├── uploads/                         # Media file storage
├── start.sh                         # Start service script
├── stop.sh                          # Stop service script
├── restart.sh                       # Restart service script
├── status.sh                        # Status check script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── pytest.ini                       # Pytest configuration
├── alembic.ini                      # Alembic configuration
└── README.md                        # This file
```

## 🛠 Development

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Create .env file
cp .env.example .env
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Running in Development Mode

```bash
# Start with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Or use the script
./start.sh
```

### Code Quality

```bash
# Format code
black app tests

# Lint code
flake8 app tests

# Type checking
mypy app
```

## 🧪 Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/integration/test_content.py -v

# Run specific test
pytest tests/integration/test_content.py::TestCreateContent::test_create_content_success -v
```

### Test Categories

- **Integration Tests**: Test API endpoints with database
  - Content endpoints (test_content.py)
  - Translation endpoints (test_translations.py)
  - Media endpoints (test_media.py)
  - Auth integration (test_auth_integration.py)

- **Unit Tests**: Test individual components
  - Security functions (test_security.py)

### Test Coverage

Current test coverage: **80%+**

```bash
# Generate coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## 🚀 Deployment

### Using Docker

```bash
# Build image
docker build -t content-service .

# Run container
docker run -d -p 8002:8002 --name content-service content-service
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f content-service

# Stop services
docker-compose down
```

### Production Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed production deployment instructions including:
- Environment configuration
- Database setup
- Security best practices
- Monitoring setup
- Backup strategies

## 📚 Documentation

- **[API Documentation](./API_DOCUMENTATION.md)**: Complete API reference with examples
- **[Development Guide](./DEVELOPMENT_GUIDE.md)**: Developer documentation and best practices
- **[Deployment Guide](./DEPLOYMENT_GUIDE.md)**: Production deployment instructions
- **[Testing Documentation](./TESTING_AND_DOCUMENTATION_SUMMARY.md)**: Test coverage and documentation summary

### Auto-Generated Documentation

- **Swagger UI**: http://localhost:8002/docs - Interactive API documentation
- **ReDoc**: http://localhost:8002/redoc - Alternative API documentation
- **OpenAPI JSON**: http://localhost:8002/openapi.json - OpenAPI specification

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow PEP 8 style guide
- Update documentation
- Add type hints
- Write descriptive commit messages

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact the development team
- Refer to the documentation

## 📊 Service Status

- **API Version**: v1
- **Service Port**: 8002
- **Database**: PostgreSQL 15+
- **Python Version**: 3.11+
- **Test Coverage**: 80%+
- **Endpoints**: 25 (8 content + 9 translation + 8 media)

## 🔗 Related Services

Part of the Mission Engadi microservices ecosystem:
- **Auth Service** (port 8001): Authentication and user management
- **Content Service** (port 8002): Content management (this service)
- **Other services**: Coming soon...

---

**Note**: This service runs on localhost of the computer hosting it. To access remotely, deploy to your own infrastructure.

Made with ❤️ by the Mission Engadi team
