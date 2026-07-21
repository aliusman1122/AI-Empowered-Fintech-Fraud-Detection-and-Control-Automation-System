from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog
from backend.core.exceptions import AppException

logger = structlog.get_logger("finguard.exceptions")

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        rid = getattr(request.state, "request_id", "n/a")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_type,
                "message": exc.message,
                "detail": exc.detail,
                "request_id": rid,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = getattr(request.state, "request_id", "n/a")
        logger.exception("Unhandled exception [rid=%s]: %s", rid, exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred.",
                "detail": {},
                "request_id": rid,
            },
        )
