"""Shared Pydantic schemas."""

from shared.schemas.base import (
    BaseSchema,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    SuccessResponse,
)

__all__ = [
    "BaseSchema",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "SuccessResponse",
]
