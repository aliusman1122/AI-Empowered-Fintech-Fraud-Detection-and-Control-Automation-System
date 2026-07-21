"""
backend/services/notification_service.py
==========================================
Handles external notifications:
  - Webhook calls to n8n automation platform
  - (Future) Email via SMTP
"""
import logging
from typing import Any

import httpx

from backend.core.config import settings

logger = logging.getLogger("finguard.notification")


async def send_webhook_to_n8n(payload: dict[str, Any]) -> bool:
    """
    POST the payload to the configured n8n webhook URL.
    Returns True on success, False on any network / HTTP error.
    """
    url = settings.N8N_WEBHOOK_URL
    if not url:
        logger.warning("N8N_WEBHOOK_URL is not set — skipping webhook.")
        return False

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info("Webhook sent to n8n (status=%d)", response.status_code)
            return True
    except httpx.HTTPStatusError as exc:
        logger.error("n8n returned error %d: %s", exc.response.status_code, exc.response.text[:200])
        return False
    except Exception as exc:
        logger.error("Failed to reach n8n webhook: %s", exc)
        return False


async def trigger_alert(
    transaction_id: str, 
    fraud_score: float, 
    user_email: str | None = None, 
    currency: str = "USD",
    amount: float = 0.0,
    merchant_category: str = "other",
    country: str = "US"
) -> None:
    """
    Assemble and send a fraud alert webhook to n8n.
    Uses Redis to ensure duplicate webhooks are not sent for the same transaction.
    """
    from backend.core.redis import redis_client

    if redis_client.client:
        cache_key = f"alert_sent:{transaction_id}"
        if await redis_client.client.get(cache_key):
            logger.info("Alert already sent for %s. Skipping duplicate.", transaction_id)
            return
        await redis_client.client.set(cache_key, "1", ex=3600)  # 1 hour cache

    # Convert Enum to string value cleanly
    cat_str = merchant_category.value if hasattr(merchant_category, 'value') else str(merchant_category)
    clean_category = cat_str.replace('MerchantCategory.', '').replace('_', ' ').title()

    payload = {
        "event":           "fraud_alert",
        "transaction_id":  transaction_id,
        "fraud_score":     fraud_score,
        "user_email":      user_email or "",
        "currency":        currency,
        "amount":          str(amount),
        "merchant_category": clean_category,
        "country":         country,
        "action_required": True,
    }
    success = await send_webhook_to_n8n(payload)
    if not success:
        logger.warning("Alert NOT delivered to n8n for transaction %s", transaction_id)
