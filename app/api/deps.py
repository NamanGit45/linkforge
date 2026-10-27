from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.services import user_service

# OAuth2PasswordBearer does ONE thing:
# reads the Authorization: Bearer <token> header
# and returns the raw token string.
# tokenUrl tells Swagger UI where the login endpoint is
# so the "Authorize" button in /docs works correctly.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),  # extracts Bearer token from header
    db: AsyncSession = Depends(get_db),  # injects DB session
) -> User:

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Step 1: decode and verify signature + expiry
        payload = decode_token(token)

        # Step 2: reject refresh tokens used on protected endpoints
        if payload.get("type") != "access":
            raise credentials_error

        # Step 3: extract user identity
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_error

    except JWTError:
        # Covers: invalid signature, expired, malformed
        raise credentials_error

    # Step 4: verify user still exists in DB
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise credentials_error

    # Step 5: verify account is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user  # injected into the route function as current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user),  # reuses get_current_user
) -> User:
    """
    Admin-only dependency. Builds on top of get_current_user.
    WHY compose dependencies like this?
    get_current_admin automatically does everything get_current_user does
    PLUS the role check. No duplication.

    Usage:
        async def admin_route(admin: User = Depends(get_current_admin)):
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
