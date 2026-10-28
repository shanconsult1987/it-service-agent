from pathlib import Path


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
            "priority": "High"
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
            "priority": "Medium"
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
            "priority": "Medium"
        }

    return {
        "category": "Unknown",
        "priority": "Low"
    }


def investigate(description):

    classification = classify_incident(
        description
    )

    return {
        "description": description,
        "category": classification["category"],
        "priority": classification["priority"],
        "knowledge_available": bool(
            load_knowledge()
        )
    }