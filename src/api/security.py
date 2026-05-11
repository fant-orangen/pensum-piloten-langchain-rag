"""JWT creation and verification."""

from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import InvalidTokenError

from src.config import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(subject: str) -> str:
    """Create a signed JWT with the user ID as the subject."""
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, get_settings().secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Decode a JWT and return the subject (user ID string).

    Raises jwt.InvalidTokenError if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        raise exc
    subject: str = payload["sub"]
    return subject
