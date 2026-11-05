import json

from pathlib import Path

from app.monitoring import snapshot


ROOT = Path(__file__).resolve().parent.parent

PRICING_FILE = (
    ROOT
    / "data"
    / "model_pricing.json"
)


def calculate_llm_cost():

    pricing = json.loads(
        PRICING_FILE.read_text(
            encoding="utf-8"
        )
    )

    usage = snapshot()["llm"]

    input_rate = pricing.get(
        "input_cost_per_1m_tokens"
    )

    output_rate = pricing.get(
        "output_cost_per_1m_tokens"
    )

    configured = (
        input_rate is not None
        and output_rate is not None
    )

    cost = None

    if configured:

        cost = (

            usage["prompt_tokens"]
            / 1_000_000
            * float(input_rate)

            +

            usage["completion_tokens"]
            / 1_000_000
            * float(output_rate)

        )

    return {

        "currency":
            pricing.get("currency", "USD"),

        "model":
            pricing.get("model", "unknown"),

        "pricing_configured":
            configured,

        "estimated_cost":
            round(cost, 6)
            if cost is not None
            else None,

        "prompt_tokens":
            usage["prompt_tokens"],

        "completion_tokens":
            usage["completion_tokens"],

        "total_tokens":
            usage["total_tokens"],

        "usage_unavailable_calls":
            usage["usage_unavailable"]

    }