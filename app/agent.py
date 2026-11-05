import os

import time

from pathlib import Path

from app.state import update_state

from app.memory import append_memory

from app.monitoring import record_llm_call

from app.audit import record_event


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
        "knowledge_available": bool(
            load_knowledge()
        )
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
            "Use approved enterprise knowledge "
            "and escalate when uncertain."
        )

        result["token_usage"] = {

            "prompt_tokens": 0,

            "completion_tokens": 0,

            "total_tokens": 0,

            "latency_ms": 0

        }

        record_event(
            "llm_skipped",
            outcome="deterministic_no_api_key"
        )

        return result

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5"
    )

    from openai import OpenAI

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
Category
Priority
Recommended resolution
Reason
Confidence

Rules:
Do not invent procedures.
Do not expose confidential information.
Do not bypass security controls.
If knowledge is insufficient, recommend escalation.
Do not perform privileged actions.
"""

    start = time.perf_counter()

    try:

        response = client.responses.create(
            model=model,
            input=prompt
        )

        latency_ms = round(
            (
                time.perf_counter() - start
            ) * 1000,
            2
        )

        usage = getattr(
            response,
            "usage",
            None
        )

        prompt_tokens = (
            getattr(
                usage,
                "input_tokens",
                None
            )
            if usage else None
        )

        completion_tokens = (
            getattr(
                usage,
                "output_tokens",
                None
            )
            if usage else None
        )

        total_tokens = (
            getattr(
                usage,
                "total_tokens",
                None
            )
            if usage else None
        )

        record_llm_call(
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            latency_ms,
            error=False
        )

        answer = response.output_text

    except Exception as exc:

        latency_ms = round(
            (
                time.perf_counter() - start
            ) * 1000,
            2
        )

        record_llm_call(
            model,
            latency_ms=latency_ms,
            error=True
        )

        record_event(
            "llm_call",
            outcome="error",
            details={
                "model": model,
                "error_type": type(exc).__name__
            }
        )

        raise

    token_usage = {

        "prompt_tokens": prompt_tokens,

        "completion_tokens": completion_tokens,

        "total_tokens": total_tokens,

        "latency_ms": latency_ms

    }

    update_state(
        status="Resolved",
        resolution=answer,
        last_action="Generate resolution",
        token_usage=token_usage
    )

    append_memory(
        "Successful Resolutions",
        f"- {description}: {answer}"
    )

    record_event(
        "llm_call",
        outcome="success",
        details={
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms
        }
    )

    return {
        "mode": "llm",
        "answer": answer,
        "token_usage": token_usage
    }