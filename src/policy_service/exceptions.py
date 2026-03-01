"""Service-level exceptions mapped to standard error codes."""

from __future__ import annotations


class ServiceError(Exception):
    """Base for all policy service errors."""

    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class PolicyConfigError(ServiceError):
    """Policy configuration is missing or corrupt."""

    def __init__(self, message: str = "Policy configuration error") -> None:
        super().__init__(message, code="INTERNAL_ERROR", status_code=500)


class ValidationError(ServiceError):
    """Request validation failed."""

    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(message, code="INVALID_REQUEST", status_code=400)
