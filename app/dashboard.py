
"""Executive dashboard data assembled from existing Day 2 files
and Day 3 runtime observations.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROI_FILE = ROOT / "data" / "roi.json"
RAI_FILE = ROOT / "data" / "responsible_ai.json"
STATE_FILE = ROOT / "data" / "agent_state.json"


def load_json(path):
    path = Path(path)
    content = path.read_text(encoding="utf-8-sig")

    if not content.strip():
        raise ValueError(f"JSON file '{path}' is empty.")

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in '{path}' at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error


def calculate_roi():
    """Calculate an estimate from configured ROI assumptions."""
    data = load_json(ROI_FILE)

    annual_incidents = (
        data["employees"]
        * data["incidents_per_employee_per_year"]
    )

    minutes_saved = (
        data["manual_minutes_per_incident"]
        - data["ai_minutes_per_incident"]
    )

    hours_saved = annual_incidents * minutes_saved / 60

    annual_benefit = (
        hours_saved * data["loaded_it_cost_per_hour"]
    )

    annual_cost = (
        data["annual_platform_cost"]
        + data["annual_implementation_cost"]
        + data["annual_operations_cost"]
    )

    net_benefit = annual_benefit - annual_cost

    roi_percent = (
        net_benefit / annual_cost * 100
        if annual_cost else None
    )

    return {
        "annual_incidents": annual_incidents,
        "hours_saved": round(hours_saved, 2),
        "annual_benefit": round(annual_benefit, 2),
        "annual_cost": round(annual_cost, 2),
        "net_benefit": round(net_benefit, 2),
        "roi_percent": (
            round(roi_percent, 2)
            if roi_percent is not None else None
        ),
        "assumptions": data,
        "basis": (
            "Calculated from data/roi.json. These are configured "
            "assumptions, not measured production savings."
        )
    }


def responsible_ai_summary():
    data = load_json(RAI_FILE)
    controls = data.get("controls", [])

    passed = sum(
        1 for control in controls
        if control.get("status") == "Pass"
    )
    in_review = sum(
        1 for control in controls
        if control.get("status") == "In review"
    )
    failed = sum(
        1 for control in controls
        if control.get("status") == "Fail"
    )
    needs_evidence = sum(
        1 for control in controls
        if control.get("status") == "Needs evidence"
    )

    return {
        "register_type": data.get("register_type", "unspecified"),
        "total": len(controls),
        "passed": passed,
        "in_review": in_review,
        "failed": failed,
        "needs_evidence": needs_evidence,
        "controls": controls,
        "interpretation": (
            "Register status is self-declared. A Pass status must "
            "be backed by reviewed evidence; this dashboard does "
            "not independently certify compliance."
        )
    }


def latest_agent_state():
    state = load_json(STATE_FILE)

    keys = [
        "incident_id",
        "status",
        "category",
        "priority",
        "assigned_agent",
        "confidence",
        "escalation_required",
        "last_action"
    ]

    return {key: state.get(key) for key in keys}


def executive_dashboard():
    """Return the current data payload for the executive page."""
    from app.audit import audit_summary
    from app.evaluation import run_evaluation
    from app.monitoring import snapshot

    runtime = snapshot()
    rai = responsible_ai_summary()
    audit = audit_summary()
    evaluation = run_evaluation()

    guardrail_events = [
        event for event in audit["latest_events"]
        if event.get("event_type") in (
            "guardrail_rejection",
            "request_rejected"
        )
    ]

    escalation_events = [
        event for event in audit["latest_events"]
        if event.get("event_type") == "incident_escalation"
    ]

    return {
        "service": "Contoso IT Service Agent",
        "scope": (
            "Local workshop demonstration. Runtime metrics are "
            "process-local; audit summaries read local JSONL."
        ),
        "generated_at_source": "server response time",
        "runtime": runtime,
        "readiness": {
            "scope": "local file readiness is reported by /ready",
            "endpoint": "/ready"
        },
        "guardrails": {
            "description_max_characters": 2000,
            "incident_id_max_characters": 80,
            "recent_rejection_events": len(guardrail_events),
            "recent_escalation_events": len(escalation_events),
            "recent_rejections": guardrail_events,
            "recent_escalations": escalation_events,
            "interpretation": (
                "Counts cover only events in the recent audit "
                "window, not all-time totals."
            )
        },
        "audit": audit,
        "evaluation": evaluation,
        "responsible_ai": rai,
        "roi": calculate_roi(),
        "latest_state": latest_agent_state(),
        "rai_toolbox": {
            "repository": (
                "https://github.com/microsoft/"
                "responsible-ai-toolbox"
            ),
            "availability": (
                "Optional separate model/data assessment. "
                "Requires compatible model and evaluation artefacts."
            )
        }
    }
