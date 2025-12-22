"""Dependency injection functions for FastAPI."""

from app.dependencies.auth import (  # noqa: F401
    CurrentUser,
    get_current_user,
    get_current_active_user,
    get_optional_user,
    require_superuser,
    require_roles,
)
from app.dependencies.database import get_db  # noqa: F401

__all__ = [
    "CurrentUser",
    "get_current_user",
    "get_current_active_user",
    "get_optional_user",
    "require_superuser",
    "require_roles",
    "get_db",
]
