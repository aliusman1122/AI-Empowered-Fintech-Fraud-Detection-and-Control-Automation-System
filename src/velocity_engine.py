"""
src/velocity_engine.py
=======================
Defines the velocity rules and configurations for real-time fraud detection.
These rules evaluate transaction patterns independently of the ML model.
"""

from typing import Any, Dict, List

# Rule Definitions
VELOCITY_RULES = {
    "VEL_001": {
        "name": "High Frequency (5 Min)",
        "description": "Same user > 3 transactions in 5 minutes",
        "severity": "HIGH",
        "score": 0.8
    },
    "VEL_002": {
        "name": "High Frequency (1 Hour)",
        "description": "Same user > 5 transactions in 1 hour",
        "severity": "MEDIUM",
        "score": 0.5
    },
    "VEL_003": {
        "name": "Unusual Amount",
        "description": "Transaction amount > 3x user's historical average",
        "severity": "HIGH",
        "score": 0.8
    },
    "VEL_004": {
        "name": "New Device",
        "description": "Transaction from new device (device risk score > 0.8)",
        "severity": "MEDIUM",
        "score": 0.5
    },
    "VEL_005": {
        "name": "Unusual Hour",
        "description": "Transaction at unusual hour (2 AM - 5 AM)",
        "severity": "LOW",
        "score": 0.2
    }
}

def evaluate_velocity_rules(transaction: Dict[str, Any], profile: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """
    Evaluates business rules against the current transaction and user velocity profile.
    Returns a list of triggered rules.
    """
    triggered = []
    
    # Empty profile fallback
    if not profile:
        profile = {
            "tx_5m": 0,
            "tx_1h": 0,
            "avg_amount": float(transaction.get("amount", 0))
        }

    # Rule 1: > 3 tx in 5 minutes
    if profile.get("tx_5m", 0) >= 3:
        triggered.append({
            "rule_id": "VEL_001",
            "rule_name": VELOCITY_RULES["VEL_001"]["name"],
            "severity": VELOCITY_RULES["VEL_001"]["severity"],
            "score": VELOCITY_RULES["VEL_001"]["score"]
        })

    # Rule 2: > 5 tx in 1 hour
    if profile.get("tx_1h", 0) >= 5:
        triggered.append({
            "rule_id": "VEL_002",
            "rule_name": VELOCITY_RULES["VEL_002"]["name"],
            "severity": VELOCITY_RULES["VEL_002"]["severity"],
            "score": VELOCITY_RULES["VEL_002"]["score"]
        })

    # Rule 3: > 3x avg amount
    amt = float(transaction.get("amount", 0))
    avg_amt = float(profile.get("avg_amount", 0))
    # only apply if they have a history (avg > 0) and the amount itself is not trivial (e.g. > $10)
    if avg_amt > 0 and amt > (3 * avg_amt) and amt > 10:
        triggered.append({
            "rule_id": "VEL_003",
            "rule_name": VELOCITY_RULES["VEL_003"]["name"],
            "severity": VELOCITY_RULES["VEL_003"]["severity"],
            "score": VELOCITY_RULES["VEL_003"]["score"]
        })

    # Rule 4: New device (proxied by high device risk in input data)
    # The prompt says "Transaction from new device -> MEDIUM risk"
    device_risk = float(transaction.get("device_risk_score", 0))
    if device_risk > 0.8:
        triggered.append({
            "rule_id": "VEL_004",
            "rule_name": VELOCITY_RULES["VEL_004"]["name"],
            "severity": VELOCITY_RULES["VEL_004"]["severity"],
            "score": VELOCITY_RULES["VEL_004"]["score"]
        })

    # Rule 5: Unusual hour (2 AM - 5 AM)
    hour = int(transaction.get("hour", transaction.get("transaction_hour", 12)))
    if 2 <= hour <= 5:
        triggered.append({
            "rule_id": "VEL_005",
            "rule_name": VELOCITY_RULES["VEL_005"]["name"],
            "severity": VELOCITY_RULES["VEL_005"]["severity"],
            "score": VELOCITY_RULES["VEL_005"]["score"]
        })

    return triggered
