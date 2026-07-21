"""
backend/repositories/refresh_token_repository.py
=================================================
Async data-access layer for RefreshToken.
These are the async equivalents of the sync functions in auth_service.py.
auth_service.py is NOT modified — routers use this module for DB ops.
"""
import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models


def _hash(raw_token: str) -> str:
    """SHA-256 hash for safe server-side storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def store_hash(
    db: AsyncSession,
    user_id: int,
    raw_token: str,
    expires_at: datetime,
    device_info: str | None = None,
) -> models.RefreshToken:
    """Persist a hashed refresh token."""
    token_hash = _hash(raw_token)
    db_token   = models.RefreshToken(
        user_id     = user_id,
        token_hash  = token_hash,
        device_info = device_info,
        expires_at  = expires_at,
        is_revoked  = False,
    )
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def revoke(db: AsyncSession, raw_token: str) -> bool:
    """Mark a refresh token as revoked. Returns True if found and revoked."""
    token_hash = _hash(raw_token)
    result = await db.execute(
        select(models.RefreshToken).where(
            models.RefreshToken.token_hash == token_hash,
            models.RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        return False
    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return True


async def validate_hash(db: AsyncSession, raw_token: str) -> models.RefreshToken | None:
    """
    Return a valid (non-revoked, non-expired) RefreshToken row for this raw token,
    or None if invalid.
    """
    token_hash = _hash(raw_token)
    result = await db.execute(
        select(models.RefreshToken).where(
            models.RefreshToken.token_hash == token_hash,
            models.RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    db_token = result.scalar_one_or_none()
    if db_token is None:
        return None
    # Check DB-level expiry
    expires = db_token.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < datetime.now(timezone.utc):
        return None
    return db_token


async def get_by_token_hash(db: AsyncSession, token_hash: str) -> models.RefreshToken | None:
    """Fetch a RefreshToken by its pre-computed hash."""
    result = await db.execute(
        select(models.RefreshToken).where(models.RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()
