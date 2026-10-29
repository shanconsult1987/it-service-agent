import pytest

from app.agents import (
    HumanEscalationAgent,
    KnowledgeAgent,
    PolicyAgent,
    ResolutionAgent,
    TriageAgent
)


pytestmark = pytest.mark.usefixtures("isolated_data")


def test_triage_agent_classifies_and_records_triaged_state(isolated_data):
    result = TriageAgent().run("VPN keeps disconnecting")

    assert result == {
        "agent": "TriageAgent",
        "category": "Network",
        "priority": "High",
        "assigned_agent": "NetworkAgent",
    }
    state = isolated_data.state_data()
    assert state["status"] == "Triaged"
    assert state["category"] == "Network"
    assert state["priority"] == "High"
    assert state["assigned_agent"] == "NetworkAgent"


def test_knowledge_agent_returns_sections_for_category():
    result = KnowledgeAgent().run("VPN keeps disconnecting", "Network")

    assert result["agent"] == "KnowledgeAgent"
    assert "Restart the VPN client" in result["evidence"]
    assert "Reset passwords" not in result["evidence"]


def test_knowledge_agent_keeps_every_matching_section(isolated_data):
    isolated_data.knowledge.write_text(
        "# IT Support\n\n"
        "## Network VPN\nRestart the VPN client.\n\n"
        "## Identity\nReset passwords.\n\n"
        "## Network Wi-Fi\nForget and rejoin the network.\n",
        encoding="utf-8",
    )

    evidence = KnowledgeAgent().run("Wifi keeps dropping", "Network")["evidence"]

    assert "Restart the VPN client." in evidence
    assert "Forget and rejoin the network." in evidence
    assert "Reset passwords." not in evidence


def test_knowledge_agent_matches_category_case_insensitively():
    evidence = KnowledgeAgent().run("Laptop is slow", "ENDPOINT")["evidence"]

    assert "Restart the device" in evidence


def test_knowledge_agent_reports_when_no_section_matches():
    result = KnowledgeAgent().run("Printer is on fire", "Unknown")

    assert result["evidence"] == "No approved knowledge was found."


@pytest.mark.parametrize(
    "evidence", ["", None, "No approved knowledge was found."]
)
def test_resolution_agent_escalates_without_approved_evidence(evidence):
    assert ResolutionAgent().run("Printer is on fire", evidence) == {
        "agent": "ResolutionAgent",
        "resolution": "Escalate to a human.",
        "confidence": 0.2,
    }


def test_resolution_agent_resolves_with_approved_evidence():
    assert ResolutionAgent().run(
        "VPN keeps disconnecting", "## Network\nRestart the VPN client."
    ) == {
        "agent": "ResolutionAgent",
        "resolution": "Use the approved enterprise troubleshooting procedure.",
        "confidence": 0.9,
    }


@pytest.mark.parametrize(
    "priority, confidence, decision",
    [
        ("High", 0.2, "ESCALATE"),
        ("Medium", 0.69, "ESCALATE"),
        ("High", 0.9, "HUMAN_APPROVAL"),
        ("Medium", 0.7, "RESOLVE"),  # 0.7 itself is not below the threshold
        ("Low", 0.9, "RESOLVE"),
    ],
)
def test_policy_agent_decision(priority, confidence, decision):
    assert PolicyAgent().run(priority, confidence) == {
        "agent": "PolicyAgent",
        "decision": decision,
    }


def test_human_escalation_agent_records_escalation(isolated_data):
    result = HumanEscalationAgent().run("Policy requires human involvement.")

    assert result == {
        "agent": "HumanEscalationAgent",
        "status": "Escalated",
        "reason": "Policy requires human involvement.",
    }
    state = isolated_data.state_data()
    assert state["status"] == "Escalated"
    assert state["escalation_required"] is True
    assert state["last_action"] == "Human escalation"
    assert (
        "## Escalations\n- Policy requires human involvement."
        in isolated_data.memory_text()
    )
