
"""In-memory HTTP monitoring for the Day 3 workshop.

Scope:
- Metrics belong to one running server process.
- The latency window retains at most 500 observations.
- Metrics reset when the server restarts.
- This module is not a replacement for production telemetry.
"""
from collections import Counter, deque
from datetime import datetime, timezone
from threading import Lock

_LOCK = Lock()

_REQUESTS = 0
_ERRORS = 0
_ENDPOINTS = Counter()
_STATUSES = Counter()
_LATENCIES_MS = deque(maxlen=500)

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


def _percentile(values, percentile):
    if not values:
        return None

    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * percentile))
    return round(ordered[index], 2)


def snapshot():
    """Return a consistent snapshot of current process metrics."""
    with _LOCK:
        latencies = list(_LATENCIES_MS)
        requests = _REQUESTS
        errors = _ERRORS

        error_rate = (
            round(errors / requests * 100, 2)
            if requests else None
        )

        average_latency = (
            round(sum(latencies) / len(latencies), 2)
            if latencies else None
        )

        p95_latency = _percentile(latencies, 0.95)

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
            p95_latency is not None
            and p95_latency >= LATENCY_WARNING_MS
        ):
            warnings.append({
                "code": "HTTP_LATENCY_HIGH",
                "message": (
                    "Observed p95 latency is at or above "
                    f"{LATENCY_WARNING_MS} ms."
                )
            })

        return {
            "scope": "current_server_process",
            "started_at_utc": _STARTED_AT,
            "requests_total": requests,
            "errors_total": errors,
            "error_rate_percent": error_rate,
            "latency_sample_count": len(latencies),
            "average_latency_ms": average_latency,
            "p95_latency_ms": p95_latency,
            "requests_by_endpoint": dict(_ENDPOINTS),
            "responses_by_status": dict(_STATUSES),
            "warning_thresholds": {
                "error_rate_percent": ERROR_WARNING_PERCENT,
                "p95_latency_ms": LATENCY_WARNING_MS
            },
            "warnings": warnings
        }
