"""
backend/routers/webhook.py
===========================
Inbound webhook endpoints (called by n8n and user email action links).
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend import models, schemas
from backend.core.dependencies import get_db

logger = logging.getLogger("finguard.webhook")

router = APIRouter(prefix="/api/v1", tags=["Webhooks"])


@router.post("/webhook/n8n", summary="Receive inbound n8n webhook")
async def receive_n8n_webhook(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Called by n8n to notify the backend of automation results
    (e.g., email sent, action received).
    """
    logger.info("n8n webhook received: %s", payload)
    # Acknowledge receipt — business logic can be extended here
    return {"status": "received", "timestamp": datetime.utcnow().isoformat()}


@router.post("/transaction-response", summary="Handle approve/reject from email link")
async def transaction_response(
    body: schemas.VerifyRequest,
    transaction_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Called when a user clicks Approve or Reject in a fraud alert email.
    Validates the token and updates the transaction status.
    """
    now = datetime.now(timezone.utc)

    # Find the verification token
    result = await db.execute(
        select(models.VerificationToken).where(
            models.VerificationToken.token == token,
            models.VerificationToken.is_used == False,  # noqa: E712
        )
    )
    vtoken = result.scalar_one_or_none()

    if not vtoken:
        raise HTTPException(status_code=400, detail="Invalid or already-used token.")

    expires = vtoken.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise HTTPException(status_code=400, detail="Token has expired.")

    if vtoken.action != body.action:
        raise HTTPException(
            status_code=400,
            detail=f"Token is for '{vtoken.action}', not '{body.action}'.",
        )

    # Find the transaction
    txn_result = await db.execute(
        select(models.Transaction).where(models.Transaction.id == vtoken.transaction_id)
    )
    txn = txn_result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")

    # Apply decision
    if str(txn.status).lower() != "pending":
        return HTMLResponse(
            content=f"<h2>This authorization link has already been processed or expired. Current status: {txn.status}</h2>",
            status_code=400,
            headers={"Content-Type": "text/html; charset=utf-8"}
        )

    if body.action == "approve":
        txn.status = models.TransactionStatus.APPROVED.value
        msg = f"Success! Transaction {txn.transaction_id} has been approved."
    else:
        txn.status = models.TransactionStatus.REJECTED.value
        msg = f"Transaction {txn.transaction_id} rejected successfully."

    vtoken.is_used = True
    vtoken.used_at = now

    await db.commit()
    await db.refresh(txn)
    logger.info("Transaction %s %sd via email token.", txn.transaction_id, body.action)

    return HTMLResponse(content=f"<h2>{msg}</h2>", status_code=200)
