"""FastAPI dependency injection utilities."""

from typing import Generator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that decodes the Bearer JWT token, validates identity,
    and returns the authenticated User entity.
    """
    if not token:
        raise UnauthorizedException(detail="Authentication token is missing.")

    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(detail="Invalid token claims: subject missing.")

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedException(detail="Invalid token claims: malformed user ID.")

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedException(detail="User corresponding to token no longer exists.")

    return user
