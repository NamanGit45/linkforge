import uuid
from datetime import date
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
