"""
backend/core/middleware.py
==========================
ASGI middleware components:
  - RequestIDMiddleware  : attaches a uuid4 to every request (for tracing)
  - LoggingMiddleware    : structured request/response logs
  - SecurityHeadersMiddleware : injects hardening headers on all responses
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import structlog

logger = structlog.get_logger("finguard.http")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generates a unique UUID per request and attaches it to request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status, and duration via structured logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = getattr(request.state, "request_id", "-")
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=rid,
            method=request.method,
            path=request.url.path,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration = (time.perf_counter() - start) * 1000  # ms
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration, 2),
            )
            return response
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed",
                error=str(e),
                duration_ms=round(duration, 2),
            )
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security response headers on every response.
    HSTS is only added in production to avoid breaking local HTTP dev servers.
    """

    def __init__(self, app, is_production: bool = False):
        super().__init__(app)
        self._is_production = is_production

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"]       = "1; mode=block"
        response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
        if self._is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response
