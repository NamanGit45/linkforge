from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, LoginRequest, RefreshRequest
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service
from app.core.security import create_access_token, create_refresh_token, decode_token
from jose import JWTError


router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,  # Pydantic filters response through this schema
    status_code=status.HTTP_201_CREATED,  # 201 = Created (not 200 = OK)
)
async def register(
    user_data: UserCreate,  # Pydantic validates request body
    db: AsyncSession = Depends(get_db),  # DB session injected automatically
):

    user = await user_service.register_user(db, user_data)
    return user


# @router.post("/login", response_model=TokenResponse)
# async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):

#     # Verify credentials — raises 401 if invalid
#     user = await user_service.authenticate_user(
#         db, login_data.email, login_data.password
#     )

#     # Create both tokens with user's ID as the subject
#     access_token = create_access_token(subject=str(user.id))
#     refresh_token = create_refresh_token(subject=str(user.id))

# return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    # OAuth2PasswordRequestForm reads form data automatically
    # fields are: form_data.username and form_data.password
    # WHY username and not email?
    # OAuth2 spec uses "username" as the field name.
    # We treat it as email internally.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshRequest, db: AsyncSession = Depends(get_db)
):

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    try:
        payload = decode_token(refresh_data.refresh_token)

        # Reject if someone tries to use an access token as refresh token
        if payload.get("type") != "refresh":
            raise credentials_error

        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_error

    except JWTError:
        raise credentials_error

    # Verify user still exists and is active
    user = await user_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise credentials_error

    # Issue fresh tokens
    new_access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile.
    No DB call needed here — get_current_user already loaded the user.
    We just return what was injected.
    """
    return current_user
