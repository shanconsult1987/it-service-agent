import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

ROI_FILE = ROOT / "data" / "roi.json"
RAI_FILE = (
    ROOT
    / "data"
    / "responsible_ai.json"
)


def load_json(path):

    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")

    if not text.strip():
        raise ValueError(
            f"JSON file '{path}' is empty. "
            "Restore valid JSON before loading the dashboard."
        )

    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in '{path}' at line {error.lineno}, "
            f"column {error.colno}: {error.msg}."
        ) from error


def calculate_roi():

    data = load_json(
        ROI_FILE
    )

    annual_incidents = (
        data["employees"]
        * data[
            "incidents_per_employee_per_year"
        ]
    )

    minutes_saved = (
        data["manual_minutes_per_incident"]
        - data["ai_minutes_per_incident"]
    )

    hours_saved = (
        annual_incidents
        * minutes_saved
        / 60
    )

    annual_benefit = (
        hours_saved
        * data[
            "loaded_it_cost_per_hour"
        ]
    )

    annual_cost = (
        data["annual_platform_cost"]
        + data["annual_implementation_cost"]
        + data["annual_operations_cost"]
    )

    net_benefit = (
        annual_benefit
        - annual_cost
    )

    roi_percent = (
        net_benefit
        / annual_cost
        * 100
        if annual_cost
        else 0
    )

    return {
        "annual_incidents":
            annual_incidents,

        "hours_saved":
            round(hours_saved, 2),

        "annual_benefit":
            round(
                annual_benefit,
                2
            ),

        "annual_cost":
            round(
                annual_cost,
                2
            ),

        "net_benefit":
            round(
                net_benefit,
                2
            ),

        "roi_percent":
            round(
                roi_percent,
                2
            )
    }

def responsible_ai_summary():

    data = load_json(
        RAI_FILE
    )

    controls = data["controls"]

    passed = sum(
        1
        for control in controls
        if control["status"] == "Pass"
    )

    total = len(controls)

    score = (
        passed / total * 100
        if total
        else 0
    )

    return {
        "passed": passed,
        "total": total,
        "score_percent":
            round(score, 2),
        "controls": controls
    }