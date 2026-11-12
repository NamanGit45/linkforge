import logging
import uuid
from datetime import timedelta
from app.db.session import AsyncSessionLocal
from app.models.click import Click
from app.models.link import Link
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def get_link_stats(db: AsyncSession, link: Link) -> dict:
    # Computed by the database clock, not Python's (same reasoning as created_at)
    since = func.now() - timedelta(days=7)
    day = cast(Click.clicked_at, Date)  # timestamp -> just the date, for grouping

    total = await db.scalar(
        select(func.count()).select_from(Click).where(Click.link_id == link.id)
    )
    last_7_days = await db.scalar(
        select(func.count())
        .select_from(Click)
        .where(Click.link_id == link.id, Click.clicked_at >= since)
    )
    daily_rows = await db.execute(
        select(day.label("day"), func.count().label("clicks"))
        .where(Click.link_id == link.id, Click.clicked_at >= since)
        .group_by(day)
        .order_by(day)
    )
    referrer_rows = await db.execute(
        select(Click.referer, func.count().label("clicks"))
        .where(Click.link_id == link.id, Click.referer.is_not(None))
        .group_by(Click.referer)
        .order_by(func.count().desc())  # most clicks first
        .limit(5)
    )

    return {
        "link_id": link.id,
        "total_clicks": total or 0,
        "clicks_last_7_days": last_7_days or 0,
        "daily": [{"day": r.day, "clicks": r.clicks} for r in daily_rows],
        "top_referrers": [
            {"referer": r.referer, "clicks": r.clicks} for r in referrer_rows
        ],
    }
