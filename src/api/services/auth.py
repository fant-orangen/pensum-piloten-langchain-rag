"""Authentication business logic."""

import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.api.models.user import User
from src.api.schemas.auth import RegisterRequest
from src.api.utils.exception_util import conflict_error, unauthorized_error


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if the plaintext password matches the stored bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def register_user(request: RegisterRequest, db: AsyncSession) -> User:
    """Create a new user. Raises HTTP 409 if the email is already taken."""
    existing = await db.execute(select(User).where(User.email == request.email))
    if existing.scalars().first() is not None:
        raise conflict_error("An account with this email already exists.")

    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(email: str, password: str, db: AsyncSession) -> User:
    """Verify credentials. Raises HTTP 401 if email or password is wrong."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None or not verify_password(password, user.hashed_password):
        raise unauthorized_error(
            "Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
