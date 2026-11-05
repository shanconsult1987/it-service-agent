import json

from app.monitoring import snapshot

from app.governance import (
    governance_summary,
    responsible_ai_summary
)

from app.evaluation import RESULTS_FILE

from app.costing import calculate_llm_cost

from app.roi import calculate_roi

from app.audit import read_events


def dashboard_snapshot():

    try:

        evaluation = json.loads(
            RESULTS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError
    ):

        evaluation = {

            "case_count": 0,

            "passed": 0,

            "failed": 0,

            "pass_rate_percent": 0,

            "results": []

        }

    return {

        "runtime":
            snapshot(),

        "governance":
            governance_summary(),

        "responsible_ai":
            responsible_ai_summary(),

        "evaluation":
            evaluation,

        "cost":
            calculate_llm_cost(),

        "roi":
            calculate_roi(),

        "audit":
            read_events(30)

    }