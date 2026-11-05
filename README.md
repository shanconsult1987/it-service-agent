# IT Service Desk (Contoso)

- **Overview**
  - A Python IT service desk application for incident classification, knowledge-based
    resolution recommendations, multi-agent orchestration, and human escalation.
  - Includes a web dashboard for runtime metrics, governance, responsible AI,
    evaluation results, estimated LLM costs, ROI, and audit events.
  - Runs locally with deterministic behavior; OpenAI-backed resolution is optional.

- **Setup**
  - Prerequisites:
    - Python with `pip` and `venv`.
    - PowerShell for the commands below.
  - Clone the repository and enter the project directory:
    ```powershell
    git clone https://github.com/shanconsult1987/it-service-agent.git
    Set-Location .\it-service-agent
    ```
  - Create a virtual environment and install dependencies:
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    ```
  - Optional: enable OpenAI-backed resolution in the current terminal:
    ```powershell
    $env:OPENAI_API_KEY = "<your-api-key>"
    $env:OPENAI_MODEL = "gpt-5"
    ```
    - Keep API keys out of source control.
    - Without `OPENAI_API_KEY`, resolution uses the deterministic fallback.
    - `OPENAI_MODEL` defaults to `gpt-5`; API usage may incur charges.
  - Start the server from the project root:
    ```powershell
    .\.venv\Scripts\python.exe -m app.server
    ```
    - Direct-file startup is also supported:
      ```powershell
      .\.venv\Scripts\python.exe .\app\server.py
      ```
    - Running the server by its absolute file path from another directory also
      resolves the application's package imports.
    - Server address: http://127.0.0.1:8000.
    - Dashboard: http://127.0.0.1:8000/dashboard.
    - Stop the server with `Ctrl+C`.

- **Key Interfaces**
  - HTTP endpoints in [server.py](app/server.py):
    - `GET /`: service name and health status.
    - `GET /dashboard`: HTML dashboard.
    - `GET /api/dashboard`: dashboard snapshot as JSON.
    - `POST /investigate`: classify an incident and check knowledge availability.
    - `POST /resolve`: generate a resolution recommendation or deterministic fallback.
    - `POST /orchestrate`: execute the multi-agent incident workflow.
  - POST request contract:
    - `description`: non-empty text, up to 2000 characters.
    - `incident_id`: `INC-` followed by 4 to 8 digits, such as `INC-1001`.
    - Requests failing policy checks return HTTP 400 with `error` and `details`.
    - Blocked phrases are configured in
      [security_policy.json](data/security_policy.json).
    - Example:
      ```powershell
      $body = @{
          incident_id = "INC-1001"
          description = "VPN connection fails"
      } | ConvertTo-Json

      Invoke-RestMethod `
          -Uri "http://127.0.0.1:8000/investigate" `
          -Method Post `
          -ContentType "application/json" `
          -Body $body
      ```
  - Python entry points:
    - [agent.py](app/agent.py): `classify_incident(description)`,
      `investigate(description)`, and `generate_resolution(description)`.
    - [guardrails.py](app/guardrails.py):
      `enforce_request_policy(description, incident_id)`, `check_input(text)`,
      `validate_incident_id(incident_id)`, and
      `check_resolution_policy(category, priority, confidence)`.
    - [dashboard.py](app/dashboard.py): `dashboard_snapshot()`.
    - [evaluation.py](app/evaluation.py): `run_evaluation()`.

- **Key Classes**
  - [Handler](app/server.py): HTTP request handler for service and dashboard routes.
  - [ITServiceOrchestrator](app/orchestrator.py):
    - `process(incident_id, description)` coordinates triage, knowledge retrieval,
      resolution, policy decisions, and escalation.
  - Agent classes in [agents.py](app/agents.py):
    - `TriageAgent`: classifies incidents and assigns a category, priority, and agent.
    - `KnowledgeAgent`: retrieves matching sections from approved knowledge.
    - `ResolutionAgent`: recommends an approved procedure or human escalation.
    - `PolicyAgent`: decides between resolution, escalation, and human approval.
    - `HumanEscalationAgent`: records escalation state and memory.
  - [GuardrailResult](app/guardrails.py):
    - Dataclass containing `allowed`, `outcome`, and `reason` for guardrail checks.

- **Configuration and Persistence**
  - [it-support.md](knowledge/it-support.md): approved troubleshooting knowledge.
  - [security_policy.json](data/security_policy.json): request restrictions and
    resolution-policy settings used by the guardrail functions.
  - [state.py](app/state.py): incident state stored in
    [agent_state.json](data/agent_state.json).
  - [memory.py](app/memory.py): resolution and escalation notes stored in
    [agent_memory.md](data/agent_memory.md).
  - [audit.py](app/audit.py): append-only events stored in
    [audit.jsonl](data/audit.jsonl).
  - [monitoring.py](app/monitoring.py): in-memory HTTP and LLM metrics; reset when
    the process restarts.

- **Unit Tests**
  - Run the complete test suite from the project root:
    ```powershell
    .\.venv\Scripts\python.exe -m pytest tests -q
    ```
  - Run focused evaluation and request-policy tests:
    ```powershell
    .\.venv\Scripts\python.exe -m pytest tests\test_evaluation.py tests\test_guardrails.py tests\test_server_policy.py -q
    ```
  - Collect coverage:
    ```powershell
    .\.venv\Scripts\python.exe -m pytest tests --cov=app --cov-report=term-missing
    ```
  - Test coverage areas:
    - [test_day3_baseline.py](tests/test_day3_baseline.py): incident classification.
    - [test_evaluation.py](tests/test_evaluation.py): report generation, category
      mismatches, classifier errors, empty cases, timestamps, and persistence.
    - [test_guardrails.py](tests/test_guardrails.py): input validation, incident IDs,
      configured blocked phrases, and resolution-policy decisions.
    - [test_server_policy.py](tests/test_server_policy.py): server startup and policy
      enforcement before HTTP request dispatch.

- **Acceptance Evaluation**
  - Run the synthetic acceptance cases:
    ```powershell
    .\.venv\Scripts\python.exe -m app.evaluation
    ```
  - Reads [evaluation.json](data/evaluation.json) and writes
    [evaluation_results.json](data/evaluation_results.json).
  - Reports pass/fail counts and pass rate; exits with code 1 if any case fails.

- **License**
  - Distributed under the [MIT License](LICENSE).
  - Copyright (c) 2026 shanconsult1987.