import os
from pathlib import Path

root = Path(r"c:\D_volume\FYP\Projects\AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System")
schemas_file = root / "backend" / "schemas.py"
main_file = root / "backend" / "main.py"

# Update schemas.py
schemas_content = schemas_file.read_text("utf-8")
old_prediction_response = """class PredictionResponse(BaseModel):
    \"\"\"
    Response returned after POST /api/v1/transactions/predict.
    This is what the frontend (React dashboard) will receive and display.
    \"\"\"
    transaction_id:    str         # Unique ID for this transaction
    fraud_probability: float       # 0.0000 to 1.0000 (the raw ML output)
    fraud_flag:        bool        # True = flagged as fraud
    risk_level:        str         # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    status:            str         # "APPROVED" | "FLAGGED" | "VERIFICATION_SENT"
    reason_codes:      List[str]   # Human-readable list of risk reasons
    message:           str         # User-friendly summary of the decision
    threshold_used:    float       # The threshold that was applied"""

new_prediction_response = """class PredictionResponse(BaseModel):
    transaction_id: str
    prediction: str
    risk_score: float
    risk_level: str
    confidence: float
    fraud_indicators: List[str]
    recommended_action: str
    model_version: str
    timestamp: str"""

if old_prediction_response in schemas_content:
    schemas_content = schemas_content.replace(old_prediction_response, new_prediction_response)
schemas_file.write_text(schemas_content, "utf-8")

# Update main.py
main_content = main_file.read_text("utf-8")
# Risk levels threshold logic replacement
old_risk_level = """    if probability < 0.30:
        return "LOW"
    elif probability < 0.50:
        return "MEDIUM"
    elif probability < 0.75:
        return "HIGH"
    else:
        return "CRITICAL\"\"\""""
new_risk_level = """    if probability <= 0.3:
        return "LOW"
    elif probability <= 0.6:
        return "MEDIUM"
    elif probability <= 0.8:
        return "HIGH"
    else:
        return "CRITICAL\"\"\""""
if "    if probability < 0.30:\n        return \"LOW\"" in main_content:
    main_content = main_content.replace(old_risk_level, new_risk_level) # Approximation if exact match fails, manual below

main_content = main_content.replace(
    'return "LOW"\n    elif probability < 0.50:\n        return "MEDIUM"\n    elif probability < 0.75:\n        return "HIGH"',
    'return "LOW"\n    elif probability <= 0.60:\n        return "MEDIUM"\n    elif probability <= 0.80:\n        return "HIGH"'
)
main_content = main_content.replace('    if probability < 0.30:', '    if probability <= 0.30:')

# The prediction return replacement
old_return = """    # ── Step 9: Return response ────────────────────────────────────────────
    return schemas.PredictionResponse(
        transaction_id    = transaction_id,
        fraud_probability = round(fraud_probability, 4),
        fraud_flag        = fraud_flag,
        risk_level        = risk_level,
        status            = status,
        reason_codes      = reason_codes,
        message           = message,
        threshold_used    = _threshold,
    )"""

new_return = """    # ── Step 9: Return response ────────────────────────────────────────────
    from datetime import datetime
    
    # Calculate confidence_score conceptually: the further from 0.5, the more confident
    confidence = abs(fraud_probability - 0.5) * 2

    return schemas.PredictionResponse(
        transaction_id = transaction_id,
        prediction = "FRAUD" if fraud_flag else "LEGITIMATE",
        risk_score = round(fraud_probability, 4),
        risk_level = risk_level,
        confidence = round(confidence, 4),
        fraud_indicators = reason_codes,
        recommended_action = "BLOCK" if status == "BLOCKED" else ("VERIFY" if status in ["VERIFICATION_SENT", "FLAGGED"] else "APPROVE"),
        model_version = "v1.0.0",
        timestamp = datetime.utcnow().isoformat() + "Z"
    )"""
if old_return in main_content:
    main_content = main_content.replace(old_return, new_return)

main_file.write_text(main_content, "utf-8")
print("ML Enhancements added.")
