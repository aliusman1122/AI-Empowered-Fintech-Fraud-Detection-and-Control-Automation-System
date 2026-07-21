"""
╔══════════════════════════════════════════════════════════════╗
║           DATABASE MODELS — 5 TABLES                         ║
║                                                              ║
║   Every Python class represent the  database table.          ║
║   Use SQLAlchemy ORM:                                        ║
║     → Python                                                 ║
║     → SQLAlchemy translate in SQL                            ║
║                                                              ║
║   TABLE 1  →  users               (users of system )         ║
║   TABLE 2  →  transactions        (every financial txn)      ║
║   TABLE 3  →  fraud_alerts        (suspicious detections)    ║
║   TABLE 4  →  verification_tokens (tokens of email links )   ║
║   TABLE 5  →  audit_logs          (permanent action record)  ║
╚══════════════════════════════════════════════════════════════╝
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import enum

from .database import Base


# ══════════════════════════════════════════════════════════════
# ENUM TYPES — Fixed choices define karna
# ══════════════════════════════════════════════════════════════
#
# Enum matlab: Only specific values are allowed for a column.
# Resist to enter the wrong values in Database
#

class UserRole(str, enum.Enum):
    """
    User Role Enum — RBAC (Role-Based Access Control) ke liye.

    admin   → Full system access (view all, manage users)
    analyst → Can view transactions and run queries
    user    → Can only submit transactions and view own records
    """
    admin   = "admin"
    analyst = "analyst"
    user    = "user"


class TransactionStatus(str, enum.Enum):
    """
    Possible States of transaction — State Machine.

    Flow diagram:
      New transaction 
            │
            ▼
      Check by ML model 
            │
      ┌─────┴──────────────────────────┐
      │                                │
      ▼ (score < threshold)            ▼ (score >= threshold)
    AUTO_APPROVED                    PENDING
                                       │
                           Send the email to user
                                       │
                              ┌────────┴────────┐
                              │                 │
                              ▼ (approve)       ▼ (reject)
                           APPROVED          REJECTED / BLOCKED
    """
    PENDING       = "pending"        # ML flagged, user se confirm karna hai
    AUTO_APPROVED = "auto_approved"  # ML score kam tha, khud approve ho gayi
    APPROVED      = "approved"       # User ne email se approve kiya
    REJECTED      = "rejected"       # User ne email se reject kiya
    BLOCKED       = "blocked"        # System ne permanently block kiya


class AlertLevel(str, enum.Enum):
    """
    Severity Level of fraud alert ki .
    Level decide according to fraud probability.
    """
    LOW      = "low"       # 0.35 – 0.50  →  Careful
    MEDIUM   = "medium"    # 0.50 – 0.70  →  Suspicious
    HIGH     = "high"      # 0.70 – 0.90  →  Likely Fraud
    CRITICAL = "critical"  # 0.90+         →  Almost Certain Fraud


# ══════════════════════════════════════════════════════════════
# TABLE 1: users
# ══════════════════════════════════════════════════════════════

class User(Base):
    """
    Users Table — System registered users.

    Columns:
      id         → Auto-increment primary key (1, 2, 3 ...)
      email      → Unique email address (verification email comes here)
      full_name  → Full_Name of user
      phone      → Optional phone number
      is_active  → Account active or not (default: True)
      created_at → Account creation time (automatic)
      updated_at → Last update time (automatic)

    Relationships:
      ↳ a user should have many transactions (One-to-Many)
    """
    __tablename__ = "users"

    id              = Column(Integer,     primary_key=True, index=True, autoincrement=True)
    email           = Column(String(255), unique=True,      nullable=False, index=True)
    full_name       = Column(String(255), nullable=False)
    phone           = Column(String(20),  nullable=True)
    # ⚠️  SECURITY: No default value — password MUST be hashed before saving.
    # Use auth_service.get_password_hash(password) before creating a User.
    hashed_password = Column(String(255), nullable=False)
    # RBAC: role determines what endpoints the user can access
    role            = Column(String(20),  nullable=False, default=UserRole.user.value, index=True)
    is_active       = Column(Boolean,     default=True,   nullable=False)
    is_verified     = Column(Boolean,     default=False,  nullable=False)  # Email verified?
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions   = relationship("Transaction",  back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User  id={self.id}  email={self.email}>"


# ══════════════════════════════════════════════════════════════
# TABLE 2: transactions
# ══════════════════════════════════════════════════════════════

class Transaction(Base):
    """
    Transactions Table — Core of system /main table.
    Every financial transaction record here.

    Columns Group 1 — Identity:
      id             → Auto-increment internal ID
      transaction_id → Human-readable unique ID (e.g., "TXN-A1B2C3D4")
      user_id        → Which user's transaction(Foreign Key → users.id)

    Columns Group 2 — Transaction Details (ML ka input):
      amount             → Amount (e.g., 85000.00)
      merchant_category  → Merchant category (e.g., "grocery", "international_wire")
      transaction_hour   → Transaction hour (0-23)
      device_risk_score  → Device risk score (0.0 = safe, 1.0 = very risky)
      ip_risk_score      → IP address risk score (0.0 = safe, 1.0 = very risky)

    Columns Group 3 — ML Output:
      fraud_probability  → ML score (e.g., 0.89 = 89% fraud probability)
      fraud_flag         → True or False (decide after the threshold)
      reason_codes       → Reasons in JSON string (e.g., '["High IP risk"]')

    Columns Group 4 — Status:
      status → Current state (pending/auto_approved/approved/rejected/blocked)

    Relationships:
      ↳ fraud_alerts        (there should be multiple alerts of single transaction)
      ↳ verification_tokens (tokens of email links)
      ↳ audit_logs          (record of status changes)
    """
    __tablename__ = "transactions"
    __table_args__ = (
        Index('ix_transactions_user_id', 'user_id'),
    )

    # ── Identity ──────────────────────────────────────────────
    id             = Column(Integer,   primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id        = Column(Integer,   ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # ── Transaction Input Fields ───────────────────────────────
    amount             = Column(Float,        nullable=False)
    merchant_category  = Column(String(100),  nullable=False)
    transaction_hour   = Column(Integer,      nullable=False)   # 0–23
    device_risk_score  = Column(Float,        nullable=False)   # 0.0–1.0
    ip_risk_score      = Column(Float,        nullable=False)   # 0.0–1.0

    # ── ML Model Output Fields ─────────────────────────────────
    fraud_probability  = Column(Float,   nullable=True)   # ML score (0.0–1.0)
    fraud_flag         = Column(Boolean, nullable=True)   # Threshold ke baad set hota hai
    reason_codes       = Column(JSONB,   nullable=True)   # JSON array natively via PostgreSQL
    risk_level         = Column(String(20),   nullable=True)
    risk_score         = Column(Float,        nullable=True)
    transaction_type   = Column(String(50),   nullable=True)
    country            = Column(String(50),   nullable=True)
    user_email         = Column(String(255),  nullable=True)
    verification_token = Column(String(100),  nullable=True)

    # ── Status (State Machine) ─────────────────────────────────
    status = Column(
        String(20),
        default=TransactionStatus.PENDING.value,
        nullable=False,
        index=True
    )

    # ── Timestamps ─────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── Relationships ──────────────────────────────────────────
    user                = relationship("User",              back_populates="transactions")
    fraud_alerts        = relationship("FraudAlert",        back_populates="transaction")
    verification_tokens = relationship("VerificationToken", back_populates="transaction")
    audit_logs          = relationship("AuditLog",          back_populates="transaction")

    def __repr__(self):
        return (
            f"<Transaction  id={self.id}  "
            f"txn_id={self.transaction_id}  "
            f"amount={self.amount}  "
            f"status={self.status}>"
        )


# ══════════════════════════════════════════════════════════════
# TABLE 3: fraud_alerts
# ══════════════════════════════════════════════════════════════

class FraudAlert(Base):
    """
    Fraud Alerts Table — Alert record for suspicious transactions.

    When it is created:
      ML model detects fraud_flag=True → Fraud Alert is created
      → n8n webhook triggers → Email is sent to the user

    Tracking:
      - n8n_webhook_sent    → Was the signal sent to n8n?
      - n8n_webhook_sent_at → When was it sent?
      - n8n_response_status → What did n8n reply? ("success"/"failed")
      - email_sent          → Was the email sent to the user?
      - email_sent_at       → When was it sent?
      - email_recipient     → Who was it sent to?
    """
    __tablename__ = "fraud_alerts"
    __table_args__ = (
        Index('ix_fraud_alerts_transaction_id', 'transaction_id'),
    )

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)

    # Alert ki severity
    alert_level  = Column(String(20), default=AlertLevel.LOW.value, nullable=False)
    reason_codes = Column(JSONB,      nullable=True)    # JSON array natively via PostgreSQL

    # n8n automation tracking
    n8n_webhook_sent    = Column(Boolean,                  default=False)
    n8n_webhook_sent_at = Column(DateTime(timezone=True),  nullable=True)
    n8n_response_status = Column(String(50),               nullable=True)

    # Email tracking
    email_sent      = Column(Boolean,                 default=False)
    email_sent_at   = Column(DateTime(timezone=True), nullable=True)
    email_recipient = Column(String(255),             nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship: FraudAlert → Transaction (Many-to-One)
    transaction = relationship("Transaction", back_populates="fraud_alerts")

    def __repr__(self):
        return f"<FraudAlert  id={self.id}  level={self.alert_level}  webhook={self.n8n_webhook_sent}>"


# ══════════════════════════════════════════════════════════════
# TABLE 4: verification_tokens
# ══════════════════════════════════════════════════════════════

class VerificationToken(Base):
    """
    Verification Tokens Table — Tokens for email action links.

    How it works:
      1. Fraud is detected
      2. User receives an email:
           "Was this transaction made by you?"
           [✅ Yes, Approve] → Link contains token (action='approve')
           [❌ No, Block]    → Link contains token (action='reject')
      3. User clicks the link
      4. FastAPI validates the token
      5. Transaction status is updated

    Safety features:
      - Each token is a UUID (random, impossible to guess)
      - Token expires in 24 hours
      - Token can only be used once (is_used becomes True)
      - Two tokens are generated per transaction (approve + reject)
    """
    __tablename__ = "verification_tokens"
    __table_args__ = (
        Index('ix_verification_tokens_transaction_id', 'transaction_id'),
    )

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)

    # Unique secret token (UUID v4 format)
    token  = Column(String(100), unique=True, nullable=False, index=True)

    # Yeh token click hone par kya karega
    action = Column(String(20), nullable=False)   # sirf 'approve' ya 'reject'

    # Token ki validity
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used    = Column(Boolean, default=False)
    used_at    = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: VerificationToken → Transaction (Many-to-One)
    transaction = relationship("Transaction", back_populates="verification_tokens")

    def __repr__(self):
        return (
            f"<VerificationToken  id={self.id}  "
            f"action={self.action}  "
            f"is_used={self.is_used}>"
        )


# ══════════════════════════════════════════════════════════════
# TABLE 5: audit_logs
# ══════════════════════════════════════════════════════════════

class AuditLog(Base):
    """
    Audit Logs Table — Permanent record of every action in the system.

    This table:
      ✔ Is read-only (no entries can be deleted or edited)
      ✔ Is mandatory for bank regulations
      ✔ Is highly useful for debugging
      ✔ Provides a complete trail of "who did what and when"

    A log entry is created for each of these actions:
      - TRANSACTION_CREATED       → New transaction submitted
      - ML_SCORE_ASSIGNED         → ML model assigned a score
      - FRAUD_ALERT_TRIGGERED     → Suspicious transaction detected
      - WEBHOOK_SENT_TO_N8N       → Signal sent to n8n
      - EMAIL_SENT_TO_USER        → Email sent to the user
      - USER_APPROVED             → Approved by the user
      - USER_REJECTED             → Rejected by the user
      - TRANSACTION_AUTO_APPROVED → Automatically approved by ML
      - TRANSACTION_BLOCKED       → Blocked by the system
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('ix_audit_logs_user_id', 'user_id'),
    )

    id             = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    # Kya hua
    action      = Column(String(100), nullable=False)
    description = Column(Text,        nullable=True)

    # Status change track karna
    old_status = Column(String(20), nullable=True)   # Pehle kya tha
    new_status = Column(String(20), nullable=True)   # Ab kya hai

    # Kisne kiya
    performed_by = Column(String(50), nullable=False)
    # Possible values: 'user', 'system', 'n8n', 'ml_model', 'admin'

    ip_address = Column(String(45), nullable=True)   # IPv4 ya IPv6

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: AuditLog → Transaction (Many-to-One)
    transaction = relationship("Transaction", back_populates="audit_logs")

    def __repr__(self):
        return (
            f"<AuditLog  id={self.id}  "
            f"action={self.action}  "
            f"by={self.performed_by}>"
        )


# ══════════════════════════════════════════════════════════════
# TABLE 6: refresh_tokens  (JWT Refresh Token Store)
# ══════════════════════════════════════════════════════════════

class RefreshToken(Base):
    """
    Refresh Token Table — Server-side JWT refresh token storage.

    Why store refresh tokens server-side?
      - Enables token revocation (logout, stolen token handling)
      - Prevents reuse after logout (blacklist mechanism)
      - Supports per-device session management

    Flow:
      1. Login  → access_token (15 min) + refresh_token (7 days) created
      2. Expired access_token → POST /api/v1/auth/refresh with refresh_token
      3. Logout → refresh_token is_revoked = True (cannot be reused)
    """
    __tablename__ = "refresh_tokens"

    id         = Column(Integer,     primary_key=True, index=True, autoincrement=True)
    user_id    = Column(Integer,     ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Stored as a SHA-256 hash of the actual token (never store raw JWT)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)

    # Device/session identifier (optional — helps multi-device users)
    device_info = Column(String(255), nullable=True)

    # Lifecycle
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    is_revoked  = Column(Boolean, default=False,  nullable=False)
    revoked_at  = Column(DateTime(timezone=True), nullable=True)

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship: RefreshToken → User (Many-to-One)
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return (
            f"<RefreshToken  id={self.id}  "
            f"user_id={self.user_id}  "
            f"revoked={self.is_revoked}>"
        )
