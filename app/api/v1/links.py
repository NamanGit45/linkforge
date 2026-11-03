from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse
from app.services import link_service

router = APIRouter()


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    data: LinkCreate,
    current_user: User = Depends(
        get_current_user
    ),  # this one line makes the route protected
    db: AsyncSession = Depends(get_db),
):
    return await link_service.create_link(db, current_user, data)


@router.get("", response_model=list[LinkResponse])
async def list_my_links(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await link_service.get_user_links(db, current_user.id)
