import uuid
from datetime import date , datetime
from pydantic import BaseModel


class DailyClicks(BaseModel):
    day: date
    clicks: int


class ReferrerCount(BaseModel):
    referer: str
    clicks: int


class LinkStats(BaseModel):
    link_id: uuid.UUID
    total_clicks: int
    clicks_last_7_days: int
    daily: list[DailyClicks]
    top_referrers: list[ReferrerCount]


class ClickResponse(BaseModel):
    id: uuid.UUID
    clicked_at: datetime
    ip_address: str | None
    referer: str | None
    user_agent: str | None
