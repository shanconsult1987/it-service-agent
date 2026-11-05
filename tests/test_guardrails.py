import json

import pytest

from app import guardrails
from app.guardrails import (
    check_input,
    check_resolution_policy,
    enforce_request_policy,
    validate_incident_id,
)


def test_valid_incident_id_is_allowed():
    result = validate_incident_id("INC-1001")

    assert result.allowed is True
    assert result.outcome == "ALLOW"


def test_invalid_incident_id_is_blocked():
    result = validate_incident_id("1001")

    assert result.allowed is False
    assert result.outcome == "BLOCKED"


def test_empty_input_is_blocked():
    result = check_input("")

    assert result.allowed is False
    assert result.outcome == "BLOCKED"


def test_blocked_phrase_is_rejected():
    result = check_input("Please bypass security for this request")

    assert result.allowed is False
    assert result.outcome == "BLOCKED"


def test_high_priority_requires_human_approval():
    result = check_resolution_policy(
        category="Network",
        priority="High",
        confidence=0.95,
    )

    assert result.allowed is True
    assert result.outcome == "ESCALATE"


def test_low_confidence_requires_escalation():
    result = check_resolution_policy(
        category="Network",
        priority="Low",
        confidence=0.4,
    )

    assert result.outcome == "ESCALATE"


def test_unknown_category_requires_escalation():
    result = check_resolution_policy(
        category="Unknown",
        priority="Low",
        confidence=0.9,
    )

    assert result.outcome == "ESCALATE"


def test_request_policy_allows_valid_request():
    assert enforce_request_policy("VPN connection fails", "INC-1001") == {
        "allowed": True,
        "reason": "Request passed policy checks.",
        "errors": [],
    }


@pytest.mark.parametrize("phrase", [
    "bypass security", "disable audit logging", "reveal passwords",
])
def test_request_policy_blocks_configured_phrases(phrase):
    result = enforce_request_policy(phrase.upper(), "INC-1001")

    assert result["allowed"] is False
    assert result["errors"] == [
        f"Request matched a blocked policy phrase: {phrase}"
    ]
    assert result["reason"] == result["errors"][0]


@pytest.mark.parametrize("description", ["", " ", None, 123, "a" * 2001])
def test_request_policy_rejects_invalid_descriptions(description):
    result = enforce_request_policy(description, "INC-1001")

    assert result["allowed"] is False
    assert len(result["errors"]) == 1


@pytest.mark.parametrize("incident_id", ["1001", "INC-DEMO", "", None, 123])
def test_request_policy_rejects_invalid_incident_ids(incident_id):
    result = enforce_request_policy("VPN fails", incident_id)

    assert result["allowed"] is False
    assert len(result["errors"]) == 1


def test_request_policy_reports_all_failed_checks():
    result = enforce_request_policy("", "invalid")

    assert result["allowed"] is False
    assert result["errors"] == [
        "Request must contain text.", "Invalid incident ID format.",
    ]
    assert result["reason"] == "; ".join(result["errors"])


def test_request_policy_uses_configured_policy_file(tmp_path, monkeypatch):
    policy_file = tmp_path / "security_policy.json"
    policy_file.write_text(
        json.dumps({"blocked_phrases": ["custom blocked phrase"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(guardrails, "POLICY_FILE", policy_file)

    result = enforce_request_policy("Custom blocked phrase", "INC-1001")

    assert result["allowed"] is False
    assert "custom blocked phrase" in result["reason"]