"""
backend/services/transaction_service.py
=========================================
Business logic for transaction processing and fraud prediction.
All DB interactions go through the transaction_repository.
"""
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend import models
from backend.repositories import transaction_repository
from backend.services import ml_service
from backend.core import metrics
import structlog
import time

logger = structlog.get_logger("finguard.transaction")

# Fraud probability threshold bands
def _risk_level(score: float) -> str:
    if score >= 0.90: return "CRITICAL"
    if score >= 0.70: return "HIGH"
    if score >= 0.50: return "MEDIUM"
    return "LOW"


def _reason_codes(data: dict, score: float) -> list[str]:
    """Generate human-readable reason codes from input features."""
    reasons = []
    if data.get("device_risk_score", 0) >= 0.7:
        reasons.append(f"High device risk score ({data['device_risk_score']:.2f})")
    if data.get("ip_risk_score", 0) >= 0.7:
        reasons.append(f"High IP risk score ({data['ip_risk_score']:.2f})")
    hour = data.get("hour", data.get("transaction_hour", 12))
    if hour < 6 or hour > 22:
        reasons.append(f"Unusual transaction hour ({hour}:00)")
    cat = data.get("merchant_category", "")
    if cat in ("gambling", "crypto", "wire_transfer", "foreign_exchange", "international_wire"):
        reasons.append(f"High-risk merchant category: {cat}")
    if data.get("amount", 0) > 50_000:
        reasons.append(f"Large transaction amount (${data['amount']:,.2f})")
    if score >= 0.50 and not reasons:
        reasons.append("Elevated fraud probability from ML model")
    return reasons


async def predict_fraud(transaction_data: dict, user_id: int | None = None) -> dict:
    """
    Run ML model and rule engine on transaction data.
    Does NOT save to database.
    """
    from backend.services.velocity_service import check_velocity_rules
    from backend.services.rule_engine import combine_scores
    
    # 1. Run velocity/business checks
    rule_results = await check_velocity_rules(user_id, transaction_data)
    
    # 2. Base ML prediction
    ml_result   = ml_service.predict(transaction_data)
    ml_score    = ml_result["fraud_probability"]
    
    # 3. Combine scores using weights
    final_eval  = combine_scores(ml_score, rule_results)
    final_score = final_eval["final_score"]
    risk_level  = final_eval["risk_level"]
    
    base_reasons = _reason_codes(transaction_data, ml_score)
    triggered_reasons = [r["rule_name"] for r in rule_results]
    reason_codes = base_reasons + triggered_reasons

    fraud_flag = final_score >= ml_result["threshold_used"]

    # Determine status label for the frontend
    if not fraud_flag:
        status_label = "AUTO_APPROVED"
        message      = f"Transaction approved automatically (fraud probability: {final_score:.1%})"
    else:
        status_label = "PENDING"
        message      = f"Transaction flagged for review (fraud probability: {final_score:.1%})"
        
    metrics.fraud_detection_total.labels(is_fraud=str(fraud_flag).lower(), risk_level=risk_level).inc()

    return {
        "fraud_probability": final_score,
        "fraud_flag":        fraud_flag,
        "risk_level":        risk_level,
        "reason_codes":      reason_codes,
        "status":            status_label,
        "message":           message,
        "threshold_used":    ml_result["threshold_used"],
    }


async def create_transaction(
    db: AsyncSession,
    transaction_data: dict,
    user_id: int | None = None,
) -> models.Transaction:
    """
    Run fraud prediction and persist the transaction to the database.
    """
    from backend.services.velocity_service import store_transaction_velocity
    
    start_time = time.perf_counter()
    metrics.active_transactions.inc()
    try:
        prediction = await predict_fraud(transaction_data, user_id)
        
        await store_transaction_velocity(user_id, transaction_data)
        
        txn_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"

        row = {
            "transaction_id":    txn_id,
            "user_id":           user_id,
            "amount":            transaction_data.get("amount"),
            "merchant_category": str(transaction_data.get("merchant_category", "other")),
            "transaction_hour":  transaction_data.get("hour", transaction_data.get("transaction_hour", 12)),
            "device_risk_score": transaction_data.get("device_risk_score", 0.0),
            "ip_risk_score":     transaction_data.get("ip_risk_score", 0.0),
            "fraud_probability": prediction["fraud_probability"],
            "fraud_flag":        prediction["fraud_flag"],
            "reason_codes":      json.dumps(prediction["reason_codes"]),
            "risk_level":        prediction["risk_level"],
            "risk_score":        prediction["fraud_probability"],
            "transaction_type":  transaction_data.get("transaction_type", "online"),
            "country":           transaction_data.get("country", "US"),
            "user_email":        transaction_data.get("user_email"),
            "status":            prediction["status"],
        }

        txn = await transaction_repository.create(db, row)
        
        # Broadcast via Redis Pub/Sub for SSE clients
        from backend.core.redis import redis_client
        if redis_client.client:
            try:
                txn_dict = {
                    "id": txn.id,
                    "transaction_id": txn.transaction_id,
                    "amount": float(txn.amount),
                    "merchant_category": txn.merchant_category,
                    "fraud_probability": float(txn.fraud_probability),
                    "fraud_flag": txn.fraud_flag,
                    "risk_level": txn.risk_level,
                    "status": txn.status,
                    "timestamp": txn.timestamp.isoformat() if txn.timestamp else None,
                    "country": txn.country,
                }
                await redis_client.client.publish("transactions_channel", json.dumps(txn_dict))
            except Exception as e:
                logger.warning("failed_to_publish_redis", error=str(e), transaction_id=txn.transaction_id)
                
        return txn
    finally:
        metrics.active_transactions.dec()
        duration = time.perf_counter() - start_time
        metrics.fraud_detection_latency_seconds.observe(duration)


async def get_transactions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Transaction]:
    return await transaction_repository.get_all(db, skip=skip, limit=limit)


async def get_transaction_by_id(
    db: AsyncSession,
    transaction_id: int,
) -> models.Transaction | None:
    return await transaction_repository.get_by_id(db, transaction_id)
