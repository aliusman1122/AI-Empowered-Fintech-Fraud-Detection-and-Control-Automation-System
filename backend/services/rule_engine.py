"""
backend/services/rule_engine.py
================================
Combines ML and Business Rule scores into a final decision.
"""
from typing import Any, Dict, List
import structlog
from backend.core import metrics

logger = structlog.get_logger("finguard.rules")

@metrics.rule_engine_latency_seconds.time()
def evaluate_rules(transaction_data: Dict[str, Any], user_profile: Dict[str, Any] | None, velocity_data: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """
    Returns rule results based on velocity_data and transaction_data.
    Delegates to the configured velocity engine.
    """
    from src.velocity_engine import evaluate_velocity_rules
    return evaluate_velocity_rules(transaction_data, velocity_data)


def combine_scores(ml_score: float, rule_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Final score = (ML_score * 0.7) + (rule_score * 0.3)
    Returns updated score and updated risk label.
    """
    if not rule_results:
        rule_score = 0.0
    else:
        rule_score = max((float(r["score"]) for r in rule_results), default=0.0)
        
    final_score = (ml_score * 0.7) + (rule_score * 0.3)
    
    def get_risk_level(s: float) -> str:
        if s >= 0.90: return "CRITICAL"
        if s >= 0.70: return "HIGH"
        if s >= 0.50: return "MEDIUM"
        return "LOW"
        
    return {
        "final_score": round(final_score, 4),
        "rule_score": round(rule_score, 4),
        "risk_level": get_risk_level(final_score),
    }
