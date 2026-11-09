from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.services import link_service

router = APIRouter()


@router.get("/{short_code}")
async def redirect_to_original(short_code: str, db: AsyncSession = Depends(get_db)):
    url = await link_service.resolve_short_code(db, short_code)
    if url is None:
        raise NotFoundError("Link not found")
    return RedirectResponse(url=url, status_code=302)
