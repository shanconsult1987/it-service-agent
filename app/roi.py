import json

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

ROI_FILE = ROOT / "data" / "roi.json"


def calculate_roi():

    data = json.loads(
        ROI_FILE.read_text(
            encoding="utf-8"
        )
    )

    annual_incidents = (
        data["employees"]
        * data["incidents_per_employee_per_year"]
    )

    minutes_saved = (
        data["manual_minutes_per_incident"]
        -
        data["ai_minutes_per_incident"]
    )

    hours_saved = (
        annual_incidents
        * minutes_saved
        / 60
    )

    annual_benefit = (
        hours_saved
        * data["loaded_it_cost_per_hour"]
    )

    annual_cost = (

        data["annual_platform_cost"]

        +

        data["annual_implementation_cost"]

        +

        data["annual_operations_cost"]

    )

    net_benefit = (
        annual_benefit - annual_cost
    )

    return {

        "annual_incidents":
            annual_incidents,

        "hours_saved":
            round(hours_saved, 2),

        "annual_benefit":
            round(annual_benefit, 2),

        "annual_cost":
            round(annual_cost, 2),

        "net_benefit":
            round(net_benefit, 2),

        "roi_percent":
            round(
                net_benefit / annual_cost * 100,
                2
            ) if annual_cost else None,

        "assumption_note":
            "Calculated from editable planning assumptions; not measured production ROI."

    }