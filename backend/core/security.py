"""
backend/core/security.py
=========================
Re-exports pure-crypto functions from auth_service.
No database access here — only password hashing and JWT creation/decoding.
This module is the canonical source for import in routers and services.
"""

# Re-export everything that is pure crypto (no DB)
from backend.services.auth_service import (  # noqa: F401
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    _hash_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
import re

def validate_password(password: str) -> None:
    """Enforces strict password complexity rules."""
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r'[\W_]', password):
        raise ValueError("Password must contain at least one special character.")
    
    # Reject extremely common passwords
    common_passwords = {"password123!", "admin123456!", "qwertyuiop1!", "1234567890Aa!"}
    if password.lower() in common_passwords:
        raise ValueError("Password appears in common password list. Choose a more secure password.")
