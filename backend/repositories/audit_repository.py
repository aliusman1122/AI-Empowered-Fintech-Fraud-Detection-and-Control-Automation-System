"""
backend/repositories/audit_repository.py
==========================================
Async data-access layer for AuditLog.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models


async def create_log(db: AsyncSession, log_data: dict) -> models.AuditLog:
    """Insert an audit log entry."""
    entry = models.AuditLog(**log_data)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_logs(
    db: AsyncSession,
    user_id: int | None = None,
    limit: int = 100,
) -> list[models.AuditLog]:
    """Return audit logs, optionally filtered by user_id, newest first."""
    stmt = select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(limit)
    if user_id is not None:
        stmt = stmt.where(models.AuditLog.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
