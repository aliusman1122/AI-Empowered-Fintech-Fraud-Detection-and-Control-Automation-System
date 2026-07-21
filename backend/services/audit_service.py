"""
backend/services/audit_service.py
===================================
Business logic for audit trail management.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories import audit_repository

logger = logging.getLogger("finguard.audit")


async def log_action(
    db: AsyncSession,
    action: str,
    transaction_id: int,
    user_id: int | None = None,
    entity_type: str = "transaction",
    entity_id: int | None = None,
    old_status: str | None = None,
    new_status: str | None = None,
    performed_by: str = "system",
    description: str | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> None:
    """
    Write one entry to the audit_logs table.
    Never raises — audit failures are only logged, never propagated.
    """
    try:
        log_data = {
            "transaction_id": transaction_id,
            "user_id":        user_id,
            "action":         action,
            "description":    description or (str(details) if details else None),
            "old_status":     old_status,
            "new_status":     new_status,
            "performed_by":   performed_by,
            "ip_address":     ip_address,
        }
        await audit_repository.create_log(db, log_data)
    except Exception as exc:
        logger.error("Audit log write failed: %s", exc)


async def get_audit_trail(
    db: AsyncSession,
    user_id: int | None = None,
    limit: int = 100,
) -> list:
    """Return audit log entries, optionally filtered by user."""
    return await audit_repository.get_logs(db, user_id=user_id, limit=limit)
