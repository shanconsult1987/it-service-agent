import json
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from app import evaluation


@pytest.fixture
def evaluation_files(tmp_path, monkeypatch):
    cases_file = tmp_path / "evaluation.json"
    results_file = tmp_path / "reports" / "evaluation_results.json"
    monkeypatch.setattr(evaluation, "CASES_FILE", cases_file)
    monkeypatch.setattr(evaluation, "RESULTS_FILE", results_file)
    return cases_file, results_file


def write_specification(cases_file, cases):
    cases_file.write_text(
        json.dumps({"evaluation_version": "test-1.0", "cases": cases}),
        encoding="utf-8",
    )


def make_case(case_id="EV-001", description="VPN fails", category="Network"):
    return {
        "id": case_id,
        "description": description,
        "expected_category": category,
    }


def test_successful_evaluation_returns_and_persists_complete_report(
    evaluation_files, monkeypatch
):
    cases_file, results_file = evaluation_files
    write_specification(cases_file, [make_case(description="WiFi caf\u00e9 fails")])
    classifier = Mock(return_value={"category": "Network"})
    monkeypatch.setattr(evaluation, "classify_incident", classifier)
    before = datetime.now(evaluation.timezone.utc)

    report = evaluation.run_evaluation()

    after = datetime.now(evaluation.timezone.utc)
    created = datetime.fromisoformat(report["created_utc"])
    assert before <= created <= after
    assert created.utcoffset() == timedelta(0)
    assert report == {
        "evaluation_version": "test-1.0",
        "created_utc": report["created_utc"],
        "data_type": "synthetic_acceptance_tests",
        "total_cases": 1,
        "passed": 1,
        "failed": 0,
        "pass_rate": 1.0,
        "results": [{
            "id": "EV-001",
            "expected_category": "Network",
            "actual_category": "Network",
            "passed": True,
            "error": None,
        }],
    }
    classifier.assert_called_once_with("WiFi caf\u00e9 fails")
    assert json.loads(results_file.read_text(encoding="utf-8")) == report


@pytest.mark.parametrize("actual_category", ["Identity", "network", None])
def test_category_mismatch_is_a_failure(evaluation_files, monkeypatch, actual_category):
    cases_file, _ = evaluation_files
    write_specification(cases_file, [make_case()])
    monkeypatch.setattr(
        evaluation, "classify_incident", Mock(return_value={"category": actual_category})
    )

    report = evaluation.run_evaluation()

    assert report["total_cases"] == 1
    assert report["passed"] == 0
    assert report["failed"] == 1
    assert report["pass_rate"] == 0.0
    assert report["results"] == [{
        "id": "EV-001",
        "expected_category": "Network",
        "actual_category": actual_category,
        "passed": False,
        "error": None,
    }]


def test_missing_category_is_a_failure_without_classifier_error(
    evaluation_files, monkeypatch
):
    cases_file, _ = evaluation_files
    write_specification(cases_file, [make_case()])
    monkeypatch.setattr(evaluation, "classify_incident", Mock(return_value={}))

    report = evaluation.run_evaluation()

    assert report["failed"] == 1
    assert report["results"][0]["actual_category"] is None
    assert report["results"][0]["passed"] is False
    assert report["results"][0]["error"] is None


def test_classifier_error_is_recorded_and_remaining_cases_are_evaluated(
    evaluation_files, monkeypatch
):
    cases_file, _ = evaluation_files
    write_specification(cases_file, [
        make_case("EV-001", "Broken input"),
        make_case("EV-002", "Password reset", "Identity"),
        make_case("EV-003", "VPN fails"),
    ])
    classifier = Mock(side_effect=[
        RuntimeError("Classifier unavailable"),
        {"category": "Identity"},
        {"category": "Unknown"},
    ])
    monkeypatch.setattr(evaluation, "classify_incident", classifier)

    report = evaluation.run_evaluation()

    assert report["total_cases"] == 3
    assert report["passed"] == 1
    assert report["failed"] == 2
    assert report["pass_rate"] == pytest.approx(1 / 3)
    assert report["results"][0] == {
        "id": "EV-001",
        "expected_category": "Network",
        "actual_category": None,
        "passed": False,
        "error": "Classifier unavailable",
    }
    assert [item["id"] for item in report["results"]] == [
        "EV-001", "EV-002", "EV-003",
    ]
    assert [item["passed"] for item in report["results"]] == [False, True, False]
    assert [call.args for call in classifier.call_args_list] == [
        ("Broken input",), ("Password reset",), ("VPN fails",),
    ]


def test_empty_cases_have_no_pass_rate(evaluation_files, monkeypatch):
    cases_file, results_file = evaluation_files
    write_specification(cases_file, [])
    classifier = Mock()
    monkeypatch.setattr(evaluation, "classify_incident", classifier)

    report = evaluation.run_evaluation()

    assert report["total_cases"] == 0
    assert report["passed"] == 0
    assert report["failed"] == 0
    assert report["pass_rate"] is None
    assert report["results"] == []
    classifier.assert_not_called()
    assert json.loads(results_file.read_text(encoding="utf-8")) == report


def test_existing_report_is_replaced(evaluation_files, monkeypatch):
    cases_file, results_file = evaluation_files
    write_specification(cases_file, [])
    results_file.parent.mkdir()
    results_file.write_text('{"stale": true}', encoding="utf-8")
    monkeypatch.setattr(evaluation, "classify_incident", Mock())

    report = evaluation.run_evaluation()

    assert json.loads(results_file.read_text(encoding="utf-8")) == report


def test_missing_specification_raises_file_not_found(evaluation_files):
    _, results_file = evaluation_files

    with pytest.raises(FileNotFoundError):
        evaluation.run_evaluation()

    assert not results_file.exists()


def test_invalid_specification_json_raises_decode_error(evaluation_files):
    cases_file, results_file = evaluation_files
    cases_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        evaluation.run_evaluation()

    assert not results_file.exists()


def test_report_write_error_is_propagated(evaluation_files):
    cases_file, results_file = evaluation_files
    write_specification(cases_file, [])
    results_file.parent.write_text("not a directory", encoding="utf-8")

    with pytest.raises(FileExistsError):
        evaluation.run_evaluation()