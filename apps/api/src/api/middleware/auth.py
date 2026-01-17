"""
Authentication middleware for FastAPI.

Provides JWT validation via Supabase Auth and user context extraction.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from src.core.supabase import get_supabase_client
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Security scheme for Bearer token authentication
security = HTTPBearer(auto_error=True)
optional_security = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user from Supabase Auth."""

    id: str
    email: str
    role: str = "user"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == "admin"


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> AuthenticatedUser:
    """
    Validate JWT token and extract authenticated user.

    Args:
        credentials: Bearer token from Authorization header.
        supabase: Supabase client instance.

    Returns:
        AuthenticatedUser with id and email.

    Raises:
        HTTPException: 401 if token is invalid or expired.
    """
    try:
        # Validate token with Supabase
        response = supabase.auth.get_user(credentials.credentials)

        if response.user is None:
            logger.warning("auth_failed", reason="no_user_in_response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = response.user
        logger.info(
            "auth_success",
            user_id=user.id,
            email=user.email,
        )

        return AuthenticatedUser(
            id=user.id,
            email=user.email or "",
            role=user.user_metadata.get("role", "user") if user.user_metadata else "user",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("auth_failed", reason="token_validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(optional_security)],
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> AuthenticatedUser | None:
    """
    Optionally validate JWT token if provided.

    Use for endpoints that work with or without authentication.

    Args:
        credentials: Optional Bearer token from Authorization header.
        supabase: Supabase client instance.

    Returns:
        AuthenticatedUser if valid token provided, None otherwise.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        # For optional auth, return None instead of raising
        return None


def require_role(required_role: str):
    """
    Create a dependency that requires a specific user role.

    Args:
        required_role: The role required to access the endpoint.

    Returns:
        Dependency function that validates role.

    Example:
        @app.get("/admin")
        async def admin_only(user: AuthenticatedUser = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}
    """

    async def role_checker(
        user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if user.role != required_role and not user.is_admin:
            logger.warning(
                "permission_denied",
                user_id=user.id,
                required_role=required_role,
                user_role=user.role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user

    return role_checker


# Type aliases for cleaner route signatures
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
OptionalUser = Annotated[AuthenticatedUser | None, Depends(get_optional_user)]
