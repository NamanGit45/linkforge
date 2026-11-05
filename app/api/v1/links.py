from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse, LinkUpdate
from app.services import link_service
from app.schemas.pagination import Page

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


@router.get("", response_model=Page[LinkResponse])
async def list_my_links(
    # Query() validates BEFORE the function runs:
    # limit=0 or limit=5000 returns 422 automatically
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await link_service.get_user_links(db, current_user.id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}


# @router.get("", response_model=list[LinkResponse])
# async def list_my_links(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     return await link_service.get_user_links(db, current_user.id)


@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: uuid.UUID,  # invalid UUID strings get an automatic 422
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await link_service.get_link_for_user(db, link_id, current_user)


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: uuid.UUID,
    data: LinkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await link_service.get_link_for_user(db, link_id, current_user)
    return await link_service.update_link(db, link, data)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await link_service.get_link_for_user(db, link_id, current_user)
    await link_service.delete_link(db, link)
