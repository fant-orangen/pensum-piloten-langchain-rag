"""FastAPI dependencies shared across routers."""

import uuid

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.database import get_db
from src.api.models.user import User
from src.api.security import decode_access_token

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the Bearer token and return the authenticated user.

    Raises HTTP 401 if the token is missing, invalid, or the user no longer
    exists / is inactive.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id_str = decode_access_token(token)
        user_id = uuid.UUID(user_id_str)
    except (InvalidTokenError, ValueError):
        raise credentials_error

    result = await db.exec(select(User).where(User.id == user_id))
    user = result.first()

    if user is None or not user.is_active:
        raise credentials_error

    return user
