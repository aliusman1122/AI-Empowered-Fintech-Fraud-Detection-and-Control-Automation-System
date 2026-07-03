# =============================================================================
# backend/schemas.py
# =============================================================================
# PURPOSE:
#   This file defines the SHAPE of data that goes IN and OUT of our API.
#   Pydantic schemas do two jobs automatically:
#     1. VALIDATION → If a user sends "amount": "hello", Pydantic rejects it
#                     because "hello" is not a valid number.
#     2. SERIALIZATION → Converts Python objects to JSON for API responses.
#
# DIFFERENCE BETWEEN schemas.py and models.py:
#   models.py  → Defines database tables (what gets STORED)
#   schemas.py → Defines API contracts (what gets SENT and RECEIVED)
#   They are kept separate because:
#     - You never want to expose DB internals directly (e.g., verification tokens)
#     - API input shape ≠ database storage shape
# =============================================================================

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic import EmailStr
from enum import Enum
# =============================================================================
# REQUEST SCHEMAS (what the user SENDS to the API)
# =============================================================================
class MerchantCategory(str, Enum):
    electronics = "electronics"
    food = "food"
    travel = "travel"
    gambling = "gambling"
    crypto = "crypto"
    wire_transfer = "wire_transfer"
    foreign_exchange = "foreign_exchange"
    other = "other"
class TransactionInput(BaseModel):
    """
    The JSON body a user must send to POST /api/v1/transactions/predict.

    Every field has:
        - Type annotation (str, float, int)
        - Field() with validation rules and description
        - An example value (shown in /docs)

    IMPORTANT: These column names must match what the ML model was trained on.
    Check your src/validation.py → REQUIRED_FEATURE_COLUMNS to verify.
    """

    # Transaction financial details
    amount: float = Field(
        ...,
        gt=0,
        description="Transaction amount in USD. Must be greater than 0.",
        example=2499.99
    )
    hour: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hour of the day when the transaction occurred (0=midnight, 23=11PM).",
        example=2
    )

    # Risk scores (pre-computed by the bank's systems before calling this API)
    device_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Risk score for the device used (0.0 = safe, 1.0 = very risky).",
        example=0.87
    )
    ip_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Risk score for the IP address (0.0 = safe, 1.0 = very risky).",
        example=0.91
    )

    # Transaction context
    merchant_category: MerchantCategory = Field(
        ...,
        description="Category of the merchant. Examples: electronics, food, travel, gambling.",
        example="electronics"
    )
    transaction_type: Optional[str] = Field(
        default="online",
        description="How the transaction was made. Examples: online, pos, wire_transfer, atm.",
        example="online"
    )
    country: Optional[str] = Field(
        default="US",
        description="Country where the transaction originated (2-letter code).",
        example="PK"
    )

    # Email for verification workflow (Phase 5)
    user_email: Optional[EmailStr] = Field(
        default=None,
        description="User's email address. If provided and transaction is suspicious, a verification email is sent.",
        example="user@example.com"
    )

    class Config:
        # This adds a working example to the /docs swagger UI
        json_schema_extra = {
            "example": {
                "amount": 2499.99,
                "hour": 2,
                "device_risk_score": 0.87,
                "ip_risk_score": 0.91,
                "merchant_category": "electronics",
                "transaction_type": "online",
                "country": "PK",
                "user_email": "customer@example.com"
            }
        }


# =============================================================================
# RESPONSE SCHEMAS (what the API RETURNS to the user)
# =============================================================================

class PredictionResponse(BaseModel):
    """
    Response returned after POST /api/v1/transactions/predict.
    This is what the frontend (React dashboard) will receive and display.
    """
    transaction_id:    str         # Unique ID for this transaction
    fraud_probability: float       # 0.0000 to 1.0000 (the raw ML output)
    fraud_flag:        bool        # True = flagged as fraud
    risk_level:        str         # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    status:            str         # "APPROVED" | "FLAGGED" | "VERIFICATION_SENT"
    reason_codes:      List[str]   # Human-readable list of risk reasons
    message:           str         # User-friendly summary of the decision
    threshold_used:    float       # The threshold that was applied


class TransactionStatusResponse(BaseModel):
    """
    Response returned after GET /api/v1/transactions/{id}.
    Used by the frontend to poll and check if a user has responded to email.
    """
    transaction_id:    str
    status:            str
    fraud_probability: Optional[float]
    fraud_flag:        Optional[bool]
    risk_level:        Optional[str]
    amount:            Optional[float]
    created_at:        Optional[datetime]
    updated_at:        Optional[datetime]
    message:           str

    class Config:
        from_attributes = True  # Allows creating from SQLAlchemy model objects


class TransactionListItem(BaseModel):
    """
    One item in the list returned by GET /api/v1/transactions/.
    Contains less detail than the full status response (for dashboard table display).
    """
    transaction_id:    str
    amount:            Optional[float]
    status:            str
    fraud_probability: Optional[float]
    risk_level:        Optional[str]
    merchant_category: Optional[str]
    created_at:        Optional[datetime]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """
    Response for GET /api/v1/stats.
    Shows aggregate counts for the dashboard summary cards.
    """
    total_transactions:      int
    approved_count:          int
    blocked_count:           int
    under_review_count:      int
    fraud_rate_percent:      float    # What % of all transactions were flagged
    avg_fraud_probability:   float    # Average fraud score across all transactions
    model_threshold:         float
    timestamp:               str


class AuditLogItem(BaseModel):
    """
    One entry in the audit log returned by GET /api/v1/audit-logs.
    """
    id:             int
    transaction_id: str
    action:         str
    details:        Optional[str]
    performed_by:   str
    timestamp:      Optional[str]