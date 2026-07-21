"""
backend/routers/stats.py
=========================
Dashboard statistics and system metrics endpoints.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend import models, schemas
from backend.core.dependencies import get_db
from backend.services.ml_service import get_feature_importance, _threshold

logger = logging.getLogger("finguard.stats")

router = APIRouter(prefix="/api/v1", tags=["Statistics"])


@router.get("/stats", response_model=schemas.StatsResponse, summary="Dashboard statistics")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate counts for the fraud dashboard summary cards."""
    # Total
    total_result = await db.execute(select(func.count()).select_from(models.Transaction))
    total = total_result.scalar() or 0

    # Auto-approved only (ML score below threshold, no human review needed)
    auto_approved_result = await db.execute(
        select(func.count()).select_from(models.Transaction).where(
            func.lower(models.Transaction.status) == "auto_approved"
        )
    )
    auto_approved = auto_approved_result.scalar() or 0

    # Fraud alerts: rejected + blocked (case-insensitive)
    fraud_alert_result = await db.execute(
        select(func.count()).select_from(models.Transaction).where(
            func.lower(models.Transaction.status).in_(["blocked", "rejected"])
        )
    )
    fraud_alerts = fraud_alert_result.scalar() or 0

    # Pending verifications (awaiting user email response)
    pending_result = await db.execute(
        select(func.count()).select_from(models.Transaction).where(
            func.lower(models.Transaction.status) == "pending"
        )
    )
    pending = pending_result.scalar() or 0

    # Average fraud probability
    avg_result = await db.execute(
        select(func.avg(models.Transaction.fraud_probability))
    )
    avg_prob = float(avg_result.scalar() or 0.0)

    fraud_rate = round((fraud_alerts / total * 100) if total > 0 else 0.0, 2)

    return schemas.StatsResponse(
        total_transactions    = total,
        fraud_alert_count     = fraud_alerts,
        auto_approved_count   = auto_approved,
        pending_count         = pending,
        fraud_rate_percent    = fraud_rate,
        avg_fraud_probability = round(avg_prob, 4),
        model_threshold       = _threshold,
        timestamp             = datetime.utcnow().isoformat(),
    )


@router.get("/metrics", summary="System metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    """Return model feature importances and basic system health metrics."""
    return {
        "feature_importances": get_feature_importance(),
        "timestamp":           datetime.utcnow().isoformat(),
    }
