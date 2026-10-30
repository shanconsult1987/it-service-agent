
"""Input guardrails shared by HTTP and orchestration entry points."""

MAX_DESCRIPTION_LENGTH = 2000
MAX_INCIDENT_ID_LENGTH = 80


def validate_incident_description(description):
    """Validate user-controlled incident text before processing."""
    if not isinstance(description, str):
        return {
            "allowed": False,
            "code": "INVALID_DESCRIPTION_TYPE",
            "reason": "Description must be text."
        }

    cleaned = description.strip()

    if not cleaned:
        return {
            "allowed": False,
            "code": "EMPTY_DESCRIPTION",
            "reason": "Incident description is required."
        }

    if len(cleaned) > MAX_DESCRIPTION_LENGTH:
        return {
            "allowed": False,
            "code": "DESCRIPTION_TOO_LONG",
            "reason": (
                "Incident description exceeds "
                f"{MAX_DESCRIPTION_LENGTH} characters."
            )
        }

    return {
        "allowed": True,
        "code": "INPUT_ACCEPTED",
        "description": cleaned,
        "reason": "Input passed basic validation."
    }


def validate_incident_id(incident_id):
    """Allow simple incident identifiers, not arbitrary payload strings."""
    if not isinstance(incident_id, str):
        return {
            "allowed": False,
            "code": "INVALID_INCIDENT_ID",
            "reason": "Incident ID must be text."
        }

    value = incident_id.strip()

    if not value:
        return {
            "allowed": False,
            "code": "EMPTY_INCIDENT_ID",
            "reason": "Incident ID is required."
        }

    if len(value) > MAX_INCIDENT_ID_LENGTH:
        return {
            "allowed": False,
            "code": "INCIDENT_ID_TOO_LONG",
            "reason": (
                f"Incident ID exceeds "
                f"{MAX_INCIDENT_ID_LENGTH} characters."
            )
        }

    # Keep identifiers safe for logs and simple audit records.
    allowed_characters = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789-_"
    )

    if any(character not in allowed_characters for character in value):
        return {
            "allowed": False,
            "code": "INVALID_INCIDENT_ID_CHARACTERS",
            "reason": (
                "Incident ID may contain only letters, "
                "numbers, hyphens and underscores."
            )
        }

    return {
        "allowed": True,
        "code": "INCIDENT_ID_ACCEPTED",
        "incident_id": value,
        "reason": "Incident ID passed validation."
    }
