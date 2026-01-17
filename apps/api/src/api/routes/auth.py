"""
Authentication routes for user registration, login, and session management.

Wraps Supabase Auth for consistent API responses.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from supabase import Client

from src.api.middleware.auth import CurrentUser
from src.core.supabase import get_supabase_client
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# Request/Response Models
# =============================================================================


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response with tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    created_at: str | None = None


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# =============================================================================
# Routes
# =============================================================================


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> AuthResponse:
    """
    Register a new user account.

    Creates a new user in Supabase Auth and returns access tokens.
    Rate limited to 3 requests per minute.
    """
    logger.info("registration_attempt", email=request.email)

    try:
        response = supabase.auth.sign_up(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if response.user is None:
            logger.warning("registration_failed", email=request.email, reason="no_user")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed. Please try again.",
            )

        if response.session is None:
            # Email confirmation required
            logger.info("registration_pending_confirmation", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Please check your email to confirm your account.",
            )

        logger.info("registration_success", user_id=response.user.id)

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in or 3600,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or "",
                created_at=response.user.created_at,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "already exists" in error_msg:
            logger.warning("registration_failed", email=request.email, reason="email_exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from e

        logger.exception("registration_error", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later.",
        ) from e


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> AuthResponse:
    """
    Authenticate user and return access tokens.

    Rate limited to 5 requests per minute per IP.
    """
    logger.info("login_attempt", email=request.email)

    try:
        response = supabase.auth.sign_in_with_password(
            {
                "email": request.email,
                "password": request.password,
            }
        )

        if response.user is None or response.session is None:
            logger.warning("login_failed", email=request.email, reason="invalid_credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        logger.info("login_success", user_id=response.user.id)

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in or 3600,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or "",
                created_at=response.user.created_at,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("login_failed", email=request.email, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from e


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshRequest,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> AuthResponse:
    """
    Refresh access token using refresh token.

    Use this endpoint when the access token has expired.
    """
    logger.info("token_refresh_attempt")

    try:
        response = supabase.auth.refresh_session(request.refresh_token)

        if response.user is None or response.session is None:
            logger.warning("token_refresh_failed", reason="invalid_refresh_token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        logger.info("token_refresh_success", user_id=response.user.id)

        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            expires_in=response.session.expires_in or 3600,
            user=UserResponse(
                id=response.user.id,
                email=response.user.email or "",
                created_at=response.user.created_at,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.warning("token_refresh_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from e


@router.post("/logout", response_model=MessageResponse)
async def logout(
    _user: CurrentUser,
    supabase: Annotated[Client, Depends(get_supabase_client)],
) -> MessageResponse:
    """
    Log out the current user.

    Invalidates the current session. Requires authentication.
    """
    logger.info("logout_attempt", user_id=_user.id)

    try:
        supabase.auth.sign_out()
        logger.info("logout_success", user_id=_user.id)
        return MessageResponse(message="Successfully logged out.")
    except Exception as e:
        logger.warning("logout_failed", user_id=_user.id, error=str(e))
        # Still return success - client should clear tokens regardless
        return MessageResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: CurrentUser) -> UserResponse:
    """
    Get current authenticated user's information.

    Requires valid access token.
    """
    return UserResponse(
        id=user.id,
        email=user.email,
    )
