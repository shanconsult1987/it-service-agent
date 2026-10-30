
"""In-memory HTTP and LLM monitoring for Day 3.

HTTP metrics:
- Request and error counts
- Endpoint and status counts
- Average and p95 latency

LLM metrics:
- Call and error counts
- Prompt, completion and total tokens
- Token usage by model and operation
- Average LLM latency

Scope:
- Metrics belong to one running server process.
- HTTP latency retains at most 500 observations.
- LLM latency retains at most 500 observations.
- Metrics reset when the server restarts.
- This is not a durable production telemetry backend.
"""
from collections import Counter, deque
from datetime import datetime, timezone
from threading import Lock

_LOCK = Lock()

# HTTP metrics
_REQUESTS = 0
_ERRORS = 0
_ENDPOINTS = Counter()
_STATUSES = Counter()
_LATENCIES_MS = deque(maxlen=500)

# LLM metrics
_LLM_CALLS = 0
_LLM_ERRORS = 0
_LLM_USAGE_AVAILABLE = 0

_LLM_PROMPT_TOKENS = 0
_LLM_COMPLETION_TOKENS = 0
_LLM_TOTAL_TOKENS = 0

_LLM_MODELS = Counter()
_LLM_OPERATIONS = Counter()
_LLM_LATENCIES_MS = deque(maxlen=500)

_STARTED_AT = datetime.now(timezone.utc).isoformat()

# Workshop thresholds. Tune these using actual service requirements.
ERROR_WARNING_PERCENT = 5.0
LATENCY_WARNING_MS = 1500.0


def record_request(path, status, elapsed_ms):
    """Record one completed HTTP response."""
    global _REQUESTS, _ERRORS

    elapsed_ms = max(0.0, float(elapsed_ms))

    with _LOCK:
        _REQUESTS += 1
        _ENDPOINTS[str(path)] += 1
        _STATUSES[str(status)] += 1

        if int(status) >= 400:
            _ERRORS += 1

        _LATENCIES_MS.append(round(elapsed_ms, 2))


def record_llm_call(
    model,
    operation,
    prompt_tokens=None,
    completion_tokens=None,
    total_tokens=None,
    elapsed_ms=0.0,
    success=True
):
    """Record one LLM call and its API-reported token usage.

    Missing usage is represented as unavailable, not as zero tokens.
    """
    global _LLM_CALLS
    global _LLM_ERRORS
    global _LLM_USAGE_AVAILABLE
    global _LLM_PROMPT_TOKENS
    global _LLM_COMPLETION_TOKENS
    global _LLM_TOTAL_TOKENS

    elapsed_ms = max(0.0, float(elapsed_ms))

    usage_available = all(
        value is not None
        for value in (
            prompt_tokens,
            completion_tokens,
            total_tokens
        )
    )

    with _LOCK:
        _LLM_CALLS += 1

        if not success:
            _LLM_ERRORS += 1

        _LLM_MODELS[str(model or "unknown")] += 1
        _LLM_OPERATIONS[str(operation or "unspecified")] += 1

        _LLM_LATENCIES_MS.append(round(elapsed_ms, 2))

        if usage_available:
            prompt = int(prompt_tokens)
            completion = int(completion_tokens)
            total = int(total_tokens)

            _LLM_USAGE_AVAILABLE += 1
            _LLM_PROMPT_TOKENS += prompt
            _LLM_COMPLETION_TOKENS += completion
            _LLM_TOTAL_TOKENS += total


def _percentile(values, percentile):
    if not values:
        return None

    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * percentile))

    return round(ordered[index], 2)


def snapshot():
    """Return a consistent snapshot of HTTP and LLM metrics."""
    with _LOCK:
        http_latencies = list(_LATENCIES_MS)
        llm_latencies = list(_LLM_LATENCIES_MS)

        requests = _REQUESTS
        errors = _ERRORS

        error_rate = (
            round(errors / requests * 100, 2)
            if requests else None
        )

        average_http_latency = (
            round(
                sum(http_latencies) / len(http_latencies),
                2
            )
            if http_latencies else None
        )

        p95_http_latency = _percentile(
            http_latencies,
            0.95
        )

        average_llm_latency = (
            round(
                sum(llm_latencies) / len(llm_latencies),
                2
            )
            if llm_latencies else None
        )

        warnings = []

        if (
            error_rate is not None
            and error_rate >= ERROR_WARNING_PERCENT
        ):
            warnings.append({
                "code": "HTTP_ERROR_RATE_HIGH",
                "message": (
                    "Observed HTTP error rate is at or above "
                    f"{ERROR_WARNING_PERCENT}%."
                )
            })

        if (
            p95_http_latency is not None
            and p95_http_latency >= LATENCY_WARNING_MS
        ):
            warnings.append({
                "code": "HTTP_LATENCY_HIGH",
                "message": (
                    "Observed HTTP p95 latency is at or above "
                    f"{LATENCY_WARNING_MS} ms."
                )
            })

        return {
            "scope": "current_server_process",
            "started_at_utc": _STARTED_AT,

            "http": {
                "requests_total": requests,
                "errors_total": errors,
                "error_rate_percent": error_rate,
                "latency_sample_count": len(http_latencies),
                "average_latency_ms": average_http_latency,
                "p95_latency_ms": p95_http_latency,
                "requests_by_endpoint": dict(_ENDPOINTS),
                "responses_by_status": dict(_STATUSES)
            },

            "llm": {
                "calls_total": _LLM_CALLS,
                "errors_total": _LLM_ERRORS,
                "usage_available_calls": _LLM_USAGE_AVAILABLE,
                "usage_unavailable_calls": (
                    _LLM_CALLS - _LLM_USAGE_AVAILABLE
                ),
                "prompt_tokens_total": _LLM_PROMPT_TOKENS,
                "completion_tokens_total": _LLM_COMPLETION_TOKENS,
                "total_tokens": _LLM_TOTAL_TOKENS,
                "average_latency_ms": average_llm_latency,
                "latency_sample_count": len(llm_latencies),
                "calls_by_model": dict(_LLM_MODELS),
                "calls_by_operation": dict(_LLM_OPERATIONS)
            },

            "warning_thresholds": {
                "error_rate_percent": ERROR_WARNING_PERCENT,
                "p95_http_latency_ms": LATENCY_WARNING_MS
            },

            "warnings": warnings
        }
