"""
backend/repositories/transaction_repository.py
===============================================
Async data-access layer for the Transaction table.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models


async def create(db: AsyncSession, transaction_data: dict) -> models.Transaction:
    """Insert a new Transaction and return it."""
    txn = models.Transaction(**transaction_data)
    db.add(txn)
    await db.commit()
    await db.refresh(txn)
    return txn


async def get_by_id(db: AsyncSession, transaction_id: int) -> models.Transaction | None:
    """Fetch a transaction by its integer primary key."""
    result = await db.execute(
        select(models.Transaction).where(models.Transaction.id == transaction_id)
    )
    return result.scalar_one_or_none()


async def get_by_txn_id(db: AsyncSession, transaction_id: str) -> models.Transaction | None:
    """Fetch a transaction by its human-readable string ID (e.g. 'TXN-ABCD1234')."""
    result = await db.execute(
        select(models.Transaction).where(models.Transaction.transaction_id == transaction_id)
    )
    return result.scalar_one_or_none()


async def get_all(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Transaction]:
    """Return all transactions ordered by creation time (newest first), with pagination."""
    result = await db.execute(
        select(models.Transaction)
        .order_by(models.Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_by_user(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Transaction]:
    """Return transactions belonging to a specific user."""
    result = await db.execute(
        select(models.Transaction)
        .where(models.Transaction.user_id == user_id)
        .order_by(models.Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
