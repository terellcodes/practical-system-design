"""
OpenTelemetry tracing configuration - shared across all services.
"""
import os
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.context import Context

logger = logging.getLogger(__name__)
_tracer: Optional[trace.Tracer] = None


class FilteringSpanExporter(SpanExporter):
    """
    Span exporter that filters out unwanted ASGI lifecycle spans.

    Filters spans with names ending in:
    - "http send" (ASGI response sending events)
    - "http receive" (ASGI request receiving events)
    """

    def __init__(self, wrapped_exporter: SpanExporter):
        self.wrapped_exporter = wrapped_exporter
        self.filtered_suffixes = ("http send", "http receive")

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        """Filter spans and export the remaining ones."""
        filtered_spans = [
            span for span in spans
            if not any(span.name.endswith(suffix) for suffix in self.filtered_suffixes)
        ]

        if not filtered_spans:
            return SpanExportResult.SUCCESS

        return self.wrapped_exporter.export(filtered_spans)

    def shutdown(self) -> None:
        """Shutdown the wrapped exporter."""
        self.wrapped_exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush the wrapped exporter."""
        return self.wrapped_exporter.force_flush(timeout_millis)


def setup_tracing(
    service_name: str,
    enable_kafka: bool = False,
    enable_redis: bool = True,
    enable_httpx: bool = True,
    filter_asgi_spans: bool = True
):
    """
    Initialize OpenTelemetry tracing with Jaeger exporter.

    Args:
        service_name: Name of the service for trace identification
        enable_kafka: Enable Kafka instrumentation (only for chat-service/lambda)
        enable_redis: Enable Redis instrumentation
        enable_httpx: Enable httpx HTTP client instrumentation
        filter_asgi_spans: Filter out ASGI http send/receive spans (default: True)
    """
    global _tracer

    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "1.0.0"),
    })

    provider = TracerProvider(resource=resource)

    jaeger_endpoint = os.getenv(
        "OTEL_EXPORTER_JAEGER_ENDPOINT",
        "http://jaeger:14268/api/traces"
    )

    jaeger_exporter = JaegerExporter(collector_endpoint=jaeger_endpoint)

    # Optionally wrap exporter with filtering to remove ASGI lifecycle spans
    if filter_asgi_spans:
        exporter = FilteringSpanExporter(jaeger_exporter)
        logger.info("ASGI span filtering enabled (http send/receive spans will be filtered)")
    else:
        exporter = jaeger_exporter

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    _tracer = trace.get_tracer(__name__)

    # Auto-instrument libraries based on flags (lazy imports to avoid missing deps)
    if enable_httpx:
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX instrumentation enabled")
        except ImportError:
            logger.warning("httpx not installed, skipping HTTPX instrumentation")

    if enable_redis:
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            RedisInstrumentor().instrument()
            logger.info("Redis instrumentation enabled")
        except ImportError:
            logger.warning("redis instrumentation not available, skipping")

    if enable_kafka:
        try:
            from opentelemetry.instrumentation.kafka import KafkaInstrumentor
            KafkaInstrumentor().instrument()
            logger.info("Kafka instrumentation enabled")
        except ImportError:
            logger.warning("kafka instrumentation not available, skipping")

    logger.info(f"Tracing initialized for {service_name} -> {jaeger_endpoint}")


def instrument_fastapi(app):
    """Instrument FastAPI application."""
    FastAPIInstrumentor.instrument_app(app)
    logger.info("FastAPI instrumented for tracing")


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    if _tracer is None:
        raise RuntimeError("Tracing not initialized")
    return _tracer


def get_current_trace_id() -> str:
    """Get current trace ID as hex string."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, '032x')
    return ""


def get_current_span_id() -> str:
    """Get current span ID as hex string."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().span_id, '016x')
    return ""
