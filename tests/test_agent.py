from unittest.mock import MagicMock

import pytest

import app.agent as agent
from app.agent import (
    classify_incident,
    generate_resolution,
    investigate,
    load_knowledge
)


pytestmark = pytest.mark.usefixtures("isolated_data")

NO_KEY_ANSWER = (
    "LLM is not configured. "
    "Use approved enterprise knowledge and escalate when uncertain."
)

LLM_ANSWER = (
    "Category: Network\n"
    "Priority: High\n"
    "Recommended resolution: Restart the VPN client and reconnect.\n"
    "Reason: Approved knowledge covers VPN drops.\n"
    "Confidence: 0.9"
)


@pytest.fixture
def fake_openai(monkeypatch):
    client = MagicMock()
    client.responses.create.return_value.output_text = LLM_ANSWER
    openai_class = MagicMock(return_value=client)
    monkeypatch.setattr(agent, "OpenAI", openai_class)
    return openai_class, client


@pytest.mark.parametrize(
    "description, category, priority, assigned_agent",
    [
        ("VPN keeps disconnecting", "Network", "High", "NetworkAgent"),
        ("Wifi drops every hour", "Network", "High", "NetworkAgent"),
        ("Forgot my password", "Identity", "Medium", "IdentityAgent"),
        ("Cannot login to email", "Identity", "Medium", "IdentityAgent"),
        ("Laptop is slow", "Endpoint", "Medium", "EndpointAgent"),
        ("High CPU usage", "Endpoint", "Medium", "EndpointAgent"),
        ("Printer is on fire", "Unknown", "Low", "HumanEscalationAgent"),
    ],
)
def test_classify_incident_maps_keywords_to_category(
    description, category, priority, assigned_agent
):
    assert classify_incident(description) == {
        "category": category,
        "priority": priority,
        "agent": assigned_agent,
    }


def test_classify_incident_checks_network_before_other_categories():
    assert classify_incident("VPN login is slow")["category"] == "Network"


def test_load_knowledge_returns_file_contents(isolated_data):
    isolated_data.knowledge.write_text(
        "## Network\nRestart the VPN.\n", encoding="utf-8"
    )

    assert load_knowledge() == "## Network\nRestart the VPN.\n"


def test_investigate_classifies_incident_and_records_state(isolated_data):
    result = investigate("VPN keeps disconnecting")

    assert result == {
        "description": "VPN keeps disconnecting",
        "category": "Network",
        "priority": "High",
        "agent": "NetworkAgent",
        "knowledge_available": True,
    }
    state = isolated_data.state_data()
    assert state["status"] == "Investigating"
    assert state["category"] == "Network"
    assert state["priority"] == "High"
    assert state["assigned_agent"] == "NetworkAgent"


def test_investigate_reports_empty_knowledge(isolated_data):
    isolated_data.knowledge.write_text("", encoding="utf-8")

    assert investigate("Laptop is slow")["knowledge_available"] is False


def test_generate_resolution_without_api_key_uses_deterministic_mode(
    monkeypatch, isolated_data, fake_openai
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    openai_class, _ = fake_openai

    result = generate_resolution("VPN keeps disconnecting")

    assert result["mode"] == "deterministic"
    assert result["category"] == "Network"
    assert result["answer"] == NO_KEY_ANSWER
    assert isolated_data.state_data()["status"] == "Investigating"
    openai_class.assert_not_called()


def test_generate_resolution_treats_blank_api_key_as_missing(
    monkeypatch, fake_openai
):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    openai_class, _ = fake_openai

    assert generate_resolution("Laptop is slow")["mode"] == "deterministic"
    openai_class.assert_not_called()


def test_generate_resolution_with_api_key_calls_llm_and_records_answer(
    monkeypatch, isolated_data, fake_openai
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    openai_class, client = fake_openai

    result = generate_resolution("VPN keeps disconnecting")

    assert result == {"mode": "llm", "answer": LLM_ANSWER}
    openai_class.assert_called_once_with(api_key="test-key")
    request = client.responses.create.call_args.kwargs
    assert request["model"] == "gpt-5"
    assert "Restart the VPN client" in request["input"]
    assert "VPN keeps disconnecting" in request["input"]
    state = isolated_data.state_data()
    assert state["status"] == "Resolved"
    assert state["resolution"] == LLM_ANSWER
    assert f"- VPN keeps disconnecting: {LLM_ANSWER}" in isolated_data.memory_text()


def test_generate_resolution_uses_model_from_environment(
    monkeypatch, fake_openai
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    _, client = fake_openai

    generate_resolution("VPN keeps disconnecting")

    assert client.responses.create.call_args.kwargs["model"] == "gpt-test"
