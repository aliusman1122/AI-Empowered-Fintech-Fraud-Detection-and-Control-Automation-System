"""
backend/services/ml_service.py
================================
ML model lifecycle management.
  - load_model_on_startup() is called from main.py startup event
  - predict() is called per request from transaction_service
  - get_feature_importance() exposes model explainability info
"""
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import structlog
from backend.core import metrics

logger = structlog.get_logger("finguard.ml")

# Module-level model holder — populated once on startup
_model: Any = None
_threshold: float = 0.5

# Path to model files (root-level models/ folder)
_MODEL_DIR = Path(__file__).parents[2] / "models"
_PIPELINE_PATH  = _MODEL_DIR / "fraud_pipeline.joblib"
_THRESHOLD_PATH = _MODEL_DIR / "threshold.json"


import os

from backend.core.config import settings

def load_model_from_registry() -> bool:
    """Attempt to load the production model from MLflow Registry."""
    global _model
    
    # Restrict MLflow network retries to prevent startup freeze when unreachable
    os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] = "1"
    os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = "2"
    
    mlflow_uri = settings.MLFLOW_TRACKING_URI
    model_name = "finguard_fraud_model"
    stage = getattr(settings, "MLFLOW_MODEL_STAGE", "Production").capitalize()
    
    try:
        import mlflow
        mlflow.set_tracking_uri(mlflow_uri)
        model_uri = f"models:/{model_name}/{stage}"
        logger.info("Attempting to load model from MLflow registry: %s", model_uri)
        _model = mlflow.sklearn.load_model(model_uri)
        logger.info("Successfully loaded ML model from MLflow registry.")
        return True
    except Exception as exc:
        logger.warning("Could not load from MLflow registry: %s", exc)
        return False

def load_model_on_startup() -> None:
    """
    Load the fraud detection pipeline and threshold into memory.
    Called once in FastAPI startup event.
    """
    global _model, _threshold

    # 1. Try MLflow Model Registry first
    if not load_model_from_registry():
        # 2. Fallback to local .joblib file
        if not _PIPELINE_PATH.exists():
            logger.warning(
                "ML model not found at %s. "
                "Predictions will return a static stub. "
                "Run `python -m src.train_model` to generate it.",
                _PIPELINE_PATH,
            )
            return

        _model = joblib.load(_PIPELINE_PATH)
        logger.info("ML model loaded from %s", _PIPELINE_PATH)

    if _THRESHOLD_PATH.exists():
        import json
        with _THRESHOLD_PATH.open() as f:
            data = json.load(f)
        _threshold = float(data.get("threshold", 0.5))
        logger.info("Fraud threshold set to %.3f", _threshold)


@metrics.model_prediction_latency_seconds.time()
def predict(features: dict) -> dict:
    """
    Run the ML pipeline on a single transaction feature dict.
    Returns a dict with:
      - fraud_probability: float  (0.0 – 1.0)
      - fraud_flag:        bool
      - threshold_used:    float
    """
    if _model is None:
        # Stub fallback when no model is loaded
        score = round(
            features.get("device_risk_score", 0.5) * 0.4 +
            features.get("ip_risk_score", 0.5) * 0.4 +
            (1 if features.get("transaction_hour", 12) < 6 else 0) * 0.2,
            4,
        )
        return {"fraud_probability": score, "fraud_flag": score >= _threshold, "threshold_used": _threshold}

    # The pipeline expects a DataFrame with the same columns as training
    row = pd.DataFrame([{
        "amount":             features.get("amount", 0),
        "hour":               features.get("hour", features.get("transaction_hour", 12)),
        "device_risk_score":  features.get("device_risk_score", 0),
        "ip_risk_score":      features.get("ip_risk_score", 0),
        "merchant_category":  features.get("merchant_category", "other"),
        "transaction_type":   features.get("transaction_type", "online"),
        "country":            features.get("country", "US"),
    }])

    prob = float(_model.predict_proba(row)[0, 1])
    return {
        "fraud_probability": round(prob, 4),
        "fraud_flag":        prob >= _threshold,
        "threshold_used":    _threshold,
    }


def get_feature_importance() -> list[dict]:
    """Return feature name + importance pairs from the trained model (if available)."""
    if _model is None:
        return []
    try:
        preproc = _model.named_steps["preprocess"]
        clf     = _model.named_steps["clf"]
        names   = preproc.get_feature_names_out()
        imps    = clf.feature_importances_
        return [
            {"feature": n, "importance": round(float(i), 6)}
            for n, i in sorted(zip(names, imps), key=lambda x: -x[1])
        ]
    except Exception as exc:
        logger.debug("Could not extract feature importances: %s", exc)
        return []
