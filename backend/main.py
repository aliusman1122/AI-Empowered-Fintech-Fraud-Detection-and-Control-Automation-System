"""
backend/main.py
================
FastAPI application entry point.
≤100 lines — contains ONLY wiring, no business logic.
All routes are in backend/routers/.
All logic is in backend/services/ and backend/repositories/.
"""
import logging
import subprocess

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from backend.core.config import settings
from backend.core.dependencies import limiter
from backend.core.exceptions import AppException
from backend.core.logger import setup_logging
from backend.core.middleware import RequestIDMiddleware, LoggingMiddleware, SecurityHeadersMiddleware
from backend.routers import auth, transactions, stats, webhook, health

from prometheus_fastapi_instrumentator import Instrumentator
import structlog

setup_logging()
logger = structlog.get_logger("finguard.main")

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "FinGuard — AI Fraud Detection API",
    description = "Real-time AI-powered fraud detection for fintech transactions.",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── Rate limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware (added in LIFO order — last added runs first) ──────────────────
app.add_middleware(SecurityHeadersMiddleware, is_production=settings.is_production)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    # When debugging CORS locally, inject ["*"]. Starlette strictly enforces that 
    # allow_credentials CANNOT be True if origins is a raw wildcard.
    allow_origins     = ["*"] if not settings.is_production else settings.cors_origins_list,
    allow_credentials = False if not settings.is_production else True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Global exception handler ──────────────────────────────────────────────────
from backend.core.exception_handlers import add_exception_handlers
add_exception_handlers(app)

if settings.PROMETHEUS_ENABLED:
    Instrumentator().instrument(app).expose(app, include_in_schema=False)
    logger.info("metrics_endpoint_enabled", path="/metrics")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(stats.router)
app.include_router(webhook.router)

# ── Lifecycle events ──────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    from backend.services.ml_service import load_model_on_startup
    from backend.core.redis import redis_client
    from backend.database import engine
    from sqlalchemy import text
    
    await redis_client.connect()
    
    logger.info("Checking database tables...")
    try:
        async with engine.connect() as conn:
            # Query pg_tables to check if our expected tables exist
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result]
            if "users" not in tables or "transactions" not in tables:
                logger.error("Missing database tables detected. Please run 'alembic upgrade head'.")
            else:
                logger.info("Database tables verified.")
    except Exception as e:
        logger.error(f"Database table verification failed: {e}")
        
    load_model_on_startup()
    
    logger.info("api_started", env=settings.ENVIRONMENT)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    from backend.database import engine
    from backend.core.redis import redis_client
    await redis_client.disconnect()
    await engine.dispose()
    logger.info("FinGuard API shutdown complete.")
