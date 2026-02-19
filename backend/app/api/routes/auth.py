
from datetime import timedelta
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.core import security
from app.db.session import get_db
from app.models.user import User

router = APIRouter()
logger = structlog.get_logger(__name__)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """Create new user."""
    logger.info("auth.signup_attempt", email=user_in.email)
    
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            logger.warning("auth.signup_duplicate", email=user_in.email)
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )

        user = User(
            email=user_in.email,
            hashed_password=security.get_password_hash(user_in.password),
            full_name=user_in.full_name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("auth.signup_success", email=user_in.email, user_id=user.id)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error("auth.signup_error", email=user_in.email, error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail=f"Signup failed: {type(e).__name__}: {str(e)}",
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Any:
    """OAuth2 compatible token login, get an access token for future requests."""
    logger.info("auth.login_attempt", email=form_data.username)

    try:
        # Find user by email (username field in form_data)
        result = await db.execute(select(User).where(User.email == form_data.username))
        user = result.scalar_one_or_none()

        if not user or not security.verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        logger.info("auth.login_success", email=form_data.username)
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("auth.login_error", email=form_data.username, error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail=f"Login failed: {type(e).__name__}: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: Annotated[User, Depends(deps.get_current_active_user)],
) -> Any:
    """Get current user."""
    return current_user
