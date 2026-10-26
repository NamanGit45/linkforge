from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:

    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:

    # Check email uniqueness
    existing = await get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Hash password — NEVER store plaintext
    hashed = hash_password(user_data.password)

    # Create user ORM object
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        # role defaults to "user" as defined in the model
        # is_active defaults to True
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:

    user = await get_user_by_email(db, email)

    # Same error whether email wrong OR password wrong
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        raise credentials_error

    if not verify_password(password, user.hashed_password):
        raise credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )

    return user
