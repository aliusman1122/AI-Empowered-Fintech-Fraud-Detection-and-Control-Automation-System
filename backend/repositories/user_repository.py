"""
backend/repositories/user_repository.py
=========================================
Async data-access layer for the User table.
All DB interactions are isolated here — no business logic.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models


async def create_user(db: AsyncSession, user_data: dict) -> models.User:
    """Insert a new User row and return the refreshed ORM object."""
    user = models.User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_by_email(db: AsyncSession, email: str) -> models.User | None:
    """Fetch a user by email address. Returns None if not found."""
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> models.User | None:
    """Fetch a user by primary key. Returns None if not found."""
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()
