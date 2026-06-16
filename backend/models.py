# =============================================================================
# backend/models.py
# =============================================================================
# PURPOSE:
#   This file defines what our DATABASE TABLES look like.
#   Each Python class here = one table in the database.
#   Each class attribute = one column in that table.
#
# TABLES IN THIS FILE:
#   1. Transaction  → Stores every submitted transaction and its fraud result
#   2. FraudLog     → Audit trail - records every action taken on transactions
#
# HOW SQLALCHEMY MODELS WORK:
#   Instead of writing SQL like:
#     CREATE TABLE transactions (id TEXT PRIMARY KEY, amount REAL, ...)
#   We write Python classes and SQLAlchemy creates the SQL for us.
# =============================================================================

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from backend.database import Base


# =============================================================================
# TABLE 1: Transaction
# =============================================================================
class Transaction(Base):
    """
    Stores every transaction that was submitted to the fraud detection API.

    STATUS FLOW (state machine):
        PENDING
            ↓ (model scores it)
        APPROVED          ← low fraud probability (below threshold)
            or
        FLAGGED           ← high fraud probability, no email provided
            or
        VERIFICATION_SENT ← high fraud probability, email sent to user
            ↓ (user responds to email)
        APPROVED          ← user confirmed "yes, this was me"
            or
        BLOCKED           ← user said "no, this was not me" (fraud confirmed)
    """

    __tablename__ = "transactions"

    # ─── PRIMARY KEY ─────────────────────────────────────────────────────────
    # UUID is a long random string like "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    # This is better than auto-incrementing integers because:
    #   - It's unique across ALL systems (useful when scaling)
    #   - It doesn't expose how many transactions you have
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    # ─── TRANSACTION INPUT FEATURES ──────────────────────────────────────────
    # These are the values the user submitted for fraud analysis.
    # They must EXACTLY match the features the ML model was trained on.
    amount              = Column(Float,   nullable=False)   # Transaction amount in USD
    hour                = Column(Integer, nullable=False)   # Hour of day (0-23)
    device_risk_score   = Column(Float,   nullable=False)   # Device fingerprint risk (0.0-1.0)
    ip_risk_score       = Column(Float,   nullable=False)   # IP address risk score (0.0-1.0)
    merchant_category   = Column(String,  nullable=False)   # e.g. "electronics", "food"
    transaction_type    = Column(String,  nullable=True)    # e.g. "online", "pos", "wire"
    country             = Column(String,  nullable=True)    # e.g. "US", "GB", "PK"

    # ─── ML MODEL OUTPUT ─────────────────────────────────────────────────────
    # These are calculated by the ML model after submission.
    fraud_probability   = Column(Float,   nullable=True)    # 0.0 to 1.0
    fraud_flag          = Column(Boolean, nullable=True)    # True if probability >= threshold
    risk_level          = Column(String,  nullable=True)    # LOW / MEDIUM / HIGH / CRITICAL
    risk_score          = Column(Float,   nullable=True)    # fraud_probability * 100 (0-100)
    reason_codes        = Column(Text,    nullable=True)    # JSON array of reason strings

    # ─── WORKFLOW STATE ───────────────────────────────────────────────────────
    # Tracks where this transaction is in the approval/rejection process.
    status = Column(String, default="PENDING")
    # Possible values:
    #   "PENDING"           → just received, not yet processed
    #   "APPROVED"          → cleared (low risk or user confirmed)
    #   "FLAGGED"           → high risk, no email provided
    #   "VERIFICATION_SENT" → email sent to user awaiting decision
    #   "BLOCKED"           → user rejected / fraud confirmed

    # ─── EMAIL VERIFICATION ───────────────────────────────────────────────────
    # Used in Phase 5 (n8n email workflow)
    user_email          = Column(String,  nullable=True)    # Where to send verification email
    verification_token  = Column(String,  nullable=True, unique=True)
    # verification_token is a secret UUID sent in the email URL so only the
    # account owner can approve/reject their own transaction.

    # ─── TIMESTAMPS ───────────────────────────────────────────────────────────
    # server_default=func.now() → database sets this automatically when inserted
    # onupdate=func.now()       → database updates this automatically on every update
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<Transaction id={self.id[:8]}... "
            f"amount={self.amount} "
            f"status={self.status} "
            f"prob={self.fraud_probability}>"
        )


# =============================================================================
# TABLE 2: FraudLog (Audit Trail)
# =============================================================================
class FraudLog(Base):
    """
    Immutable audit log of every action taken on every transaction.

    Why do we need this?
        - Compliance: regulators require a full audit trail
        - Debugging: if something goes wrong, we can trace every step
        - Security: proves who did what and when
        - Portfolio: shows interviewers you understand enterprise-grade design

    This table is APPEND-ONLY. We never update or delete rows here.
    Every action creates a NEW row.
    """

    __tablename__ = "fraud_logs"

    # ─── PRIMARY KEY ─────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ─── FOREIGN KEY REFERENCE ───────────────────────────────────────────────
    # Links this log entry to a specific transaction.
    # (We keep this as a simple String to avoid SQLite FK complexity)
    transaction_id = Column(String(36), nullable=False, index=True)

    # ─── ACTION DESCRIPTION ──────────────────────────────────────────────────
    # What happened to this transaction?
    action = Column(String, nullable=False)
    # Possible values:
    #   "CREATED"           → Transaction was submitted
    #   "AI_SCORED"         → ML model ran and assigned probability
    #   "AUTO_APPROVED"     → Low risk, automatically approved
    #   "FLAGGED"           → High risk, flagged for review
    #   "EMAIL_SENT"        → Verification email dispatched via n8n
    #   "USER_APPROVED"     → User clicked Approve in email
    #   "USER_REJECTED"     → User clicked Reject in email
    #   "ANALYST_APPROVED"  → Human analyst approved
    #   "ANALYST_BLOCKED"   → Human analyst blocked

    # ─── DETAILS & METADATA ──────────────────────────────────────────────────
    details      = Column(Text,   nullable=True)  # Human-readable explanation
    performed_by = Column(String, default="system")
    # performed_by options: "ai_model", "user", "analyst", "system", "n8n"

    timestamp = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return (
            f"<FraudLog id={self.id} "
            f"tx={self.transaction_id[:8]}... "
            f"action={self.action}>"
        )
