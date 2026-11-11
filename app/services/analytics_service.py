# app/services/analytics_service.py
import logging
import uuid

from app.db.session import AsyncSessionLocal
from app.models.click import Click

logger = logging.getLogger("linkforge.analytics")


async def record_click(
    link_id: str,
    ip: str | None,
    user_agent: str | None,
    referer: str | None,
) -> None:
    """
    Runs AFTER the redirect has been sent. It must never raise: nobody is
    waiting for it, so an exception here would only produce confusing noise.
    """
    try:
        # Its own session. The route's session belongs to the request and may
        # already be closed by the time this runs.
        async with AsyncSessionLocal() as session:
            session.add(
                Click(
                    link_id=uuid.UUID(link_id),  # the cache stores the id as text
                    ip_address=ip,
                    user_agent=(
                        user_agent[:512] if user_agent else None
                    ),  # column limits
                    referer=referer[:2048] if referer else None,
                )
            )
            await session.commit()
    except Exception:
        logger.exception("Failed to record click for link %s", link_id)
