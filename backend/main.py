# =============================================================================
# backend/main.py
# =============================================================================
# PURPOSE:
#   This is the HEART of Phase 4. It creates the FastAPI web server with all
#   API endpoints. This file ties together:
#     - The existing ML model (from Phase 1-2)
#     - The database (from database.py)
#     - The request/response schemas (from schemas.py)
#
# TO RUN THIS SERVER:
#   cd to your project root folder, then:
#   uvicorn backend.main:app --reload --port 8000
#
# AFTER STARTING:
#   - API docs (Swagger UI):  http://localhost:8000/docs
#   - API docs (ReDoc):       http://localhost:8000/redoc
#   - API root:               http://localhost:8000/
#
# API ENDPOINTS IN THIS FILE:
#   GET  /                                      → Welcome / system info
#   GET  /health                                → Health check
#   POST /api/v1/transactions/predict           → Submit transaction, get prediction
#   GET  /api/v1/transactions/                  → List all transactions
#   GET  /api/v1/transactions/{id}              → Get one transaction status
#   POST /api/v1/transactions/{id}/approve      → Approve a transaction (n8n webhook)
#   POST /api/v1/transactions/{id}/reject       → Reject/block a transaction (n8n webhook)
#   GET  /api/v1/stats                          → System-wide statistics
#   GET  /api/v1/audit-logs                     → Audit trail logs
#   GET  /api/v1/model/info                     → ML model information
# =============================================================================

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import requests


# ─── PATH SETUP ──────────────────────────────────────────────────────────────
# Add the project root to Python's path so we can import from "src/"
# This is necessary because backend/ is a subfolder of the project root.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─── INTERNAL IMPORTS ────────────────────────────────────────────────────────
from backend.database import Base, engine, get_db
from backend import models, schemas
from backend.services import auth_service

# ─── LOGGING SETUP ───────────────────────────────────────────────────────────
# Logging prints informative messages to the terminal as the server runs.
# INFO level shows general messages; WARNING shows potential problems; ERROR shows failures.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("fraud_engine")


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
# Base.metadata.create_all() looks at all classes in models.py that inherit
# from Base, and creates those tables in the database IF THEY DON'T EXIST.
# This is called "database migration" at its simplest form.
# Safe to run multiple times — it won't overwrite existing data.
Base.metadata.create_all(bind=engine)
logger.info(f"✅ Database tables initialized ({engine.name}: {engine.url.database})")


# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================
app = FastAPI(
    title="AI-Empowered Fintech Fraud Detection API",
    description="""
## Real-Time AI Fraud Detection and Control Automation System

**Final Year Project** | Minhaj University Lahore | Mohammad Usman (2026)

---

### What this API does:
1. **Accepts** transaction data (amount, location, device risk, etc.)
2. **Scores** it using a trained Machine Learning model
3. **Decides**: Approve automatically OR flag for email verification
4. **Integrates** with n8n automation for email-based approve/reject workflow

### Key Endpoints:
- `POST /api/v1/transactions/predict` → Submit a transaction for fraud analysis
- `GET /api/v1/transactions/` → View all transactions
- `POST /api/v1/transactions/{id}/approve` → Approve (called by n8n webhook)
- `POST /api/v1/transactions/{id}/reject`  → Block (called by n8n webhook)
- `GET /api/v1/stats` → Dashboard statistics
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Mohammad Usman",
        "url": "https://github.com/aliusman1122",
    },
)


# ─── CORS MIDDLEWARE ─────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing.
# This allows the React frontend (running on port 3000) to talk to this
# FastAPI server (running on port 8000) without the browser blocking it.
# In production, replace "*" with your actual frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],  # Allowed origins
    allow_credentials=True,
    allow_methods=["*"],          # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],          # Allow all headers
)


# =============================================================================
# ML MODEL LOADING
# =============================================================================
# These are module-level variables. They are set once when the server starts.
# "None" means not loaded yet.
_ml_model = None
_threshold = 0.35   # Default threshold (will be overridden from threshold.json)

# Paths to the model files (relative to project root)
MODEL_PATH      = os.path.join(PROJECT_ROOT, "models", "fraud_pipeline.joblib")
THRESHOLD_PATH  = os.path.join(PROJECT_ROOT, "models", "threshold.json")
# n8n Automation Workflow 1 URL (Manually Added)
N8N_WEBHOOK_URL = "http://localhost:5678/webhook-test/fintech-fraud-alert"

@app.on_event("startup")
async def load_model_on_startup():
    """
    This function runs ONCE when the FastAPI server starts up.
    It loads the trained ML model and threshold into memory.

    Why load at startup instead of per-request?
        - Loading a model takes 0.5-2 seconds
        - If we loaded per-request, every API call would be slow
        - Loaded once at startup → instant predictions on every request
    """
    global _ml_model, _threshold

    # Load the scikit-learn pipeline
    if os.path.exists(MODEL_PATH):
        _ml_model = joblib.load(MODEL_PATH)
        logger.info(f"✅ ML model loaded from: {MODEL_PATH}")
    else:
        logger.warning(
            f"⚠️  Model not found at {MODEL_PATH}. "
            "Run: python -m src.train_model"
        )

    # Load the saved threshold
    if os.path.exists(THRESHOLD_PATH):
        with open(THRESHOLD_PATH, "r") as f:
            threshold_data = json.load(f)
        # The threshold.json stores the optimal threshold from evaluate.py
        # It may be stored as {"threshold": 0.30} or just a number — handle both
        if isinstance(threshold_data, dict):
            _threshold = float(threshold_data.get("threshold", 0.35))
        else:
            _threshold = float(threshold_data)
        logger.info(f"✅ Threshold loaded: {_threshold}")
    else:
        logger.warning(
            f"⚠️  threshold.json not found. Using default: {_threshold}. "
            "Run: python -m src.evaluate"
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_risk_level(probability: float) -> str:
    """
    Converts a raw fraud probability into a human-readable risk level.

    These thresholds are business decisions:
        LOW      → Below 30% chance of fraud → Green
        MEDIUM   → 30-50% → Yellow (borderline)
        HIGH     → 50-75% → Orange
        CRITICAL → Above 75% → Red (almost certainly fraud)
    """
    if probability < 0.30:
        return "LOW"
    elif probability < 0.50:
        return "MEDIUM"
    elif probability < 0.75:
        return "HIGH"
    else:
        return "CRITICAL"


def generate_reason_codes(data: dict, probability: float) -> List[str]:
    """
    Generates human-readable explanations for WHY a transaction was flagged.

    These are rule-based reason codes (not ML-based). They are a quick summary
    of the most obvious risk factors. For deeper explanations, SHAP values
    from the original Streamlit dashboard are still available.

    In production systems, reason codes must be:
        - Short (under 10 words)
        - Non-technical (card holder might read them)
        - Actionable (analyst knows what to investigate)
    """
    reasons = []

    if data.get("device_risk_score", 0) >= 0.70:
        reasons.append("High-risk device fingerprint detected")

    if data.get("ip_risk_score", 0) >= 0.70:
        reasons.append("High-risk IP address or proxy detected")

    if data.get("amount", 0) >= 5000:
        reasons.append(f"Unusually large transaction: ${data['amount']:,.2f}")
    elif data.get("amount", 0) >= 2000:
        reasons.append("Transaction amount above typical threshold")

    hour = data.get("hour", 12)
    if hour in [0, 1, 2, 3, 4]:
        reasons.append(f"Transaction at high-risk hour: {hour}:00 AM")

    category = data.get("merchant_category", "").lower()
    high_risk_categories = ["gambling", "crypto", "wire_transfer", "foreign_exchange"]
    if category in high_risk_categories:
        reasons.append(f"High-risk merchant category: {category}")

    tx_type = data.get("transaction_type", "").lower()
    if tx_type in ["wire_transfer", "international"]:
        reasons.append(f"High-risk transaction type: {tx_type}")

    country = data.get("country", "").upper()
    if country not in ["US", "GB", "CA", "AU", "PK", "AE"]:
        reasons.append(f"Transaction originated from flagged region: {country}")

    if probability >= 0.75:
        reasons.append("Critical fraud probability score from AI model")
    elif probability >= 0.50:
        reasons.append("High fraud probability score from AI model")
    elif probability >= _threshold:
        reasons.append("Fraud probability exceeds configured threshold")

    # If no specific risk factor was found, give a generic message
    if not reasons:
        reasons.append("Low-risk transaction — all indicators within normal range")

    return reasons


def build_prediction_dataframe(transaction: schemas.TransactionInput) -> pd.DataFrame:
    """
    Converts the API input (TransactionInput schema) into a pandas DataFrame
    that the ML pipeline can process.

    CRITICAL: The column names here MUST match the columns in your training data.
    If your model was trained with different column names, you'll get an error.
    To verify, check: src/validation.py → REQUIRED_FEATURE_COLUMNS
    """
    input_dict = {
        "amount":             [transaction.amount],
        "hour":               [transaction.hour],
        "device_risk_score":  [transaction.device_risk_score],
        "ip_risk_score":      [transaction.ip_risk_score],
        "merchant_category":  [transaction.merchant_category],
        "transaction_type":   [transaction.transaction_type or "online"],
        "country":            [transaction.country or "US"],
    }
    return pd.DataFrame(input_dict)


# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post(
    "/api/v1/auth/register",
    tags=["Authentication"],
    summary="Register a new user",
)
async def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    # Check if email is already registered
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password and save
    hashed_password = auth_service.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "phone": new_user.phone
    }

@app.post(
    "/api/v1/auth/login",
    response_model=schemas.TokenResponse,
    tags=["Authentication"],
    summary="Login and get JWT token",
)
async def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not auth_service.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate JWT token
    access_token = auth_service.create_access_token(data={"sub": user.email, "user_id": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }


# =============================================================================
# ROOT & HEALTH ENDPOINTS
# =============================================================================

@app.get("/", tags=["System"])
async def root():
    """
    Welcome endpoint. Returns system info and a map of all endpoints.
    Open http://localhost:8000/ in your browser to see this.
    """
    return {
        "system":       "AI-Empowered Fintech Fraud Detection Engine",
        "version":      "1.0.0",
        "author":       "Mohammad Usman | Minhaj University Lahore",
        "status":       "operational",
        "model_loaded": _ml_model is not None,
        "threshold":    _threshold,
        "endpoints": {
            "predict":       "POST /api/v1/transactions/predict",
            "list":          "GET  /api/v1/transactions/",
            "get_status":    "GET  /api/v1/transactions/{id}",
            "approve":       "POST /api/v1/transactions/{id}/approve",
            "reject":        "POST /api/v1/transactions/{id}/reject",
            "stats":         "GET  /api/v1/stats",
            "audit_logs":    "GET  /api/v1/audit-logs",
            "model_info":    "GET  /api/v1/model/info",
            "swagger_docs":  "GET  /docs",
            "redoc":         "GET  /redoc",
        },
    }


@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint. Returns 200 if everything is working.
    Use this to confirm the server is up before running tests.
    """
    try:
        # Quick database check
        db.execute(models.Transaction.__table__.select().limit(1))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status":           "healthy",
        "model_loaded":     _ml_model is not None,
        "database":         db_status,
        "threshold":        _threshold,
        "timestamp":        datetime.utcnow().isoformat() + "Z",
    }


# =============================================================================
# CORE PREDICTION ENDPOINT
# =============================================================================

@app.post(
    "/api/v1/transactions/predict",
    response_model=schemas.PredictionResponse,
    tags=["Transactions"],
    summary="Submit a transaction for fraud analysis",
)
async def predict_transaction(
    transaction: schemas.TransactionInput,
    db: Session = Depends(get_db),
):
    """
    ## The main endpoint of the entire system.

    **What happens when you call this:**
    1. Receive transaction data (JSON body)
    2. Validate all fields (Pydantic does this automatically)
    3. Build a DataFrame and pass it to the ML model
    4. Get fraud probability (0.0 - 1.0)
    5. Compare against threshold (default: 0.35)
    6. Save transaction + prediction to database
    7. Write audit log entry
    8. Return decision

    **Decision logic:**
    - probability < threshold → `APPROVED` (auto-cleared)
    - probability >= threshold + no email → `FLAGGED`
    - probability >= threshold + email provided → `VERIFICATION_SENT` (Phase 5: sends email via n8n)
    """
    allowed_categories = [cat.value for cat in schemas.MerchantCategory]
    if str(transaction.merchant_category).lower().strip() not in allowed_categories:
        transaction.merchant_category = schemas.MerchantCategory.other
        
    # ── Step 1: Check model is loaded ──────────────────────────────────────
    if _ml_model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "ML model is not loaded. "
                "Please train the model first by running: "
                "python -m src.train_model"
            )
        )

    # ── Step 2: Build DataFrame for prediction ─────────────────────────────
    try:
        df = build_prediction_dataframe(transaction)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to prepare input data: {str(e)}"
        )

    # ── Step 3: Run ML model prediction ────────────────────────────────────
    try:
        # predict_proba returns [[prob_class_0, prob_class_1]]
        # prob_class_1 is the probability of FRAUD
        fraud_probability = float(_ml_model.predict_proba(df)[0][1])
    except Exception as e:
        logger.error(f"Model prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=(
                f"Prediction failed: {str(e)}. "
                "This usually means the input column names don't match the training data. "
                "Check src/validation.py → REQUIRED_FEATURE_COLUMNS for the exact column names."
            )
        )

    # ── Step 4: Calculate derived fields ───────────────────────────────────
    fraud_flag   = fraud_probability >= _threshold
    risk_level   = get_risk_level(fraud_probability)
    reason_codes = generate_reason_codes(transaction.dict(), fraud_probability)

    # ── Step 5: Generate unique transaction ID ─────────────────────────────
    transaction_id = str(uuid.uuid4())

    # ── Step 6: Determine transaction status ───────────────────────────────
    if not fraud_flag:
        status  = "APPROVED"
        message = (
            f"✅ APPROVED — Transaction cleared. "
            f"Fraud probability: {fraud_probability:.1%} (below threshold of {_threshold:.0%}). "
            f"Bank release authorized."
        )
    elif transaction.user_email:
        status  = "VERIFICATION_SENT"
        message = (
            f"⚠️ SUSPICIOUS — Verification email queued for {transaction.user_email}. "
            f"Fraud probability: {fraud_probability:.1%}. "
            f"Transaction held pending user confirmation."
        )
        # 🔥 LIVE N8N AUTOMATION TRIGGER (The Data hits the n8n workf)
        try:
            payload = {
                "transaction_id": transaction_id,
                "amount": transaction.amount,
                "merchant_category": transaction.merchant_category,
                "fraud_probability": round(fraud_probability, 4),
                "user_email": transaction.user_email
            }
            # send the alert to n8n 
            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
            logger.info(f"🚀 n8n Automation Webhook Triggered for {transaction.user_email}")
        except Exception as e:
            logger.error(f"❌ Failed to trigger n8n webhook: {str(e)}")

    else:
        status  = "FLAGGED"
        message = (
            f"🚨 FLAGGED — Transaction held for review. "
            f"Fraud probability: {fraud_probability:.1%}. "
            f"Provide user_email to trigger automated verification."
        )

    # ── Step 7: Save to database ───────────────────────────────────────────
    try:
        db_transaction = models.Transaction(
            transaction_id    = transaction_id,
            user_id           = None,
            amount            = transaction.amount,
              transaction_hour              = transaction.hour,
            device_risk_score = transaction.device_risk_score,
            ip_risk_score     = transaction.ip_risk_score,
            merchant_category = transaction.merchant_category,
            transaction_type  = transaction.transaction_type,
            country           = transaction.country,
            fraud_probability = round(fraud_probability, 6),
            fraud_flag        = fraud_flag,
            risk_level        = risk_level,
            risk_score        = round(fraud_probability * 100, 2),
            reason_codes      = json.dumps(reason_codes),
            status            = status,
            user_email        = transaction.user_email,
            verification_token= str(uuid.uuid4()) if fraud_flag else None,
        )
        db.add(db_transaction)
        db.flush()

        # ── Step 8: Write audit log ────────────────────────────────────────
        action = "AUTO_APPROVED" if not fraud_flag else (
            "EMAIL_QUEUED" if transaction.user_email else "FLAGGED"
        )
        log_entry = models.AuditLog(
            transaction_id = db_transaction.id,
            action         = action,
            description    = (
                f"Fraud probability: {fraud_probability:.4f} | "
                f"Risk: {risk_level} | "
                f"Threshold: {_threshold}"
            ),
            performed_by   = "ai_model",
        )
        db.add(log_entry)
        db.commit()

        logger.info(
            f"Transaction {transaction_id[:8]}... | "
            f"prob={fraud_probability:.3f} | "
            f"status={status}"
        )

    except KeyError as ke:
        db.rollback()
        logger.error(f"❌ Payload structural key mismatch: {str(ke)}")
        raise HTTPException(
            status_code=422, 
            detail=f"Data payload structure mismatch: Missing field {str(ke)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Database operational failure: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database persistent storage pipeline failure error: {str(e)}"
        )


    # ── Step 9: Return response ────────────────────────────────────────────
    return schemas.PredictionResponse(
        transaction_id    = transaction_id,
        fraud_probability = round(fraud_probability, 4),
        fraud_flag        = fraud_flag,
        risk_level        = risk_level,
        status            = status,
        reason_codes      = reason_codes,
        message           = message,
        threshold_used    = _threshold,
    )


# =============================================================================
# TRANSACTION LISTING
# =============================================================================

@app.get(
    "/api/v1/transactions/",
    response_model=List[schemas.TransactionListItem],
    tags=["Transactions"],
    summary="List all transactions",
)
async def list_transactions(
    limit:  int           = Query(default=50, le=500, description="Max records to return"),
    status: Optional[str] = Query(default=None, description="Filter by status: APPROVED, FLAGGED, BLOCKED, VERIFICATION_SENT"),
    db:     Session       = Depends(get_db),
):
    """
    Returns a list of transactions, newest first.
    Use the ?status= query parameter to filter.

    Examples:
    - GET /api/v1/transactions/                     → all transactions
    - GET /api/v1/transactions/?status=BLOCKED       → only blocked ones
    - GET /api/v1/transactions/?status=FLAGGED&limit=10 → 10 flagged
    """
    query = db.query(models.Transaction)

    if status:
        query = query.filter(models.Transaction.status == status.upper())

    transactions = (
        query
        .order_by(models.Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        schemas.TransactionListItem(
            transaction_id    = tx.transaction_id,
            amount            = tx.amount,
            status            = tx.status,
            fraud_probability = tx.fraud_probability,
            risk_level        = tx.risk_level,
            merchant_category = tx.merchant_category,
            created_at        = tx.created_at,
        )
        for tx in transactions
    ]


# =============================================================================
# SINGLE TRANSACTION STATUS
# =============================================================================

@app.get(
    "/api/v1/transactions/{transaction_id}",
    response_model=schemas.TransactionStatusResponse,
    tags=["Transactions"],
    summary="Get status of a specific transaction",
)
async def get_transaction_status(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """
    Returns the full status of one transaction.
    The React frontend can poll this endpoint every few seconds to check
    if a user has responded to the verification email.
    """
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )

    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction '{transaction_id}' not found."
        )

    status_messages = {
        "APPROVED":          "✅ Transaction approved. Bank ledger release authorized.",
        "FLAGGED":           "🚨 Transaction flagged for review. Awaiting analyst decision.",
        "VERIFICATION_SENT": "📧 Verification email sent. Awaiting user response.",
        "BLOCKED":           "🚫 Transaction blocked. Fraud confirmed by account holder.",
        "PENDING":           "⏳ Transaction received. Processing...",
    }

    return schemas.TransactionStatusResponse(
        transaction_id    = tx.transaction_id,
        status            = tx.status,
        fraud_probability = tx.fraud_probability,
        fraud_flag        = tx.fraud_flag,
        risk_level        = tx.risk_level,
        amount            = tx.amount,
        created_at        = tx.created_at,
        updated_at        = tx.updated_at,
        message           = status_messages.get(tx.status, "Unknown status"),
    )


# =============================================================================
# APPROVE ENDPOINT (called by n8n webhook after user clicks "Approve" in email)
# =============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/approve",
    tags=["Workflow"],
    summary="Approve a flagged transaction (called by n8n webhook)",
)
async def approve_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """
    Approves a flagged transaction.

    **When is this called?**
    - Phase 5: n8n sends an email to the user with an "Approve" button
    - When user clicks the button, n8n calls this endpoint as a webhook

    **What happens:**
    1. Find the transaction in the database
    2. Change status from FLAGGED/VERIFICATION_SENT → APPROVED
    3. Write audit log entry
    4. Return confirmation

    **Guard rails:**
    - Already BLOCKED → error (can't approve after blocking)
    - Already APPROVED → returns success (idempotent, safe to call twice)
    """
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.status == "BLOCKED":
        raise HTTPException(
            status_code=409,
            detail="Transaction is already BLOCKED. Cannot approve a blocked transaction."
        )

    if tx.status == "APPROVED":
        return {
            "transaction_id": transaction_id,
            "status":         "APPROVED",
            "message":        "Transaction was already approved.",
            "timestamp":      datetime.utcnow().isoformat() + "Z",
        }

    # Update status
    tx.status     = "APPROVED"
    tx.updated_at = datetime.utcnow()

    # Audit log
    log_entry = models.AuditLog(
        transaction_id = tx.id,
        action         = "USER_APPROVED",
        description    = "Account holder confirmed: this transaction was made by them.",
        performed_by   = "user",
    )
    db.add(log_entry)
    db.commit()

    logger.info(f"Transaction {transaction_id[:8]}... APPROVED by user")

    return {
        "transaction_id": transaction_id,
        "status":         "APPROVED",
        "message":        "✅ Transaction APPROVED. Bank ledger release authorized. Funds transferred.",
        "timestamp":      datetime.utcnow().isoformat() + "Z",
    }


# =============================================================================
# REJECT ENDPOINT (called by n8n webhook after user clicks "Reject" in email)
# =============================================================================

@app.post(
    "/api/v1/transactions/{transaction_id}/reject",
    tags=["Workflow"],
    summary="Reject and block a transaction (called by n8n webhook)",
)
async def reject_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
):
    """
    Blocks a flagged transaction — the user said "this was NOT me."

    **What happens:**
    1. Find the transaction in the database
    2. Change status → BLOCKED
    3. Write audit log entry
    4. Return confirmation

    **In a real system, this would also:**
    - Freeze the bank card
    - Alert the fraud team
    - Generate a security incident ticket
    - Trigger card replacement workflow
    """
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.transaction_id == transaction_id)
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if tx.status == "APPROVED":
        raise HTTPException(
            status_code=409,
            detail="Transaction is already APPROVED. Cannot block an approved transaction."
        )

    if tx.status == "BLOCKED":
        return {
            "transaction_id": transaction_id,
            "status":         "BLOCKED",
            "message":        "Transaction was already blocked.",
            "timestamp":      datetime.utcnow().isoformat() + "Z",
        }

    # Update status
    tx.status     = "BLOCKED"
    tx.updated_at = datetime.utcnow()

    # Audit log
    log_entry = models.AuditLog(
        transaction_id = tx.id,
        action         = "USER_REJECTED",
        description    = "Account holder confirmed: FRAUD. Transaction rejected and card flagged.",
        performed_by   = "user",
    )
    db.add(log_entry)
    db.commit()

    logger.info(f"Transaction {transaction_id[:8]}... BLOCKED by user (fraud confirmed)")

    return {
        "transaction_id": transaction_id,
        "status":         "BLOCKED",
        "message":        "🚫 Transaction BLOCKED. Fraud confirmed by account holder. Security logs generated. Card flagged.",
        "timestamp":      datetime.utcnow().isoformat() + "Z",
    }


# =============================================================================
# STATISTICS ENDPOINT
# =============================================================================

@app.get(
    "/api/v1/stats",
    response_model=schemas.StatsResponse,
    tags=["Analytics"],
    summary="Get system-wide fraud statistics",
)
async def get_stats(db: Session = Depends(get_db)):
    """
    Returns aggregate statistics for the dashboard summary cards.
    The React frontend will call this to populate the metrics at the top.
    """
    total     = db.query(models.Transaction).count()
    approved  = db.query(models.Transaction).filter(models.Transaction.status == "APPROVED").count()
    blocked   = db.query(models.Transaction).filter(models.Transaction.status == "BLOCKED").count()
    reviewing = db.query(models.Transaction).filter(
        models.Transaction.status.in_(["FLAGGED", "VERIFICATION_SENT"])
    ).count()

    # Calculate average fraud probability across flagged transactions
    flagged_txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.fraud_flag == True)
        .all()
    )
    avg_prob = (
        float(np.mean([t.fraud_probability for t in flagged_txns if t.fraud_probability]))
        if flagged_txns else 0.0
    )

    fraud_rate = round((len(flagged_txns) / total * 100), 2) if total > 0 else 0.0

    return schemas.StatsResponse(
        total_transactions    = total,
        approved_count        = approved,
        blocked_count         = blocked,
        under_review_count    = reviewing,
        fraud_rate_percent    = fraud_rate,
        avg_fraud_probability = round(avg_prob, 4),
        model_threshold       = _threshold,
        timestamp             = datetime.utcnow().isoformat() + "Z",
    )


# =============================================================================
# AUDIT LOGS ENDPOINT
# =============================================================================

@app.get(
    "/api/v1/audit-logs",
    response_model=List[schemas.AuditLogItem],
    tags=["Analytics"],
    summary="Retrieve audit trail logs",
)
async def get_audit_logs(
    transaction_id: Optional[str] = Query(default=None, description="Filter logs by transaction ID"),
    limit:          int            = Query(default=100, le=1000),
    db:             Session        = Depends(get_db),
):
    """
    Returns the full audit trail. Every action ever taken is recorded here.
    Filter by transaction_id to see all actions on one specific transaction.

    Example: GET /api/v1/audit-logs?transaction_id=f47ac10b-...
    """
    query = db.query(models.AuditLog)

    if transaction_id:
        tx = db.query(models.Transaction).filter(models.Transaction.transaction_id == transaction_id).first()
        if not tx:
            return []
        query = query.filter(models.AuditLog.transaction_id == tx.id)

    logs = (
        query
        .order_by(models.AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        schemas.AuditLogItem(
            id             = log.id,
            transaction_id = db.query(models.Transaction).filter(models.Transaction.id == log.transaction_id).first().transaction_id,
            action         = log.action,
            details        = log.description,
            performed_by   = log.performed_by,
            timestamp      = log.created_at.isoformat() if log.created_at else None,
        )
        for log in logs
    ]


# =============================================================================
# MODEL INFO ENDPOINT
# =============================================================================

@app.get(
    "/api/v1/model/info",
    tags=["System"],
    summary="Get information about the loaded ML model",
)
async def get_model_info():
    """
    Returns information about the currently loaded ML model.
    Useful for debugging and for your FYP presentation.
    """
    if _ml_model is None:
        raise HTTPException(
            status_code=503,
            detail="ML model is not loaded. Run: python -m src.train_model"
        )

    # Try to get model type from the pipeline steps
    model_type = "Unknown"
    try:
        clf = _ml_model.named_steps.get("clf", None)
        if clf:
            model_type = type(clf).__name__
    except Exception:
        pass

    # Try to get feature names
    feature_names = []
    try:
        preprocessor = _ml_model.named_steps.get("preprocess", None)
        if preprocessor:
            feature_names = list(preprocessor.get_feature_names_out())
    except Exception:
        feature_names = ["Unable to retrieve feature names"]

    return {
        "model_type":    model_type,
        "pipeline_steps": list(_ml_model.named_steps.keys()) if _ml_model else [],
        "threshold":     _threshold,
        "n_features":    len(feature_names),
        "feature_names": feature_names[:20],  # First 20 (after one-hot encoding there are many)
        "model_path":    MODEL_PATH,
        "loaded":        True,
    }
