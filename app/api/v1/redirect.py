import ipaddress

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.services import analytics_service, link_service

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    """Return the caller's IP if it's a valid IP address, otherwise None."""
    host = request.client.host if request.client else None
    try:
        return str(ipaddress.ip_address(host))
    except (ValueError, TypeError):
        return None


@router.get("/{short_code}")
async def redirect_to_original(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    target = await link_service.resolve_short_code(db, short_code)
    if target is None:
        raise NotFoundError("Link not found")

    # Scheduled now, executed after the response has gone out.
    # We pass plain values (not the Request object) because the task runs later.
    background_tasks.add_task(
        analytics_service.record_click,
        target["id"],
        _client_ip(request),
        request.headers.get("user-agent"),
        request.headers.get("referer"),  # yes, the HTTP spec misspells it
    )
    return RedirectResponse(url=target["url"], status_code=302)
