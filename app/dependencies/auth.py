"""Authentication dependencies.

Provides dependency functions for protecting routes and extracting user context.
"""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_token

# HTTP Bearer token security scheme
security = HTTPBearer()


class CurrentUser:
    """Current user context extracted from JWT token.
    
    This class represents the authenticated user making the request.
    Since Content Service doesn't have direct access to the User table
    from Auth Service, we extract user info from JWT token.
    """
    
    def __init__(
        self,
        user_id: uuid.UUID,
        email: Optional[str] = None,
        roles: Optional[list[str]] = None,
        is_active: bool = True,
        is_superuser: bool = False,
    ):
        self.user_id = user_id
        self.email = email or ""
        self.roles = roles or []
        self.is_active = is_active
        self.is_superuser = is_superuser
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def __repr__(self) -> str:
        return f"<CurrentUser(user_id={self.user_id}, email='{self.email}')>"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """Extract and validate current user from JWT token.
    
    This dependency can be used to protect routes and get user context.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.user_id}
    
    Args:
        credentials: HTTP Bearer credentials from request header
    
    Returns:
        CurrentUser object with user information
    
    Raises:
        HTTPException: If token is invalid or missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        # Extract user information from token
        user_id_str: Optional[str] = payload.get("sub")
        email: Optional[str] = payload.get("email")
        roles: list[str] = payload.get("roles", [])
        is_active: bool = payload.get("is_active", True)
        is_superuser: bool = payload.get("is_superuser", False)
        
        if user_id_str is None:
            raise credentials_exception
        
        # Convert user_id to UUID
        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, AttributeError):
            raise credentials_exception
        
        return CurrentUser(
            user_id=user_id,
            email=email,
            roles=roles,
            is_active=is_active,
            is_superuser=is_superuser,
        )
    
    except (JWTError, ValueError):
        raise credentials_exception


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Get current active user.
    
    This dependency ensures the user account is active.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_active_user)):
            return {"user_id": user.user_id}
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        CurrentUser object if active
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def require_superuser(
    current_user: CurrentUser = Depends(get_current_active_user),
) -> CurrentUser:
    """Require superuser privileges.
    
    This dependency ensures the user has superuser privileges.
    
    Usage:
        @router.get("/admin")
        async def admin_route(user: CurrentUser = Depends(require_superuser)):
            return {"message": "Admin access granted"}
    
    Args:
        current_user: Current active user
    
    Returns:
        CurrentUser object if superuser
    
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user


def require_roles(required_roles: list[str]):
    """Create a dependency that requires specific roles.
    
    This is a dependency factory that returns a dependency function.
    Use it to protect routes that require specific roles.
    
    Usage:
        @router.get("/editor")
        async def editor_route(
            user: CurrentUser = Depends(require_roles(["editor", "admin"]))
        ):
            return {"message": "Editor access granted"}
    
    Args:
        required_roles: List of roles required to access the route (any match)
    
    Returns:
        Dependency function that validates user roles
    """
    
    async def check_roles(
        user: CurrentUser = Depends(get_current_active_user),
    ) -> CurrentUser:
        """Check if user has required roles."""
        if required_roles:
            if not any(user.has_role(role) for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions. Required roles: " + ", ".join(required_roles),
                )
        return user
    
    return check_roles


# Optional dependency for routes that can be accessed with or without authentication
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[CurrentUser]:
    """Extract user from JWT token if provided, otherwise return None.
    
    This dependency is useful for routes that behave differently for
    authenticated vs unauthenticated users.
    
    Usage:
        @router.get("/content")
        async def get_content(user: Optional[CurrentUser] = Depends(get_optional_user)):
            if user:
                # Show all content including drafts
                pass
            else:
                # Show only published content
                pass
    
    Args:
        credentials: Optional HTTP Bearer credentials from request header
    
    Returns:
        CurrentUser object if valid token provided, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            return None
        
        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, AttributeError):
            return None
        
        return CurrentUser(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", []),
            is_active=payload.get("is_active", True),
            is_superuser=payload.get("is_superuser", False),
        )
    
    except (JWTError, ValueError):
        return None
