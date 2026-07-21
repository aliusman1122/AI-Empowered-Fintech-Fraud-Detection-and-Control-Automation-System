"""
backend/routers/health.py
==========================
Health and readiness check endpoints.
These are called by Docker, Kubernetes, and load balancers.
No auth required.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import os

from backend.core.dependencies import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Liveness check")
async def health():
    """Always returns 200 OK as long as the process is running."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready", summary="Readiness check")
async def ready(db: AsyncSession = Depends(get_db)):
    """
    Returns 200 if all dependencies are reachable, 503 otherwise.
    Used by Docker healthcheck and orchestrators.
    """
    checks = {}
    
    # 1. Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"unreachable: {e}"
        
    # 2. Redis
    try:
        from backend.core.redis import redis_client
        if not await redis_client.ping():
            raise Exception("Ping failed")
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"unreachable: {e}"
        
    # 3. MLflow
    try:
        uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(uri)
            resp.raise_for_status()
        checks["mlflow"] = "ok"
    except Exception as e:
        checks["mlflow"] = f"unreachable: {e}"
        
    # 4. ML Model
    try:
        from backend.services.ml_service import _model
        checks["ml_model"] = "loaded" if _model is not None else "not_loaded"
    except Exception as e:
        checks["ml_model"] = f"error: {e}"

    if any(status not in ("ok", "loaded") for status in checks.values()):
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "checks": checks},
        )

    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
