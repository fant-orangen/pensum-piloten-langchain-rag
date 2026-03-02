"""Authentication endpoints — register and login."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.database import get_db
from src.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.api.security import create_access_token
from src.api.services.auth import authenticate_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    user = await register_user(request, db)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return a JWT access token."""
    user = await authenticate_user(request.email, request.password, db)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)
