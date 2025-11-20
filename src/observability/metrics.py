"""
Custom metrics definitions for the RAG system.
"""

from opentelemetry import metrics

meter = metrics.get_meter("rag.metrics")

# Counter: Total queries processed
QUERY_COUNTER = meter.create_counter(
    "rag_queries_total",
    description="Total number of queries processed",
    unit="1"
)

# Histogram: Query latency
QUERY_LATENCY = meter.create_histogram(
    "rag_query_latency_seconds",
    description="End-to-end query latency",
    unit="s"
)

# Histogram: Token usage
TOKEN_USAGE = meter.create_histogram(
    "rag_token_usage",
    description="Number of tokens used per query",
    unit="1"
)

# Gauge: Feedback score (average)
FEEDBACK_SCORE = meter.create_observable_gauge(
    "rag_feedback_score_avg",
    description="Average user feedback score (1-5)",
    unit="1"
)

# Counter: Zero result queries
ZERO_RESULT_COUNTER = meter.create_counter(
    "rag_zero_results_total",
    description="Total queries returning zero results",
    unit="1"
)
