"""Pydantic base response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic schema with common config."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SuccessResponse(BaseSchema, Generic[T]):
    """Generic success response wrapper."""

    success: bool = True
    data: T
    message: str = "OK"


class ErrorDetail(BaseSchema):
    """Error detail schema."""

    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseSchema):
    """Standard error response."""

    success: bool = False
    error: ErrorDetail
    request_id: str | None = None


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    success: bool = True
    data: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def create(
        cls,
        data: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(data=data, total=total, page=page, page_size=page_size, pages=pages)


class HealthResponse(BaseSchema):
    """Health check response."""

    status: str = "healthy"
    service: str
    version: str = "0.1.0"
    details: dict[str, Any] = {}
