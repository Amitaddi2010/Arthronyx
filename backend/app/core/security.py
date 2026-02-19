
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Union

import jwt  # pyjwt
from passlib.context import CryptContext

# Security Config
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_fixed_for_local_debugging")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200")) # 30 days

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


import structlog

logger = structlog.get_logger(__name__)

def _truncate_password(password: str) -> str:
    """Truncate password to 72 bytes (bcrypt limit)."""
    truncated = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    if len(password) > len(truncated):
        logger.info("security.password_truncated", original_len=len(password), new_len=len(truncated))
    return truncated


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check plain password against hashed password."""
    try:
        return pwd_context.verify(_truncate_password(plain_password), hashed_password)
    except Exception as e:
        logger.error("security.verify_error", error=str(e), error_type=type(e).__name__)
        return False


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(_truncate_password(password))


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
