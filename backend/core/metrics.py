"""
backend/core/metrics.py
========================
Prometheus metrics initialization for application-level monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge

# Business & Fraud metrics
fraud_detection_total = Counter(
    "fraud_detection_total", 
    "Total fraud detection requests", 
    ["is_fraud", "risk_level"]
)

# Latency metrics
fraud_detection_latency_seconds = Histogram(
    "fraud_detection_latency_seconds", 
    "Latency of the complete predict_fraud pipeline"
)

model_prediction_latency_seconds = Histogram(
    "model_prediction_latency_seconds", 
    "Latency of the ML model predict call"
)

rule_engine_latency_seconds = Histogram(
    "rule_engine_latency_seconds", 
    "Latency of the velocity and rule engine evaluation"
)

db_query_latency_seconds = Histogram(
    "db_query_latency_seconds", 
    "Latency of database operations",
    ["operation"]
)

# Concurrency / System state
active_transactions = Gauge(
    "active_transactions", 
    "Number of transactions currently being processed real-time"
)
