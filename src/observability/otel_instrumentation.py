"""
OpenTelemetry instrumentation for the application.
Handles tracing and metrics collection.
"""

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

from config.settings import settings

def setup_telemetry(service_name: str = "rag-service"):
    """
    Configure OpenTelemetry tracing and metrics.
    """
    if not settings.observability.enable_tracing:
        return

    resource = Resource.create({
        "service.name": service_name,
        "deployment.environment": "production"
    })

    # Tracing Setup
    trace_provider = TracerProvider(resource=resource)
    otlp_exporter = OTLPSpanExporter(endpoint=settings.observability.otel_exporter_otlp_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(trace_provider)

    # Metrics Setup
    if settings.observability.enable_metrics:
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=settings.observability.otel_exporter_otlp_endpoint)
        )
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(meter_provider)

def get_tracer(name: str):
    return trace.get_tracer(name)

def get_meter(name: str):
    return metrics.get_meter(name)
