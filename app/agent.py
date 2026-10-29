import os
from pathlib import Path

from openai import OpenAI

from app.state import update_state
from app.memory import append_memory


ROOT = Path(__file__).resolve().parent.parent

KNOWLEDGE_FILE = (
    ROOT
    / "knowledge"
    / "it-support.md"
)


def load_knowledge():

    return KNOWLEDGE_FILE.read_text(
        encoding="utf-8"
    )


def classify_incident(description):

    text = description.lower()

    if any(
        word in text
        for word in [
            "vpn",
            "network",
            "wifi"
        ]
    ):

        return {
            "category": "Network",
            "priority": "High",
            "agent": "NetworkAgent"
        }

    if any(
        word in text
        for word in [
            "password",
            "login",
            "account"
        ]
    ):

        return {
            "category": "Identity",
            "priority": "Medium",
            "agent": "IdentityAgent"
        }

    if any(
        word in text
        for word in [
            "slow",
            "performance",
            "cpu"
        ]
    ):

        return {
            "category": "Endpoint",
            "priority": "Medium",
            "agent": "EndpointAgent"
        }

    return {
        "category": "Unknown",
        "priority": "Low",
        "agent": "HumanEscalationAgent"
    }


def investigate(description):

    result = classify_incident(
        description
    )

    update_state(
        category=result["category"],
        priority=result["priority"],
        assigned_agent=result["agent"],
        status="Investigating"
    )

    return {
        "description": description,
        **result,
        "knowledge_available":
            bool(load_knowledge())
    }


def generate_resolution(description):

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:

        result = investigate(
            description
        )

        result["mode"] = "deterministic"

        result["answer"] = (
            "LLM is not configured. "
            "Use approved enterprise "
            "knowledge and escalate "
            "when uncertain."
        )

        return result

    client = OpenAI(
        api_key=api_key
    )

    knowledge = load_knowledge()

    prompt = f"""
You are an enterprise IT service agent.

Use ONLY the approved knowledge.

APPROVED KNOWLEDGE:
{knowledge}

INCIDENT:
{description}

Return:

Category:
Priority:
Recommended resolution:
Reason:
Confidence:

Rules:

1. Do not invent procedures.
2. Do not expose confidential information.
3. Do not bypass security controls.
4. If knowledge is insufficient,
   recommend escalation.
5. Do not perform privileged actions.
"""

    response = client.responses.create(
        model=os.getenv(
            "OPENAI_MODEL",
            "gpt-5"
        ),
        input=prompt
    )

    answer = response.output_text

    update_state(
        status="Resolved",
        resolution=answer,
        last_action="Generate resolution"
    )

    append_memory(
        "Successful Resolutions",
        f"- {description}: {answer}"
    )

    return {
        "mode": "llm",
        "answer": answer
    }