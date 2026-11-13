# app/core/cursor.py
import base64
import uuid
from datetime import datetime

from app.core.exceptions import BadRequestError


def encode_cursor(clicked_at: datetime, click_id: uuid.UUID) -> str:
    raw = f"{clicked_at.isoformat()}|{click_id}"  # 2026-11-10T06:13:39.252571|<uuid>
    return base64.urlsafe_b64encode(raw.encode()).decode()  # looks opaque to the client


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        ts, cid = raw.split("|")
        return datetime.fromisoformat(ts), uuid.UUID(cid)
    except ValueError:
        # the client sent garbage; every error in the try block is a ValueError
        raise BadRequestError("Invalid cursor")
