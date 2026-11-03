import secrets
import string
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.user import User
from app.schemas.link import LinkCreate

# 62 characters: a-z, A-Z, 0-9
ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 7
MAX_RETRIES = 5


def generate_short_code(length: int = CODE_LENGTH) -> str:
    # secrets (not random): cryptographically secure, so codes aren't predictable
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


async def create_link(db: AsyncSession, owner: User, data: LinkCreate) -> Link:
    """
    Insert first, handle collisions after.
    We do NOT check "does this code exist?" before inserting, because
    two simultaneous requests could both pass that check (race condition).
    The UNIQUE index on short_code is the real guarantee.
    """
    for _ in range(MAX_RETRIES):
        link = Link(
            short_code=generate_short_code(),
            original_url=str(data.original_url),  # Url object -> plain string
            title=data.title,
            owner_id=owner.id,  # comes from the verified JWT user, NEVER from the client
        )
        db.add(link)
        try:
            await db.commit()
            await db.refresh(link)
            return link
        except IntegrityError:
            # Code collision: undo this failed transaction and retry with a new code
            await db.rollback()

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Could not generate a unique short code, please try again",
    )


async def get_user_links(db: AsyncSession, owner_id: uuid.UUID) -> list[Link]:
    
    result = await db.execute(
        select(Link)
        .where(Link.owner_id == owner_id)
        .order_by(Link.created_at.desc())  # newest first
    )
    return list(result.scalars().all())
