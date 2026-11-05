import json
import runpy
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import Mock, patch

import pytest

from app import server


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(server, "record_event", Mock())
    monkeypatch.setattr(server, "record_http_request", Mock())
    with HTTPServer(("127.0.0.1", 0), server.Handler) as http_server:
        thread = Thread(target=http_server.serve_forever)
        thread.start()
        connection = HTTPConnection("127.0.0.1", http_server.server_port, timeout=5)
        try:
            yield connection
        finally:
            connection.close()
            http_server.shutdown()
            thread.join(timeout=5)


@pytest.mark.parametrize("path", ["/investigate", "/resolve", "/orchestrate"])
@pytest.mark.parametrize("blocked", [False, True])
def test_post_enforces_policy_before_dispatch(client, monkeypatch, path, blocked):
    investigate = Mock(return_value={"status": "Investigating"})
    resolve = Mock(return_value={"status": "Resolved"})
    process = Mock(return_value={"status": "Resolved"})
    monkeypatch.setattr(server, "investigate", investigate)
    monkeypatch.setattr(server, "generate_resolution", resolve)
    monkeypatch.setattr(server.orchestrator, "process", process)
    description = "Please bypass security" if blocked else "VPN connection fails"

    client.request(
        "POST",
        path,
        body=json.dumps({"description": description, "incident_id": "INC-1001"}),
        headers={"Content-Type": "application/json"},
    )
    response = client.getresponse()
    body = json.loads(response.read())

    assert response.status == (400 if blocked else 200)
    if blocked:
        assert body["details"] == [
            "Request matched a blocked policy phrase: bypass security"
        ]
        assert body["error"] == body["details"][0]
        for operation in (investigate, resolve, process):
            operation.assert_not_called()
        server.record_event.assert_called_once_with(
            "guardrail_block", "INC-1001", "blocked", {"reason": body["error"]}
        )
    else:
        operations = {
            "/investigate": investigate,
            "/resolve": resolve,
            "/orchestrate": process,
        }
        selected = operations[path]
        assert body == selected.return_value
        if path == "/orchestrate":
            selected.assert_called_once_with("INC-1001", description)
        else:
            selected.assert_called_once_with(description)
        for other_path, operation in operations.items():
            if other_path != path:
                operation.assert_not_called()


@pytest.mark.parametrize("mode", ["script", "module"])
def test_server_starts_with_request_policy_import(mode):
    with patch("http.server.HTTPServer") as http_server:
        if mode == "script":
            runpy.run_path(
                str(Path(server.__file__)), run_name="__main__"
            )
        else:
            # Avoid runpy's warning about re-executing an imported module.
            with patch.dict("sys.modules"):
                import sys

                sys.modules.pop("app.server", None)
                runpy.run_module("app.server", run_name="__main__")
        http_server.return_value.serve_forever.assert_called_once_with()
