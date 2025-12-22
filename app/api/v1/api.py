"""API router configuration.

This module aggregates all API routers for version 1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import examples, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    health.router,
    tags=["health"],
)

api_router.include_router(
    examples.router,
    prefix="/examples",
    tags=["examples"],
)
