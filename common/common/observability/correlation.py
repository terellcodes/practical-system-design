"""
Correlation ID middleware - shared across all services.

Why all services need this:
- user-service: Receives API requests, needs to extract/generate correlation ID
- chat-service: Receives requests AND calls user-service (extract + propagate)
- copilot-service: Makes calls to user/chat services (must propagate)
"""
import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle correlation IDs across requests.

    - Extracts correlation ID from incoming request headers
    - Generates new UUID if not present
    - Stores in request.state for access in route handlers
    - Adds to response headers
    - Attaches to active span as attribute
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate correlation ID
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in request state
        request.state.correlation_id = correlation_id

        # Attach to current span (if tracing active)
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span.set_attribute("correlation.id", correlation_id)

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response


def get_correlation_id(request: Request) -> str:
    """Helper to get correlation ID from request state."""
    return getattr(request.state, 'correlation_id', str(uuid.uuid4()))
