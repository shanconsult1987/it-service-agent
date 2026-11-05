import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
POLICY_FILE = ROOT / "data" / "security_policy.json"


@dataclass
class GuardrailResult:
    allowed: bool
    outcome: str
    reason: str


def load_policy() -> dict[str, Any]:
    with POLICY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_incident_id(incident_id: str) -> GuardrailResult:
    if not isinstance(incident_id, str):
        return GuardrailResult(
            False, "BLOCKED", "Incident ID must be text."
        )

    if not re.fullmatch(r"INC-[0-9]{4,8}", incident_id):
        return GuardrailResult(
            False, "BLOCKED", "Invalid incident ID format."
        )

    return GuardrailResult(True, "ALLOW", "Incident ID is valid.")


def check_input(text: str) -> GuardrailResult:
    if not isinstance(text, str) or not text.strip():
        return GuardrailResult(
            False, "BLOCKED", "Request must contain text."
        )

    if len(text) > 2000:
        return GuardrailResult(
            False, "BLOCKED", "Request exceeds the length limit."
        )

    policy = load_policy()
    normalized = text.casefold()

    for phrase in policy["blocked_phrases"]:
        if phrase.casefold() in normalized:
            return GuardrailResult(
                False,
                "BLOCKED",
                f"Request matched a blocked policy phrase: {phrase}",
            )

    return GuardrailResult(True, "ALLOW", "Input passed policy checks.")


def check_resolution_policy(
    category: str,
    priority: str,
    confidence: float,
) -> GuardrailResult:
    policy = load_policy()

    if category == "Unknown":
        return GuardrailResult(
            True,
            policy["unknown_category_action"],
            "The issue could not be classified reliably.",
        )

    if confidence < policy["minimum_confidence"]:
        return GuardrailResult(
            True, "ESCALATE", "Confidence is below the policy threshold."
        )

    if priority in policy["human_approval_required_for"]:
        return GuardrailResult(
            True, "ESCALATE", "Human approval is required for this priority."
        )

    return GuardrailResult(
        True, "ALLOW", "Resolution passed the configured policy checks."
    )


def enforce_request_policy(description: str, incident_id: str) -> dict[str, Any]:
    checks = [
        check_input(description),
        validate_incident_id(incident_id),
    ]
    errors = [check.reason for check in checks if not check.allowed]
    return {
        "allowed": not errors,
        "reason": "; ".join(errors) if errors else "Request passed policy checks.",
        "errors": errors,
    }