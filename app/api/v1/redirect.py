from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.services import link_service

router = APIRouter()


@router.get("/{short_code}")
async def redirect_to_original(short_code: str, db: AsyncSession = Depends(get_db)):
    target = await link_service.resolve_short_code(db, short_code)
    if target is None:
        raise NotFoundError("Link not found")
    return RedirectResponse(url=target["url"], status_code=302)
