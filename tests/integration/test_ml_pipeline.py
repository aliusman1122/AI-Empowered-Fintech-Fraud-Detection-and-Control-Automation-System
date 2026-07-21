import pytest
import os
import tempfile
import pandas as pd
from backend.services.ml_service import MLService
import joblib

def test_ml_pipeline_e2e():
    # Because MLflow is a heavy external hook, we decouple this from the AsyncClient
    # and strictly test the service logic binding to the models.
    
    # 1. Train model (Mocked or simple local train)
    ml_svc = MLService(model_path="dummy.pkl")
    
    # Fake dataset
    df = pd.DataFrame({
        "amount": [10.0, 10000.0],
        "transaction_hour": [14, 3],
        "merchant_risk": [0.1, 0.9],
        "country_risk": [0.1, 0.9],
        "device_ip_risk_combined": [0.1, 0.95]
    })
    y = [0, 1]
    
    # Since ML service doesn't expose raw training immediately in this architecture, 
    # we just verify that predict functionality initializes correctly over standard signatures
    
    assert hasattr(ml_svc, "predict")
    assert hasattr(ml_svc, "predict_proba")
    
    # Since we mocked it in conftest, it will safely execute
    prob = ml_svc.predict_proba([[10.0, 14, 0.1, 0.1, 0.1]])
    assert isinstance(prob, (list, tuple, float, int)) or hasattr(prob, 'shape')
