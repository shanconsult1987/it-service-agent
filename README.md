# Contoso IT Support Agent

## Interfaces

- **HTTP interface** - implemented by [app/server.py](app/server.py).
  - Base URL: http://127.0.0.1:8000.
  - `GET /`: reports service status.
  - `GET /health`: reports process health.
  - `GET /ready`: checks required local files; returns HTTP 503 if any are missing.
  - `GET /metrics`: returns process-local request and latency metrics.
  - `GET /api/dashboard`: returns the executive dashboard JSON payload.
  - `POST /investigate`: classifies an incident and checks knowledge availability.
  - `POST /resolve`: generates a resolution using the configured LLM, or returns
    deterministic guidance when no API key is configured.
  - `POST /orchestrate`: runs the multi-agent incident workflow.
  - Request requirements:
    - POST requests require `Content-Type: application/json` and a JSON object
      containing `description`.
    - `/orchestrate` also accepts `incident_id`, defaulting to `INC-DEMO`.
    - Responses include an `X-Request-ID` header for correlation.
- **Dashboard interface** - rendered by
  [app/dashboard_page.py](app/dashboard_page.py).
  - Open http://127.0.0.1:8000/dashboard for the executive dashboard.
  - Displays runtime metrics, evaluations, responsible AI controls, ROI estimates,
    audit events, and the latest persisted agent state.
- **Python interfaces** - functions and methods rather than formal abstract
  interface classes.
  - [app/agent.py](app/agent.py):
    - `classify_incident(description)`: returns category, priority, and assigned agent.
    - `investigate(description)`: records investigation state and checks knowledge.
    - `generate_resolution(description)`: returns LLM or deterministic guidance.
  - [app/orchestrator.py](app/orchestrator.py):
    - `ITServiceOrchestrator.process(incident_id, description, correlation_id=...)`:
      validates inputs and coordinates triage, knowledge, resolution, and policy.
  - [app/dashboard.py](app/dashboard.py):
    - `calculate_roi()`: calculates business-value estimates.
    - `responsible_ai_summary()`: summarizes declared control statuses.
    - `executive_dashboard()`: assembles the dashboard payload.
  - [app/evaluation.py](app/evaluation.py):
    - `run_evaluation()`: runs authored acceptance cases.

## Classes

- [app/server.py](app/server.py):
  - `Handler(BaseHTTPRequestHandler)`: handles HTTP routes, input validation,
    response formatting, correlation IDs, and request metrics.
  - The server uses the standard-library `ThreadingHTTPServer` to handle requests.
- [app/orchestrator.py](app/orchestrator.py):
  - `ITServiceOrchestrator`: creates and coordinates the five workflow agents.
- [app/agents.py](app/agents.py):
  - `TriageAgent`:
    - `run(description)` classifies the incident and updates triage state.
  - `KnowledgeAgent`:
    - `run(description, category)` retrieves matching approved knowledge sections.
  - `ResolutionAgent`:
    - `run(description, evidence)` proposes guidance and a confidence score,
      escalating when approved knowledge is unavailable.
  - `PolicyAgent`:
    - `run(priority, confidence)` chooses `ESCALATE`, `HUMAN_APPROVAL`, or `RESOLVE`.
    - Confidence below `0.7` requires escalation; otherwise, high-priority cases
      require human approval.
  - `HumanEscalationAgent`:
    - `run(reason)` records escalation state and appends the reason to memory.

## Developer steps

- **Prepare the workspace**:
  - Clone the repository and enter the project root:

    ```powershell
    git clone https://github.com/shanconsult1987/it-service-agent.git
    Set-Location it-service-agent
    ```

  - Use Python 3.11 or 3.12 to match the CI test matrix.
  - Create a virtual environment and install dependencies:

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    ```

  - In VS Code, select the interpreter at `.venv\Scripts\python.exe`.
  - Commands below use `python`; activate the environment first, or replace
    `python` with `.\.venv\Scripts\python.exe`:

    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```

- **Configure optional LLM access**:
  - Without `OPENAI_API_KEY`, `/resolve` uses deterministic guidance.
  - For LLM-backed resolutions, set `OPENAI_API_KEY` in the server process
    environment using your local secret-management workflow.
  - Optionally set `OPENAI_MODEL`; the default is `gpt-5`.
  - Do not commit credentials. Environment variables must be set explicitly;
    the application does not automatically load a `.env` file.
- **Review local inputs and persistence**:
  - Approved troubleshooting knowledge:
    [knowledge/it-support.md](knowledge/it-support.md).
  - ROI assumptions: [data/roi.json](data/roi.json).
  - Responsible AI controls: [data/responsible_ai.json](data/responsible_ai.json).
  - Acceptance fixtures: [data/evaluation_cases.json](data/evaluation_cases.json).
  - Runtime requests can update [data/agent_state.json](data/agent_state.json),
    [data/agent_memory.md](data/agent_memory.md), and
    [data/audit.jsonl](data/audit.jsonl).
- **Validate changes before submitting**:
  - Run the same syntax, test, and acceptance checks used in
    [.github/workflows/ci.yml](.github/workflows/ci.yml):

    ```powershell
    python -m compileall -q app tests
    python -m pytest -q
    python -m app.evaluation
    ```

  - Start the server using the steps below.
  - In a second terminal, check health and readiness:

    ```powershell
    Invoke-RestMethod http://127.0.0.1:8000/health
    Invoke-RestMethod http://127.0.0.1:8000/ready
    ```

  - Open http://127.0.0.1:8000/dashboard to inspect the dashboard.

## Run the server

- From the project root:

  ```powershell
  python -m app.server
  ```

- Direct script execution also works, including from another working directory:

  ```powershell
  python C:\Users\shivensingh\it-service-agent\app\server.py
  ```

- The server listens at http://127.0.0.1:8000. `GET /` reports its status.
- `POST /investigate`, `POST /resolve`, and `POST /orchestrate` accept a JSON
  body with a `description` field; `/orchestrate` also accepts `incident_id`.
- Press Ctrl+C to stop it.

## Dashboard data

- [app/dashboard.py](app/dashboard.py) reads ROI inputs from
  [data/roi.json](data/roi.json) and responsible AI controls from
  [data/responsible_ai.json](data/responsible_ai.json). Both files must contain
  valid JSON and be saved as UTF-8 (with or without a byte order mark).

- ROI output includes the configured `assumptions` and a `basis` caveat alongside
  the calculated values.
- The responsible AI summary includes `score_percent`:
  - The percentage of controls declared `Pass`, rounded to two decimal places, or
    `null` when there are no controls.
  - This is a self-declared register score, not independent compliance certification.

- If loading fails, the error identifies the file.
  - Empty files must be restored with their intended data.
  - Invalid JSON errors include the line and column to correct.
  - The dashboard does not substitute empty or default data on failure.

- Run the dashboard regression tests from the project root:

  ```powershell
  python -m pytest tests\test_dashboard.py -q
  ```

## Unit tests and coverage

- Install the dependencies, which include `pytest` and `coverage`:

  ```powershell
  python -m pip install -r requirements.txt
  ```

- Run the unit tests for [app/agent.py](app/agent.py),
  [app/agents.py](app/agents.py), and
  [app/orchestrator.py](app/orchestrator.py) with branch coverage, then print
  the report:

  ```powershell
  python -m coverage run --branch --include=app/agent.py,app/agents.py,app/orchestrator.py -m pytest tests\test_agent.py tests\test_agents.py tests\test_orchestrator.py -q
  python -m coverage report -m
  ```

- Latest results (Python 3.14.7, coverage 7.15.4): 34 tests passed, with no
  missing lines or branches.

  | File | Lines and statements | Branches |
  |---|---|---|
  | [app/agent.py](app/agent.py) | 37/37 (100%) | 8/8 (100%) |
  | [app/agents.py](app/agents.py) | 40/40 (100%) | 10/10 (100%) |
  | [app/orchestrator.py](app/orchestrator.py) | 22/22 (100%) | 2/2 (100%) |
  | **Total** | **99/99 (100%)** | **20/20 (100%)** |

- Coverage.py measures statements and reports lines as the same statements, so
  line and statement coverage are identical here.