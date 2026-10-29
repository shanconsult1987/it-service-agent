# it-service-agent

## Run the server

From the project root:

```powershell
python -m app.server
```

Direct script execution also works, including from another working directory:

```powershell
python C:\Users\shivensingh\it-service-agent\app\server.py
```

The server listens at http://127.0.0.1:8000. `GET /` reports its status.
`POST /investigate`, `POST /resolve`, and `POST /orchestrate` accept a JSON
body with a `description` field; `/orchestrate` also accepts `incident_id`.
Press Ctrl+C to stop it.

## Dashboard data

`app/dashboard.py` reads ROI inputs from `data/roi.json` and responsible AI
controls from `data/responsible_ai.json`. Both files must contain valid JSON
and be saved as UTF-8 (with or without a byte order mark). The server does not
expose these as HTTP routes; the module is currently covered by its tests.

If loading fails, the error identifies the file. Empty files must be restored
with their intended data; invalid JSON errors include the line and column to
correct. The dashboard does not substitute empty or default data on failure.

Run the dashboard regression tests from the project root:

```powershell
python -m pytest tests\test_dashboard.py -q
```

## Unit tests and coverage

Install the dependencies, which include `pytest` and `coverage`:

```powershell
python -m pip install -r requirements.txt
```

Run the unit tests for `app/agent.py`, `app/agents.py`, and `app/orchestrator.py`
with branch coverage, then print the report:

```powershell
python -m coverage run --branch --include=app/agent.py,app/agents.py,app/orchestrator.py -m pytest tests\test_agent.py tests\test_agents.py tests\test_orchestrator.py -q
python -m coverage report -m
```

Latest results (Python 3.14.7, coverage 7.15.4): 34 tests passed, with no
missing lines or branches.

| File | Lines and statements | Branches |
|---|---|---|
| app/agent.py | 37/37 (100%) | 8/8 (100%) |
| app/agents.py | 40/40 (100%) | 10/10 (100%) |
| app/orchestrator.py | 22/22 (100%) | 2/2 (100%) |
| **Total** | **99/99 (100%)** | **20/20 (100%)** |

Coverage.py measures statements and reports lines as the same statements, so
line and statement coverage are identical here.