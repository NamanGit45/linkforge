import uuid
from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, INET
from datetime import datetime

from app.db.base import Base


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )

    link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
    )

    # INET is a Postgres-specific type for IP addresses.
    # Stores both IPv4 and IPv6, validates format at DB level.
    # nullable=True because some requests may not have a real IP (proxies, etc.)
    ip_address: Mapped[str] = mapped_column(
        INET, 
        nullable=True
    )

    # The Referer header — tells you where the click came from
    # e.g. "https://twitter.com" means someone clicked your link on Twitter
    referer: Mapped[str] = mapped_column(
        String(2048), 
        nullable=True
    )

    user_agent: Mapped[str] = mapped_column(
        String(512), 
        nullable=True
    )

    clicked_at: Mapped[datetime] = mapped_column(
        nullable=False, 
        server_default=func.now()
    )

    link: Mapped["Link"] = relationship("Link", lazy="selectin")

    # WHY a composite index on (link_id, clicked_at)?
    # Our analytics queries will almost always be:
    # "give me all clicks for link X, sorted by time"
    # A composite index covering both columns makes this query instant.
    # Single index on link_id alone would work but the composite is faster
    # for time-range queries like "clicks this week for link X"
    __table_args__ = (Index("ix_clicks_link_id_clicked_at", "link_id", "clicked_at"),)

    def __repr__(self) -> str:
        return f"<Click link_id={self.link_id} at={self.clicked_at}>"
