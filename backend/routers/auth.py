"""
backend/routers/auth.py
========================
Authentication endpoints.
All DB operations use AsyncSession + repositories.
Pure crypto (hashing, JWT) comes from core.security (re-exports auth_service).
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend import schemas, models
from backend.core.config import settings
from backend.core.dependencies import get_db, get_current_user, limiter
from backend.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    _hash_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.repositories import user_repository, refresh_token_repository

logger = logging.getLogger("finguard.auth")

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_token_response(
    user: models.User,
    access_token: str,
    refresh_token: str,
) -> schemas.TokenResponse:
    return schemas.TokenResponse(
        access_token  = access_token,
        refresh_token = refresh_token,
        token_type    = "bearer",
        user_id       = user.id,
        email         = user.email,
        role          = user.role,
        expires_in    = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── REGISTER ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201, summary="Create a new user account")
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    body: schemas.UserRegister,
    db: AsyncSession = Depends(get_db),
):
    existing = await user_repository.get_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = await user_repository.create_user(db, {
        "email":           body.email,
        "full_name":       body.full_name,
        "phone":           body.phone,
        "hashed_password": get_password_hash(body.password),
        "role":            models.UserRole.user.value,
        "is_active":       True,
        "is_verified":     False,
    })
    logger.info("New user registered: %s (id=%d)", user.email, user.id)
    return {
        "id":        user.id,
        "email":     user.email,
        "full_name": user.full_name,
        "role":      user.role,
        "message":   "Account created. Please verify your email.",
    }


from fastapi.security import OAuth2PasswordRequestForm

# ── LOGIN ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=schemas.TokenResponse, summary="Login")
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # OAuth2 specifies 'username', which we internally map strictly to the user's email
    user = await user_repository.get_by_email(db, form_data.username)

    # Constant-time path: always verify against *some* hash to prevent timing attacks
    _dummy = "$2b$12$invalidhashplaceholderXXXXXXXXXXXXXXXXXXXXXX"
    stored = user.hashed_password if user else _dummy

    if not verify_password(form_data.password, stored) or not user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated.")

    token_data    = {"sub": user.email, "user_id": user.id, "role": user.role}
    access_token  = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    expires_at   = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    device_info  = request.headers.get("User-Agent", "unknown")
    await refresh_token_repository.store_hash(
        db, user.id, refresh_token, expires_at, device_info=device_info
    )

    logger.info("Login: %s", user.email)
    return _build_token_response(user, access_token, refresh_token)


# ── REFRESH ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=schemas.TokenResponse, summary="Refresh access token")
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    body: schemas.RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    # Decode JWT (checks signature + expiry)
    try:
        from backend.core.security import ALGORITHM, SECRET_KEY
        from jose import jwt, JWTError
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token is invalid or expired.")

    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token.")

    # Validate DB record (not revoked, not expired)
    db_token = await refresh_token_repository.validate_hash(db, body.refresh_token)
    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token is revoked or expired.")

    user = await user_repository.get_by_id(db, payload.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated.")

    # Rotate: revoke old, issue new pair
    await refresh_token_repository.revoke(db, body.refresh_token)

    token_data    = {"sub": user.email, "user_id": user.id, "role": user.role}
    new_access    = create_access_token(data=token_data)
    new_refresh   = create_refresh_token(data=token_data)
    expires_at    = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    device_info   = request.headers.get("User-Agent", "unknown")
    await refresh_token_repository.store_hash(db, user.id, new_refresh, expires_at, device_info)

    return _build_token_response(user, new_access, new_refresh)


# ── LOGOUT ────────────────────────────────────────────────────────────────────

@router.post("/logout", summary="Logout — revoke refresh token")
@limiter.limit("20/minute")
async def logout(
    request: Request,
    body: schemas.LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    revoked = await refresh_token_repository.revoke(db, body.refresh_token)
    return {"message": "Logged out successfully." if revoked else "Token already revoked."}


# ── ME ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=schemas.UserProfile, summary="Get current user profile")
async def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
