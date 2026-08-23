"""Redacted domain errors and API error response helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from typing import Any

REDACTED_VALUE = "[REDACTED]"

_SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
    re.compile(
        r"\b(?:postgresql|postgres|mysql|mariadb|mongodb|redis)://"
        r"[^\s:@/]+:[^\s@/]+@[^\s]+",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"),
    re.compile(
        r"\b(?:api[_-]?key|password|passwd|pwd|secret|token|credential)"
        r"\b\s*[:=]\s*(?:['\"][^'\"]*['\"]|[^\s,;)}]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bAuthorization\s*[:=]\s*(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]+",
        re.IGNORECASE,
    ),
)
_SENSITIVE_KEY_PATTERN = re.compile(
    r"(?:api[_-]?key|password|passwd|pwd|secret|token|credential)",
    re.IGNORECASE,
)


class ApiErrorCode(str, Enum):
    """Stable error identifiers exposed by the API."""

    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    ANALYSIS_FAILED = "analysis_failed"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class ApiError:
    """Public, redacted error payload."""

    code: ApiErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        """Return a JSON-ready representation compatible with Pydantic naming."""

        del mode
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class ApiErrorResponse:
    """Top-level API error response shape."""

    error: ApiError

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        """Return a JSON-ready representation compatible with Pydantic naming."""

        return {"error": self.error.model_dump(mode=mode)}


def redact_sensitive(value: Any) -> Any:
    """Return a copy of value with sensitive strings replaced."""

    if isinstance(value, str):
        redacted = value
        for pattern in _SENSITIVE_PATTERNS:
            redacted = pattern.sub(REDACTED_VALUE, redacted)
        return redacted

    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive(item) for item in value)

    if isinstance(value, dict):
        return {
            str(key): (
                REDACTED_VALUE
                if _SENSITIVE_KEY_PATTERN.search(str(key))
                else redact_sensitive(item)
            )
            for key, item in value.items()
        }

    return value


class DomainError(Exception):
    """Base exception for expected domain failures.

    Domain errors keep raw causes out of API responses. Callers should pass
    only actionable context in ``message`` and ``details``.
    """

    code = ApiErrorCode.INTERNAL_ERROR
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_message = "An internal error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = redact_sensitive(message or self.default_message)
        self.details = redact_sensitive(details or {})
        super().__init__(self.message)

    def to_api_error(self) -> ApiError:
        """Convert the domain exception into a redacted public payload."""

        return ApiError(
            code=self.code,
            message=self.message,
            details=self.details,
        )


class InvalidRequestError(DomainError):
    """Raised when the request is syntactically valid but cannot be accepted."""

    code = ApiErrorCode.INVALID_REQUEST
    status_code = HTTPStatus.BAD_REQUEST
    default_message = "The request is invalid."


class ResourceNotFoundError(DomainError):
    """Raised when an analysis, finding, or related resource is not found."""

    code = ApiErrorCode.NOT_FOUND
    status_code = HTTPStatus.NOT_FOUND
    default_message = "The requested resource was not found."


class DomainConflictError(DomainError):
    """Raised when a domain state transition conflicts with current state."""

    code = ApiErrorCode.CONFLICT
    status_code = HTTPStatus.CONFLICT
    default_message = "The requested operation conflicts with current state."


class AnalysisFailedError(DomainError):
    """Raised when an analysis fails with a safe, redacted failure reason."""

    code = ApiErrorCode.ANALYSIS_FAILED
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    default_message = "Analysis could not be completed."


class DependencyUnavailableError(DomainError):
    """Raised when an optional local dependency cannot serve the request."""

    code = ApiErrorCode.DEPENDENCY_UNAVAILABLE
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    default_message = "A required dependency is unavailable."


def api_error_response(error: DomainError) -> JSONResponse:
    """Build a FastAPI JSON response for a domain error."""

    from fastapi.responses import JSONResponse

    body = ApiErrorResponse(error=error.to_api_error())
    return JSONResponse(
        status_code=int(error.status_code),
        content=body.model_dump(mode="json"),
    )


async def domain_error_handler(
    request: Any,
    exc: DomainError,
) -> Any:
    """FastAPI exception handler for expected domain errors."""

    del request
    return api_error_response(exc)


async def unhandled_error_handler(
    request: Any,
    exc: Exception,
) -> Any:
    """FastAPI exception handler that avoids leaking unexpected internals."""

    del request, exc
    return api_error_response(DomainError())


def register_error_handlers(app: Any) -> None:
    """Register SecureOps API exception handlers on a FastAPI app."""

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)


__all__ = [
    "AnalysisFailedError",
    "ApiError",
    "ApiErrorCode",
    "ApiErrorResponse",
    "DependencyUnavailableError",
    "DomainConflictError",
    "DomainError",
    "InvalidRequestError",
    "REDACTED_VALUE",
    "ResourceNotFoundError",
    "api_error_response",
    "domain_error_handler",
    "redact_sensitive",
    "register_error_handlers",
    "unhandled_error_handler",
]
