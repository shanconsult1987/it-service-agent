import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agent import classify_incident


ROOT = Path(__file__).resolve().parent.parent
CASES_FILE = ROOT / "data" / "evaluation.json"
RESULTS_FILE = ROOT / "data" / "evaluation_results.json"


def run_evaluation() -> dict[str, Any]:
    with CASES_FILE.open("r", encoding="utf-8") as file:
        specification = json.load(file)

    results = []

    for case in specification["cases"]:
        try:
            actual = classify_incident(case["description"])
            actual_category = actual.get("category")

            passed = actual_category == case["expected_category"]

            results.append({
                "id": case["id"],
                "expected_category": case["expected_category"],
                "actual_category": actual_category,
                "passed": passed,
                "error": None,
            })

        except Exception as exc:
            results.append({
                "id": case["id"],
                "expected_category": case["expected_category"],
                "actual_category": None,
                "passed": False,
                "error": str(exc),
            })

    total = len(results)
    passed_count = sum(item["passed"] for item in results)

    report = {
        "evaluation_version": specification["evaluation_version"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "data_type": "synthetic_acceptance_tests",
        "total_cases": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "pass_rate": passed_count / total if total else None,
        "results": results,
    }

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with RESULTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return report


if __name__ == "__main__":
    report = run_evaluation()

    print(json.dumps({
        "total_cases": report["total_cases"],
        "passed": report["passed"],
        "failed": report["failed"],
        "pass_rate": report["pass_rate"],
        "results_file": str(RESULTS_FILE),
    }, indent=2))

    if report["failed"] > 0:
        raise SystemExit(1)