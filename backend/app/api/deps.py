
from typing import Annotated

from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# import jwt
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select

# from app.core import security
# from app.db.session import get_db
from app.models.user import User

# Token URL relative to prefix
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# ------------------------------------------------------------------
# AUTHENTICATION BYPASS FOR TESTING
# ------------------------------------------------------------------
# The original get_current_user verified tokens.
# This replacement returns a hardcoded "Test User" to bypass login/signup.

async def get_current_user() -> User:
    """
    Authentication BYPASSED.
    Returns a dummy user to allow immediate access to protected routes.
    """
    return User(
        id=777,
        email="bypass@arthronyx.internal",
        full_name="Bypass Test User",
        is_active=True,
        hashed_password="mock_hash_ignored"
    )


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency for active user (restored)."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
