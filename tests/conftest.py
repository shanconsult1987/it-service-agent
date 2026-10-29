import json

import pytest

import app.agent
import app.memory
import app.state


SAMPLE_KNOWLEDGE = """# IT Support

## Network
Restart the VPN client and reconnect.

## Identity
Reset passwords through the self-service portal.

## Endpoint
Restart the device and close unused browser tabs.
"""


class DataFiles:
    def __init__(self, directory):
        self.state = directory / "agent_state.json"
        self.memory = directory / "agent_memory.md"
        self.knowledge = directory / "it-support.md"

    def state_data(self):
        return json.loads(self.state.read_text(encoding="utf-8"))

    def memory_text(self):
        return self.memory.read_text(encoding="utf-8")


@pytest.fixture
def isolated_data(tmp_path, monkeypatch):
    """Point state, memory, and knowledge at temp copies so tests never change data/ or knowledge/."""
    files = DataFiles(tmp_path)
    files.state.write_text("{}", encoding="utf-8")
    files.memory.write_text("# Agent Memory\n", encoding="utf-8")
    files.knowledge.write_text(SAMPLE_KNOWLEDGE, encoding="utf-8")

    monkeypatch.setattr(app.state, "STATE_FILE", files.state)
    monkeypatch.setattr(app.memory, "MEMORY_FILE", files.memory)
    monkeypatch.setattr(app.agent, "KNOWLEDGE_FILE", files.knowledge)
    return files
