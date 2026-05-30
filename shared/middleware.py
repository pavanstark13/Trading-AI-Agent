"""FastAPI middleware: request ID injection and timing."""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request ID into each request and response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Log request timing and add X-Process-Time header."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"

        # Log slow requests (> 1000ms)
        if elapsed_ms > 1000:
            logger.warning(
                "Slow request detected",
                method=request.method,
                path=request.url.path,
                duration_ms=round(elapsed_ms, 2),
            )
        else:
            logger.debug(
                "Request processed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(elapsed_ms, 2),
            )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured access logging middleware."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip health check endpoints from verbose logging
        if request.url.path in ("/health", "/api/v1/health", "/metrics"):
            return await call_next(request)

        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query) if request.url.query else None,
            client=request.client.host if request.client else None,
        )

        response = await call_next(request)

        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response
