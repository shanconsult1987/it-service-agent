import json

import pytest

from app.dashboard import calculate_roi, load_json, responsible_ai_summary


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_load_json_accepts_utf8_with_or_without_bom(tmp_path, encoding):
    path = tmp_path / "data.json"
    path.write_text('{"controls": []}', encoding=encoding)

    assert load_json(path) == {"controls": []}


@pytest.mark.parametrize("text", ["", " \n\t", "\ufeff"])
def test_load_json_reports_empty_file(tmp_path, text):
    path = tmp_path / "empty.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="is empty") as error:
        load_json(path)

    assert str(path) in str(error.value)


@pytest.mark.parametrize("text", ["<html>Error</html>", '{"controls":\n}'])
def test_load_json_reports_invalid_file_and_location(tmp_path, text):
    path = tmp_path / "invalid.json"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON") as error:
        load_json(path)

    assert str(path) in str(error.value)
    cause = error.value.__cause__
    assert isinstance(cause, json.JSONDecodeError)
    assert f"line {cause.lineno}, column {cause.colno}" in str(error.value)


def test_load_json_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_json(tmp_path / "missing.json")


def test_calculate_roi_with_project_data():
    assert calculate_roi() == {
        "annual_incidents": 20000,
        "hours_saved": 4000.0,
        "annual_benefit": 200000.0,
        "annual_cost": 120000,
        "net_benefit": 80000.0,
        "roi_percent": 66.67,
    }


def test_responsible_ai_summary_with_project_data():
    summary = responsible_ai_summary()

    assert summary["passed"] == 8
    assert summary["total"] == 8
    assert summary["score_percent"] == 100.0
    assert len(summary["controls"]) == 8
