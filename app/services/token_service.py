import uuid
from jose import JWTError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import create_refresh_token, decode_token
from app.models.refresh_token import RefreshToken
from app.services import user_service


def _issue(db: AsyncSession, user_id: uuid.UUID, family_id: uuid.UUID) -> str:
    """Create a token + its DB row. Does NOT commit, so the caller decides what
    else belongs in the same transaction (e.g. revoking the old token)."""
    token_id = uuid.uuid4()
    token, expires_at = create_refresh_token(str(user_id), str(token_id))
    db.add(
        RefreshToken(
            id=token_id, user_id=user_id, family_id=family_id, expires_at=expires_at
        )
    )
    return token


async def _revoke_family(db: AsyncSession, family_id: uuid.UUID) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
        .execution_options(synchronize_session=False)
    )


async def start_session(db: AsyncSession, user_id: uuid.UUID) -> str:
    """Login: a brand-new family of tokens."""
    token = _issue(db, user_id, uuid.uuid4())
    await db.commit()
    return token


async def rotate(db: AsyncSession, refresh_token: str) -> tuple[uuid.UUID, str]:
    """Swap a valid refresh token for a new one. Returns (user_id, new_token)."""
    invalid = UnauthorizedError("Invalid or expired refresh token")

    try:
        payload = decode_token(refresh_token)  # checks signature + expiry
        if payload.get("type") != "refresh":
            raise invalid
        token_id = uuid.UUID(payload["jti"])
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise invalid  # includes old tokens that have no jti

    # Atomic claim: in ONE statement, mark it used only if it is still unused and
    # not expired. If two requests race with the same token, Postgres lets exactly
    # one of them change revoked_at from NULL. The database is the referee,
    # the same lesson as the short-code collision.
    family_id = (
        await db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id == token_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > func.now(),
            )
            .values(revoked_at=func.now())
            .returning(RefreshToken.family_id)
            .execution_options(synchronize_session=False)
        )
    ).scalar_one_or_none()

    if family_id is None:
        # Couldn't claim it: unknown, expired, or ALREADY USED.
        row = await db.get(RefreshToken, token_id)
        if row is not None and row.revoked_at is not None:
            await _revoke_family(db, row.family_id)  # replay detected: kill the family
        await db.commit()  # keep the revocation, then reject
        raise invalid

    user = await user_service.get_user_by_id(db, str(user_id))
    if user is None or not user.is_active:
        await db.commit()
        raise invalid

    new_token = _issue(db, user_id, family_id)  # same family, new token
    await db.commit()  # revoke old + insert new, as one unit
    return user_id, new_token


async def revoke_session(db: AsyncSession, refresh_token: str) -> None:
    """Logout. Idempotent: junk or already-dead tokens are silently ignored."""
    try:
        token_id = uuid.UUID(decode_token(refresh_token)["jti"])
    except (JWTError, KeyError, ValueError):
        return
    family_id = await db.scalar(
        select(RefreshToken.family_id).where(RefreshToken.id == token_id)
    )
    if family_id is not None:
        await _revoke_family(db, family_id)
        await db.commit()
