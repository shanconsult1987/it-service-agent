import pytest

from app.agents import (
    HumanEscalationAgent,
    KnowledgeAgent,
    PolicyAgent,
    ResolutionAgent,
    TriageAgent
)
from app.orchestrator import ITServiceOrchestrator


pytestmark = pytest.mark.usefixtures("isolated_data")

RESOLUTION = "Use the approved enterprise troubleshooting procedure."
ESCALATION_REASON = "Policy requires human involvement."


def test_orchestrator_creates_all_agents():
    orchestrator = ITServiceOrchestrator()

    assert isinstance(orchestrator.triage, TriageAgent)
    assert isinstance(orchestrator.knowledge, KnowledgeAgent)
    assert isinstance(orchestrator.resolution, ResolutionAgent)
    assert isinstance(orchestrator.policy, PolicyAgent)
    assert isinstance(orchestrator.escalation, HumanEscalationAgent)


def test_unknown_incident_without_knowledge_is_escalated(isolated_data):
    result = ITServiceOrchestrator().process("INC-1", "Printer is on fire")

    assert result["triage"]["assigned_agent"] == "HumanEscalationAgent"
    assert result["resolution"]["confidence"] == 0.2
    assert result["policy"]["decision"] == "ESCALATE"
    assert result["escalation"]["status"] == "Escalated"
    assert "status" not in result
    state = isolated_data.state_data()
    assert state["incident_id"] == "INC-1"
    assert state["status"] == "Escalated"
    assert state["escalation_required"] is True
    assert ESCALATION_REASON in isolated_data.memory_text()


def test_high_priority_incident_waits_for_human_approval(isolated_data):
    result = ITServiceOrchestrator().process("INC-2", "VPN keeps disconnecting")

    assert result["triage"]["priority"] == "High"
    assert result["resolution"]["confidence"] == 0.9
    assert result["policy"]["decision"] == "HUMAN_APPROVAL"
    assert result["escalation"]["status"] == "Escalated"
    assert "status" not in result
    assert isolated_data.state_data()["status"] == "Escalated"


def test_medium_priority_incident_with_approved_knowledge_is_resolved(
    isolated_data,
):
    result = ITServiceOrchestrator().process("INC-3", "Laptop is slow")

    assert result["status"] == "Resolved"
    assert result["policy"]["decision"] == "RESOLVE"
    assert "escalation" not in result
    state = isolated_data.state_data()
    assert state["status"] == "Resolved"
    assert state["incident_id"] == "INC-3"
    assert state["resolution"] == RESOLUTION
    assert state["confidence"] == 0.9
    assert state["escalation_required"] is False
    assert state["last_action"] == "Automated resolution"
    assert (
        f"## Successful Resolutions\n- INC-3: {RESOLUTION}"
        in isolated_data.memory_text()
    )
