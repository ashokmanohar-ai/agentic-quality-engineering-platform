"""OpenTelemetry setup with opt-in export and safe defaults."""

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from app.config import get_settings


def configure_tracing() -> None:
    if not get_settings().otel_enabled:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": "agentic-qe-platform"}))
    trace.set_tracer_provider(provider)


def tracer() -> trace.Tracer:
    return trace.get_tracer("app.agentic-qe")
