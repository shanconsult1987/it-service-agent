from collections import Counter, deque

from threading import Lock


_LOCK = Lock()


_HTTP_REQUESTS = 0

_HTTP_ERRORS = 0

_HTTP_ENDPOINTS = Counter()

_HTTP_STATUSES = Counter()

_HTTP_LATENCIES = deque(
    maxlen=500
)


_LLM_CALLS = 0

_LLM_ERRORS = 0

_LLM_PROMPT_TOKENS = 0

_LLM_COMPLETION_TOKENS = 0

_LLM_TOTAL_TOKENS = 0

_LLM_LATENCIES = deque(
    maxlen=500
)

_LLM_MODELS = Counter()

_LLM_USAGE_UNAVAILABLE = 0


def record_http_request(
    endpoint,
    status,
    latency_ms
):

    global _HTTP_REQUESTS

    global _HTTP_ERRORS

    with _LOCK:

        _HTTP_REQUESTS += 1

        _HTTP_ENDPOINTS[endpoint] += 1

        _HTTP_STATUSES[str(status)] += 1

        _HTTP_LATENCIES.append(
            float(latency_ms)
        )

        if int(status) >= 400:

            _HTTP_ERRORS += 1


def record_llm_call(
    model,
    prompt_tokens=None,
    completion_tokens=None,
    total_tokens=None,
    latency_ms=0,
    error=False
):

    global _LLM_CALLS

    global _LLM_ERRORS

    global _LLM_PROMPT_TOKENS

    global _LLM_COMPLETION_TOKENS

    global _LLM_TOTAL_TOKENS

    global _LLM_USAGE_UNAVAILABLE

    with _LOCK:

        _LLM_CALLS += 1

        _LLM_MODELS[
            str(model or "unknown")
        ] += 1

        _LLM_LATENCIES.append(
            float(latency_ms)
        )

        if error:

            _LLM_ERRORS += 1

        if (
            prompt_tokens is None
            or completion_tokens is None
            or total_tokens is None
        ):

            _LLM_USAGE_UNAVAILABLE += 1

        else:

            _LLM_PROMPT_TOKENS += int(
                prompt_tokens
            )

            _LLM_COMPLETION_TOKENS += int(
                completion_tokens
            )

            _LLM_TOTAL_TOKENS += int(
                total_tokens
            )


def _stats(values):

    values = list(values)

    return {

        "count": len(values),

        "avg_ms":
            round(
                sum(values) / len(values),
                2
            ) if values else 0,

        "max_ms":
            round(
                max(values),
                2
            ) if values else 0

    }


def snapshot():

    with _LOCK:

        return {

            "http": {

                "requests": _HTTP_REQUESTS,

                "errors": _HTTP_ERRORS,

                "endpoints":
                    dict(_HTTP_ENDPOINTS),

                "statuses":
                    dict(_HTTP_STATUSES),

                "latency":
                    _stats(_HTTP_LATENCIES)

            },

            "llm": {

                "calls": _LLM_CALLS,

                "errors": _LLM_ERRORS,

                "prompt_tokens":
                    _LLM_PROMPT_TOKENS,

                "completion_tokens":
                    _LLM_COMPLETION_TOKENS,

                "total_tokens":
                    _LLM_TOTAL_TOKENS,

                "usage_unavailable":
                    _LLM_USAGE_UNAVAILABLE,

                "models":
                    dict(_LLM_MODELS),

                "latency":
                    _stats(_LLM_LATENCIES)

            }

        }


def reset_metrics():

    global _HTTP_REQUESTS

    global _HTTP_ERRORS

    global _LLM_CALLS

    global _LLM_ERRORS

    global _LLM_PROMPT_TOKENS

    global _LLM_COMPLETION_TOKENS

    global _LLM_TOTAL_TOKENS

    global _LLM_USAGE_UNAVAILABLE

    with _LOCK:

        _HTTP_REQUESTS = 0

        _HTTP_ERRORS = 0

        _LLM_CALLS = 0

        _LLM_ERRORS = 0

        _LLM_PROMPT_TOKENS = 0

        _LLM_COMPLETION_TOKENS = 0

        _LLM_TOTAL_TOKENS = 0

        _LLM_USAGE_UNAVAILABLE = 0

        _HTTP_ENDPOINTS.clear()

        _HTTP_STATUSES.clear()

        _HTTP_LATENCIES.clear()

        _LLM_LATENCIES.clear()

        _LLM_MODELS.clear()