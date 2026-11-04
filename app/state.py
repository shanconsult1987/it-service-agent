import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

STATE_FILE = ROOT / "data" / "agent_state.json"


def load_state():
    with open(
        STATE_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_state(state):
    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            state,
            file,
            indent=2
        )


def update_state(**updates):
    state = load_state()

    state.update(updates)

    save_state(state)

    return state


def reset_state():

    state = {
        "incident_id": None,
        "status": "New",
        "category": None,
        "priority": None,
        "assigned_agent": None,
        "confidence": None,
        "resolution": None,
        "escalation_required": False,
        "last_action": None
    }

    save_state(state)

    return state