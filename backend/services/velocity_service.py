"""
backend/services/velocity_service.py
======================================
Stores and retrieves historical user transaction parameters from Redis.
Executes the velocity checks defined in src/velocity_engine.py.
"""
import time
import logging
from typing import Any, Dict, List

from backend.core.redis import redis_client
from src.velocity_engine import evaluate_velocity_rules

logger = logging.getLogger("finguard.velocity")

FIVE_MINUTES = 300
ONE_HOUR = 3600
SEVEN_DAYS = 7 * 24 * 3600

async def get_user_velocity_profile(user_id: int) -> Dict[str, Any]:
    """Retrieve historical transaction stats from Redis for a user."""
    profile = {
        "tx_5m": 0,
        "tx_1h": 0,
        "avg_amount": 0.0
    }
    client = redis_client.client
    if not client:
        return profile
    
    try:
        now = time.time()
        key_list = f"user:{user_id}:tx_history"
        
        # Cleanup old entries (older than 1 hour)
        await client.zremrangebyscore(key_list, 0, now - ONE_HOUR)
        
        # Count transactions in last 5 minutes
        tx_5m = await client.zcount(key_list, now - FIVE_MINUTES, now)
        profile["tx_5m"] = tx_5m

        # Count transactions in last 1 hour
        tx_1h = await client.zcount(key_list, now - ONE_HOUR, now)
        profile["tx_1h"] = tx_1h

        # Get historical average amount from a string key
        key_avg = f"user:{user_id}:avg_amount"
        avg_str = await client.get(key_avg)
        if avg_str:
            profile["avg_amount"] = float(avg_str)
            
    except Exception as e:
        logger.warning(f"Failed to fetch velocity profile from Redis: {e}")
        
    return profile


async def check_velocity_rules(user_id: int | None, transaction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluates velocity rules and returns triggered ones."""
    if not user_id:
        return evaluate_velocity_rules(transaction_data, None)

    profile = await get_user_velocity_profile(user_id)
    return evaluate_velocity_rules(transaction_data, profile)


async def store_transaction_velocity(user_id: int | None, transaction_data: Dict[str, Any]) -> None:
    """Stores transaction in Redis and updates user averages."""
    if not user_id:
        return
        
    client = redis_client.client
    if not client:
        return
        
    try:
        now = time.time()
        key_list = f"user:{user_id}:tx_history"
        
        # Add to sorted set to track tx count over time
        amt = float(transaction_data.get("amount", 0))
        member = f"{now}_{amt}"
        await client.zadd(key_list, {member: now})
        await client.expire(key_list, ONE_HOUR)
        
        # Update running average (simplified: blend 90% old + 10% new)
        key_avg = f"user:{user_id}:avg_amount"
        avg_str = await client.get(key_avg)
        
        if avg_str:
            old_avg = float(avg_str)
            new_avg = (old_avg * 0.9) + (amt * 0.1)
        else:
            new_avg = amt
            
        await client.set(key_avg, str(new_avg), ex=SEVEN_DAYS)
        
    except Exception as e:
        logger.warning(f"Failed to store velocity in Redis: {e}")
