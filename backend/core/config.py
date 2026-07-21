"""
backend/core/config.py
======================
Centralised settings loaded from the .env file.
All environment variables are accessed through `settings.<FIELD>` —
never use os.getenv() in application code.
"""

from functools import cached_property
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",           # silently ignore any unknown vars in .env
    )

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fraud_detection_db"

    # ── JWT ──────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-32-CHARS-MIN"
    JWT_ALGORITHM:  str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS:   int = 7

    # ── CORS (stored as comma-separated string, parsed into list) ─
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    # ── Deployment ───────────────────────────────────────────────
    ENVIRONMENT: str = "development"

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_PASSWORD: str = ""
    VELOCITY_WINDOW_MINUTES: int = 5
    VELOCITY_THRESHOLD: int = 3

    # ── Observability ────────────────────────────────────────────
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # ── MLflow Config ─────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_MODEL_STAGE: str = "Production"

    # ── n8n Automation ───────────────────────────────────────────
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/fintech-fraud-alert"

    # ── SMTP (optional) ──────────────────────────────────────────
    SMTP_HOST:     str = ""
    SMTP_PORT:     int = 587
    SMTP_USER:     str = ""
    SMTP_PASSWORD: str = ""

    # ── Rate Limiting ────────────────────────────────────────────
    RATE_LIMIT_LOGIN:    str = "5/minute"
    RATE_LIMIT_REGISTER: str = "20/minute"
    RATE_LIMIT_GLOBAL:   str = "300/minute"

    @cached_property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @cached_property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


# Singleton — import this everywhere
settings = Settings()
