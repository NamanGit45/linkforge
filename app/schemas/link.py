import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, computed_field

from app.core.config import settings


class LinkCreate(BaseModel):
    """What the client sends to create a link."""

    # HttpUrl validates the format: "hello" is rejected, "ftp://x" is rejected.
    # Note: Pydantic v2 gives you a Url OBJECT, not a str.
    # We convert with str() in the service before saving to the DB.
    original_url: HttpUrl
    title: str | None = Field(default=None, max_length=255)


class LinkResponse(BaseModel):

    id: uuid.UUID
    short_code: str
    original_url: str
    title: str | None
    is_active: bool
    created_at: datetime

    # computed_field: not stored in the DB, calculated when building the response.
    # The client gets a ready-to-share link without us storing redundant data
    @computed_field
    @property
    def short_url(self) -> str:
        return f"{settings.BASE_URL}/r/{self.short_code}"

    model_config = {"from_attributes": True}
