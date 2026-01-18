"""
Observability package - Distributed tracing and correlation ID support.
"""
from .tracing import (
    setup_tracing,
    instrument_fastapi,
    get_tracer,
    get_current_trace_id,
    get_current_span_id,
)
from .correlation import (
    CorrelationIdMiddleware,
    get_correlation_id,
    CORRELATION_ID_HEADER,
)

__all__ = [
    'setup_tracing',
    'instrument_fastapi',
    'get_tracer',
    'get_current_trace_id',
    'get_current_span_id',
    'CorrelationIdMiddleware',
    'get_correlation_id',
    'CORRELATION_ID_HEADER',
]
