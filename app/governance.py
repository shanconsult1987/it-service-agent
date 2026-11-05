import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GOVERNANCE_FILE = ROOT / "data" / "governance.json"

RAI_FILE = ROOT / "data" / "responsible_ai.json"


def _read(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def governance_summary():

    data = _read(GOVERNANCE_FILE)

    controls = data.get("controls", [])

    passed = sum(
        control.get("status") == "Pass"
        for control in controls
    )

    return {
        "framework": data.get(
            "framework",
            "Day 3 Agent Governance"
        ),
        "owner": data.get(
            "owner",
            "AI Architecture"
        ),
        "total": len(controls),
        "passed": passed,
        "open": len(controls) - passed,
        "controls": controls
    }


def responsible_ai_summary():

    data = _read(RAI_FILE)

    controls = data.get("controls", [])

    passed = sum(
        control.get("status") == "Pass"
        for control in controls
    )

    return {
        "passed": passed,
        "total": len(controls),
        "score_percent": round(
            passed / len(controls) * 100,
            2
        ) if controls else 0,
        "controls": controls
    }