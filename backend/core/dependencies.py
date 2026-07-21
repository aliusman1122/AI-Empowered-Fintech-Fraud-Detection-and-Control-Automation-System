"""
backend/core/dependencies.py
=============================
FastAPI dependency functions used across routers.
  - get_db()                  : per-request AsyncSession
  - get_current_user()        : JWT → User (async)
  - require_admin()           : RBAC guard — admin only
  - require_analyst_or_above(): RBAC guard — analyst or admin
  - limiter                   : slowapi rate limiter instance
"""
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.security import verify_access_token
from backend.database import get_async_session
from backend import models

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    # Removed default_limits because it crashes FastAPI /docs internal routes via parameter mismatches
)

# ── HTTP Bearer token extractor ─────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


# ── Database session ─────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a per-request AsyncSession from the async engine."""
    async for session in get_async_session():
        yield session


# ── Current user ─────────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> models.User:
    """
    Async FastAPI dependency:
    1. Extracts Bearer token from Authorization header
    2. Decodes + validates JWT (access token)
    3. Loads user from DB, checks is_active
    Returns the live User ORM object.
    """
    if credentials is None:
        raise _credentials_exc

    payload = verify_access_token(credentials.credentials)

    user_id: int | None = payload.get("user_id")
    if user_id is None:
        raise _credentials_exc

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user   = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise _credentials_exc

    return user


# ── RBAC guards ───────────────────────────────────────────────────────────────
async def require_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if current_user.role != models.UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


async def require_analyst_or_above(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    allowed = {models.UserRole.admin.value, models.UserRole.analyst.value}
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or Admin access required.",
        )
    return current_user
