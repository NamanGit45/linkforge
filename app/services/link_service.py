import secrets
import string
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.models.user import User,UserRole
from app.schemas.link import LinkCreate, LinkUpdate

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


async def get_user_links(
    db: AsyncSession, owner_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[Link], int]:
    # Total count for the client (runs the same WHERE, but returns one number)
    total = await db.scalar(
        select(func.count()).select_from(Link).where(Link.owner_id == owner_id)
    )

    result = await db.execute(
        select(Link)
        .where(Link.owner_id == owner_id)
        # id is the tie-breaker so ordering is stable between pages
        .order_by(Link.created_at.desc(), Link.id)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all()), total or 0


# async def get_user_links(db: AsyncSession, owner_id: uuid.UUID) -> list[Link]:

#     result = await db.execute(
#         select(Link)
#         .where(Link.owner_id == owner_id)
#         .order_by(Link.created_at.desc())  # newest first
#     )
#     return list(result.scalars().all())


async def get_link_for_user(db: AsyncSession, link_id: uuid.UUID, user: User) -> Link:
    """
    The single authorization gate for single-link operations.
    Every route (get/update/delete) goes through this, so the ownership
    rule exists in ONE place. If it were copy-pasted into three routes,
    one would eventually be forgotten, and that's a security hole.
    """
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()

    # Same 404 for "doesn't exist" and "not yours" (no information leak)
    if link is None or (link.owner_id != user.id and user.role != UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
        )
    return link


async def update_link(db: AsyncSession, link: Link, data: LinkUpdate) -> Link:
    changes = data.model_dump(exclude_unset=True)

    # These columns are NOT NULL; an explicit null from the client means "ignore"
    if changes.get("original_url") is None:
        changes.pop("original_url", None)
    else:
        changes["original_url"] = str(changes["original_url"])
    if changes.get("is_active") is None:
        changes.pop("is_active", None)

    for field, value in changes.items():
        setattr(link, field, value)

    await db.commit()
    # refresh is required: we set expire_on_commit=False, so without it
    # updated_at would still show the old value in the response.
    await db.refresh(link)
    return link


async def delete_link(db: AsyncSession, link: Link) -> None:
    await db.delete(link)
    await db.commit()
    # Clicks are removed by the DB itself via ON DELETE CASCADE.
