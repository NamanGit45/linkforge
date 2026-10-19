import uuid
from sqlalchemy import String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.db.base import Base


class Link(Base):
    __tablename__ = "links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )

    short_code: Mapped[str] = mapped_column(
        String(20), 
        unique=True, 
        index=True, 
        nullable=False
    )

    # The destination URL — what we redirect to
    original_url: Mapped[str] = mapped_column(
        String(2048), 
        nullable=False  # URLs can be long, 2048 is a safe max
    )

    # Optional human-readable title for the dashboard
    title: Mapped[str] = mapped_column(
        String(255), 
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True, 
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False, 
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        nullable=True, 
        onupdate=func.now()
    )

    owner: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Link short_code={self.short_code} url={self.original_url}>"
