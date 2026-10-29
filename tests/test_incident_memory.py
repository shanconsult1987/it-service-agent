from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import MagicMock, patch

from azure.core.exceptions import ClientAuthenticationError
from azure.cosmos.exceptions import CosmosHttpResponseError


ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "incident-memory-demo" / "incident_memory.py"
ENDPOINT = "https://example.documents.azure.com:443/"


def load_module():
    spec = spec_from_file_location("incident_memory", MODULE_PATH)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_client(query_result=None, query_error=None):
    container = MagicMock()

    if query_error is not None:
        container.query_items.side_effect = query_error
    else:
        container.query_items.return_value = query_result or []

    client = MagicMock()
    client.get_database_client.return_value.get_container_client.return_value = container
    return client


def test_missing_endpoint_is_reported_without_traceback(monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(module, "ENDPOINT", None)

    assert module.main() == 1

    captured = capsys.readouterr()
    assert "Set COSMOS_ENDPOINT" in captured.err
    assert "Traceback" not in captured.err


def test_startup_auth_failure_is_reported_before_menu(monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(module, "ENDPOINT", ENDPOINT)
    auth_error = ClientAuthenticationError(message="No token")

    with patch.object(module, "DefaultAzureCredential"), patch.object(
        module, "CosmosClient", side_effect=auth_error
    ):
        assert module.main() == 1

    captured = capsys.readouterr()
    assert "Connecting to Azure Cosmos DB..." in captured.out
    assert "Could not connect to Azure Cosmos DB: No token" in captured.err
    assert "Incident Memory Demo" not in captured.out
    assert "Traceback" not in captured.err


def test_cosmos_error_during_action_returns_to_menu(monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(module, "ENDPOINT", ENDPOINT)
    forbidden = CosmosHttpResponseError(message="(Forbidden) Request blocked by Auth")
    client = make_client(query_error=forbidden)

    with patch.object(module, "DefaultAzureCredential"), patch.object(
        module, "CosmosClient", return_value=client
    ), patch("builtins.input", side_effect=["2", "4"]):
        assert module.main() is None

    captured = capsys.readouterr()
    assert captured.out.count("=== Incident Memory Demo ===") == 2
    assert "Cosmos DB request failed:" in captured.err
    assert "(Forbidden) Request blocked by Auth" in captured.err
    assert "Traceback" not in captured.err


def test_view_incident_prints_details_when_connected(monkeypatch, capsys):
    module = load_module()
    monkeypatch.setattr(module, "ENDPOINT", ENDPOINT)
    incident = {
        "id": "INC-1001",
        "customer": "Contoso Energy",
        "priority": "High",
        "status": "Investigating",
        "nextAction": "Investigate backend dependency failures",
        "memory": [],
    }
    client = make_client(query_result=[incident])

    with patch.object(module, "DefaultAzureCredential"), patch.object(
        module, "CosmosClient", return_value=client
    ), patch("builtins.input", side_effect=["2", "4"]):
        module.main()

    captured = capsys.readouterr()
    assert "Priority: High" in captured.out
    assert captured.err == ""
