"""
backend/core/exceptions.py
===========================
Custom application exceptions. These are caught by the global exception
handler in main.py and serialised into the standard JSON error envelope.
"""


class AppException(Exception):
    """Base class for all application exceptions."""
    status_code: int = 500
    error_type:  str = "InternalError"

    def __init__(self, message: str = "An unexpected error occurred", detail: dict | None = None):
        self.message = message
        self.detail  = detail or {}
        super().__init__(message)


class NotFoundException(AppException):
    status_code = 404
    error_type  = "NotFound"

    def __init__(self, message: str = "Resource not found", detail: dict | None = None):
        super().__init__(message, detail)


class AuthException(AppException):
    status_code = 401
    error_type  = "Unauthorized"

    def __init__(self, message: str = "Authentication failed", detail: dict | None = None):
        super().__init__(message, detail)


class ForbiddenException(AppException):
    status_code = 403
    error_type  = "Forbidden"

    def __init__(self, message: str = "Access denied", detail: dict | None = None):
        super().__init__(message, detail)


class ValidationException(AppException):
    status_code = 422
    error_type  = "ValidationError"

    def __init__(self, message: str = "Validation failed", detail: dict | None = None):
        super().__init__(message, detail)


class ConflictException(AppException):
    status_code = 409
    error_type  = "Conflict"

    def __init__(self, message: str = "Resource already exists", detail: dict | None = None):
        super().__init__(message, detail)
