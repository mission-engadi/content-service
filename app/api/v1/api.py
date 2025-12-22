"""API router configuration.

This module aggregates all API routers for version 1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import content, examples, health, translations

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    health.router,
    tags=["health"],
)

api_router.include_router(
    content.router,
    prefix="/content",
    tags=["content"],
)

# Translation routes with two path patterns:
# 1. /content/{content_id}/translations - for content-specific translations
# 2. /translations/{translation_id} - for direct translation access
api_router.include_router(
    translations.router,
    prefix="/content",
    tags=["translations"],
)

api_router.include_router(
    examples.router,
    prefix="/examples",
    tags=["examples"],
)
