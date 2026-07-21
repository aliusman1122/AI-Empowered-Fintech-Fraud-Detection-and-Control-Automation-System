"""
backend/routers/transactions.py
================================
Transaction endpoints — submission, listing, and pure ML prediction.
"""
import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend import schemas, models
from backend.core.dependencies import get_db, get_current_user, limiter
from backend.core.config import settings
from backend.core.redis import redis_client
from backend.repositories import transaction_repository
from backend.services import transaction_service, notification_service, audit_service

logger = logging.getLogger("finguard.transactions")

router = APIRouter(prefix="/api/v1", tags=["Transactions"])


# ── GET /transactions/stream (Server-Sent Events) ─────────────────────────

@router.get(
    "/transactions/stream",
    summary="Stream real-time transactions (SSE)",
)
async def stream_transactions():
    """Stream real-time transactions from Redis PubSub."""
    async def event_generator():
        client = redis_client.client
        if not client:
            yield "data: {\"error\": \"Redis not connected\"}\n\n"
            return
            
        pubsub = client.pubsub()
        await pubsub.subscribe("transactions_channel")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None:
                    data = message["data"]
                    yield f"data: {data}\n\n"
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            await pubsub.unsubscribe("transactions_channel")
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── POST /transactions/predict  (pure ML, no DB write) ───────────────────────

@router.post(
    "/transactions/predict",
    response_model=schemas.PredictionResponse,
    summary="Predict fraud probability (without saving)",
)
@limiter.limit("200/minute")
async def predict_only(
    request: Request,
    body: schemas.TransactionInput,
):
    """Run the ML model and return a fraud score without persisting anything."""
    data   = body.model_dump()
    result = await transaction_service.predict_fraud(data)

    return schemas.PredictionResponse(
        transaction_id    = "PREVIEW",
        fraud_probability = result["fraud_probability"],
        fraud_flag        = result["fraud_flag"],
        risk_level        = result["risk_level"],
        status            = result["status"],
        reason_codes      = result["reason_codes"],
        message           = result["message"],
        threshold_used    = result["threshold_used"],
    )


# ── POST /transactions  (create + save) ──────────────────────────────────────

@router.post(
    "/transactions",
    response_model=schemas.PredictionResponse,
    status_code=201,
    summary="Submit a transaction for fraud analysis",
)
@limiter.limit("200/minute")
async def create_transaction(
    request: Request,
    body: schemas.TransactionInput,
    db: AsyncSession = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user),
):
    user_id = current_user.id if current_user else None
    data    = body.model_dump()
    
    # Extract dynamic frontend context bypassing static ORM boundaries
    currency = data.pop("currency", "USD")
    
    txn     = await transaction_service.create_transaction(db, data, user_id=user_id)

    # Fire-and-forget webhook to n8n if fraud detected
    if txn.fraud_flag:
        try:
            await notification_service.trigger_alert(
                txn.transaction_id,
                txn.fraud_probability,
                user_email=txn.user_email,
                currency=currency,
                amount=txn.amount,
                merchant_category=txn.merchant_category,
                country=txn.country,
            )
        except Exception as exc:
            logger.warning("Webhook trigger failed: %s", exc)

    reason_codes = json.loads(txn.reason_codes) if txn.reason_codes else []

    # Build a user-facing message that reflects the actual fraud decision
    fraud_prob_pct = (txn.fraud_probability or 0.0) * 100
    if txn.fraud_flag:
        txn_message = (
            f"High Fraud Risk Detected ({fraud_prob_pct:.1f}%)! "
            "Verification email sent for human authorization."
        )
    else:
        txn_message = f"Transaction approved automatically (fraud probability: {fraud_prob_pct:.1f}%)."

    return schemas.PredictionResponse(
        transaction_id    = txn.transaction_id,
        fraud_probability = txn.fraud_probability or 0.0,
        fraud_flag        = txn.fraud_flag or False,
        risk_level        = txn.risk_level or "LOW",
        status            = txn.status,
        reason_codes      = reason_codes,
        message           = txn_message,
        threshold_used    = 0.5,
    )


# ── GET /transactions  (list) ─────────────────────────────────────────────────

@router.get(
    "/transactions",
    response_model=list[schemas.TransactionListItem],
    summary="List all transactions",
)
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    skip:  int = Query(default=0,   ge=0),
    limit: int = Query(default=100, ge=1, le=500),
):
    txns = await transaction_service.get_transactions(db, skip=skip, limit=limit)
    return txns


# ── GET /transactions/{transaction_id} ────────────────────────────────────────

@router.get(
    "/transactions/{transaction_id}",
    response_model=schemas.TransactionStatusResponse,
    summary="Get a single transaction by ID",
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    txn = await transaction_repository.get_by_txn_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id!r} not found.")
    return schemas.TransactionStatusResponse(
        transaction_id    = txn.transaction_id,
        status            = txn.status,
        fraud_probability = txn.fraud_probability,
        fraud_flag        = txn.fraud_flag,
        risk_level        = txn.risk_level,
        amount            = txn.amount,
        created_at        = txn.created_at,
        updated_at        = txn.updated_at,
        message           = f"Transaction {txn.transaction_id} — status: {txn.status}",
    )


# ── POST /transactions/{transaction_id}/approve ───────────────────────────────

@router.post(
    "/transactions/{transaction_id}/approve",
    summary="Approve a transaction",
)
async def approve_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    txn = await transaction_repository.get_by_txn_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if str(txn.status).lower() != "pending":
        return HTMLResponse(
            content=f"<h2>This authorization link has already been processed or expired. Current status: {txn.status}</h2>",
            status_code=400,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )
        
    old_status = txn.status
    txn.status = models.TransactionStatus.APPROVED.value
    
    # Audit log
    audit_log = models.AuditLog(
        transaction_id=txn.id,
        user_id=txn.user_id,
        action="USER_APPROVED",
        old_status=old_status,
        new_status=txn.status,
        performed_by="user",
        description="Transaction approved via n8n webhook"
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(txn)
    
    return HTMLResponse(
        content=f"<h2>Success! Transaction {transaction_id} has been approved.</h2>",
        status_code=200
    )


# ── POST /transactions/{transaction_id}/reject ────────────────────────────────

@router.post(
    "/transactions/{transaction_id}/reject",
    summary="Reject/Block a transaction",
)
async def reject_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    txn = await transaction_repository.get_by_txn_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if str(txn.status).lower() != "pending":
        return HTMLResponse(
            content=f"<h2>This authorization link has already been processed or expired. Current status: {txn.status}</h2>",
            status_code=400,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )
        
    old_status = txn.status
    txn.status = models.TransactionStatus.REJECTED.value
    
    # Audit log
    audit_log = models.AuditLog(
        transaction_id=txn.id,
        user_id=txn.user_id,
        action="USER_REJECTED",
        old_status=old_status,
        new_status=txn.status,
        performed_by="user",
        description="Transaction rejected via n8n webhook"
    )
    db.add(audit_log)
    await db.commit()
    await db.refresh(txn)
    
    return HTMLResponse(
        content=f"<h2>Transaction {transaction_id} rejected successfully.</h2>",
        status_code=200
    )
