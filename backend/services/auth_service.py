"""
=============================================================================
backend/services/auth_service.py
=============================================================================
PURPOSE:
  Complete authentication service implementing:
    - BCrypt password hashing (12 rounds — industry standard)
    - JWT access tokens (15 minute expiry)
    - JWT refresh tokens (7 day expiry, stored server-side as SHA-256 hash)
    - Token verification and current-user dependency
    - Refresh token rotation (old token revoked, new one issued)
    - Logout (server-side token revocation)

  SECURITY DECISIONS:
    - Refresh tokens are stored as SHA-256 hashes (never raw JWTs) 
    - Access token uses HS256 with a strong env-loaded secret key
    - bcrypt rounds=12 balances security and performance (~250ms hash time)
    - Constant-time comparison used by passlib prevents timing attacks
=============================================================================
"""

import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
# In production: set JWT_SECRET to a long random string (32+ chars)
# Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.getenv("JWT_SECRET", os.getenv("JWT_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION-USE-ENV-VAR"))
ALGORITHM  = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES  = 15        # Short-lived: reduces window of misuse
REFRESH_TOKEN_EXPIRE_DAYS    = 7         # Long-lived: stored server-side & revocable

# ─── HTTP BEARER SCHEME ──────────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)

# ─── CREDENTIALS EXCEPTION ───────────────────────────────────────────────────
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials. Please log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


# =============================================================================
# PASSWORD UTILITIES
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a bcrypt hash.
    Uses constant-time comparison (bcrypt internals) to prevent timing attacks.

    NOTE: The old 'unsecured' fallback is intentionally removed.
    Any user with a legacy 'unsecured' password must reset via /forgot-password.
    """
    try:
        # Match the 72 byte truncation applied during hashing
        password_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        # Malformed hash — treat as invalid
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt with 12 rounds.
    Always call this before storing any password in the database.
    """
    # Truncate to 72 bytes explicitly prior to hashing to avoid bcrypt buffer errors natively
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


# =============================================================================
# JWT TOKEN CREATION
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a short-lived JWT access token (default: 15 minutes).

    Args:
        data: Payload dict. Should include 'sub' (email) and 'user_id'.
        expires_delta: Custom expiry. If None, defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp":        expire,
        "token_type": "access",
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Create a long-lived JWT refresh token (7 days).
    This token MUST be stored (hashed) in the database via store_refresh_token().

    Args:
        data: Payload dict. Should include 'sub' (email) and 'user_id'.

    Returns:
        Raw JWT string (send to client, then hash before storing).
    """
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp":        expire,
        "token_type": "refresh",
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =============================================================================
# REFRESH TOKEN DATABASE OPERATIONS
# =============================================================================

def _hash_token(raw_token: str) -> str:
    """SHA-256 hash a JWT string for safe database storage."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


def store_refresh_token(
    db: Session,
    user_id: int,
    raw_token: str,
    device_info: Optional[str] = None,
) -> models.RefreshToken:
    """
    Hash and persist a refresh token in the database.
    Called immediately after creating a refresh token on login.
    """
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = models.RefreshToken(
        user_id     = user_id,
        token_hash  = token_hash,
        device_info = device_info,
        expires_at  = expires_at,
        is_revoked  = False,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """
    Revoke (blacklist) a refresh token by its hash.
    Called on logout. Returns True if found and revoked, False otherwise.
    """
    token_hash = _hash_token(raw_token)
    db_token   = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.token_hash == token_hash,
            models.RefreshToken.is_revoked == False,
        )
        .first()
    )
    if not db_token:
        return False

    db_token.is_revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """
    Revoke ALL refresh tokens for a user (e.g., on password change, account compromise).
    Returns number of tokens revoked.
    """
    now    = datetime.now(timezone.utc)
    tokens = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.user_id    == user_id,
            models.RefreshToken.is_revoked == False,
        )
        .all()
    )
    count = 0
    for t in tokens:
        t.is_revoked = True
        t.revoked_at = now
        count += 1
    db.commit()
    return count


def validate_refresh_token(db: Session, raw_token: str) -> Optional[dict]:
    """
    Validate a raw refresh token:
      1. Decode and verify JWT signature + expiry.
      2. Check token_type == "refresh".
      3. Look up hash in database — must exist and NOT be revoked.

    Returns the decoded payload dict on success, or None on any failure.
    """
    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("token_type") != "refresh":
        return None

    token_hash = _hash_token(raw_token)
    db_token   = (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.token_hash == token_hash,
            models.RefreshToken.is_revoked == False,
        )
        .first()
    )
    if not db_token:
        return None

    # Check DB-level expiry as well
    if db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return None

    return payload


# =============================================================================
# ACCESS TOKEN VERIFICATION (FastAPI Dependency)
# =============================================================================

def verify_access_token(raw_token: str) -> dict:
    """
    Decode and validate an access token.
    Raises HTTPException(401) on any failure.
    """
    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception

    if payload.get("token_type") != "access":
        raise credentials_exception

    if payload.get("sub") is None:
        raise credentials_exception

    return payload


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    FastAPI dependency: extracts and validates Bearer token, returns User object.

    Usage in route:
        @app.get("/protected")
        async def protected(current_user: models.User = Depends(get_current_user)):
            ...
    """
    if credentials is None:
        raise credentials_exception

    payload = verify_access_token(credentials.credentials)

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def require_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    FastAPI dependency: ensures the current user has admin role.
    Raises 403 Forbidden if not.
    """
    if current_user.role != models.UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this endpoint.",
        )
    return current_user


async def require_analyst_or_above(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    FastAPI dependency: ensures the current user is analyst or admin.
    """
    allowed = {models.UserRole.admin.value, models.UserRole.analyst.value}
    if current_user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or Admin access required.",
        )
    return current_user
