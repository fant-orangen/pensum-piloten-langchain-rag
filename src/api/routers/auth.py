"""Authentication endpoints — register and login."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.dependencies import get_current_user
from src.api.models.user import User
from src.api.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.api.security import create_access_token
from src.api.services.auth import authenticate_user, change_password, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new student account.

    Raises 409 when the email already exists and 422 for invalid payloads.
    """
    user = await register_user(request, db)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return a JWT access token.

    Raises 401 for invalid credentials.
    """
    user = await authenticate_user(request.email, request.password, db)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password_endpoint(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Change the authenticated user's password.

    Raises 400 for invalid old password, weak new password, or missing old
    password when the user is not in forced-change mode.
    """
    await change_password(current_user, request.old_password, request.new_password, db)
