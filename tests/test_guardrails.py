
from app.guardrails import (
    validate_incident_description,
    validate_incident_id
)
from app.orchestrator import ITServiceOrchestrator


def test_normal_incident_is_accepted():
    result = validate_incident_description(
        "VPN keeps disconnecting"
    )
    assert result["allowed"] is True
    assert result["description"] == "VPN keeps disconnecting"


def test_empty_description_is_rejected():
    result = validate_incident_description("   ")
    assert result["allowed"] is False
    assert result["code"] == "EMPTY_DESCRIPTION"


def test_non_text_description_is_rejected():
    result = validate_incident_description(None)
    assert result["allowed"] is False
    assert result["code"] == "INVALID_DESCRIPTION_TYPE"


def test_oversized_description_is_rejected():
    result = validate_incident_description("x" * 2001)
    assert result["allowed"] is False
    assert result["code"] == "DESCRIPTION_TOO_LONG"


def test_invalid_incident_id_is_rejected():
    result = validate_incident_id("../private")
    assert result["allowed"] is False


def test_orchestrator_rejects_empty_description():
    result = ITServiceOrchestrator().process(
        "INC-GUARD-01",
        "   ",
        correlation_id="TEST-GUARD-001"
    )
    assert result["status"] == "Rejected"
    assert result["guardrail"]["allowed"] is False
