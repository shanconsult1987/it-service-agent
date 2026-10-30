
from app.evaluation import run_evaluation


def test_authored_acceptance_cases_pass():
    report = run_evaluation()

    assert report["data_kind"] == (
        "authored_acceptance_cases_not_training_data"
    )
    assert report["total"] == 4
    assert report["passed"] == report["total"]


def test_every_case_has_explicit_checks():
    report = run_evaluation()

    for case in report["results"]:
        assert set(case["checks"]) == {
            "category_matches",
            "priority_matches",
            "policy_matches"
        }
        assert case["passed"] is True
