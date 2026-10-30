
"""Repeatable acceptance evaluation for Day 2 incident rules.

These are authored acceptance fixtures, not training data,
production records or a measure of general model accuracy.
"""
import json
from pathlib import Path

from app.agent import classify_incident, load_knowledge

ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "data" / "evaluation_cases.json"


def evaluate_case(case):
    triage = classify_incident(case["description"])
    knowledge = load_knowledge()

    matching_sections = [
        section
        for section in knowledge.split("\n## ")
        if triage["category"].lower() in section.lower()
    ]

    evidence_found = (
        bool(matching_sections)
        and triage["category"] != "Unknown"
    )

    confidence = 0.9 if evidence_found else 0.2

    if confidence < 0.7:
        policy = "ESCALATE"
    elif triage["priority"] == "High":
        policy = "HUMAN_APPROVAL"
    else:
        policy = "RESOLVE"

    checks = {
        "category_matches": (
            triage["category"] == case["expected_category"]
        ),
        "priority_matches": (
            triage["priority"] == case["expected_priority"]
        ),
        "policy_matches": (
            policy == case["expected_policy"]
        )
    }

    return {
        "id": case["id"],
        "description": case["description"],
        "expected": {
            "category": case["expected_category"],
            "priority": case["expected_priority"],
            "policy": case["expected_policy"]
        },
        "observed": {
            "category": triage["category"],
            "priority": triage["priority"],
            "policy": policy
        },
        "checks": checks,
        "passed": all(checks.values())
    }


def run_evaluation():
    cases = json.loads(
        CASES_FILE.read_text(encoding="utf-8")
    )

    results = [evaluate_case(case) for case in cases]
    passed = sum(1 for result in results if result["passed"])
    total = len(results)

    return {
        "source": "data/evaluation_cases.json",
        "data_kind": "authored_acceptance_cases_not_training_data",
        "passed": passed,
        "total": total,
        "score_percent": (
            round(passed / total * 100, 2)
            if total else None
        ),
        "results": results
    }


if __name__ == "__main__":
    report = run_evaluation()
    print(json.dumps(report, indent=2))
    raise SystemExit(
        0 if report["passed"] == report["total"] else 1
    )
