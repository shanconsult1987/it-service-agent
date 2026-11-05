# Stage 10 — Scalability and Enterprise Architecture

## 1. Current workshop architecture

The Day 3 application is a single-process teaching implementation.

It uses:

- Python HTTPServer
- Sequential agent orchestration
- JSON state files
- Markdown memory
- Local JSONL audit
- Process-local monitoring counters
- Synchronous LLM execution

It is not a production-scale distributed service.

## 2. Enterprise target architecture

### Ingress

Introduce a managed API gateway and load balancer.

Responsibilities:

- TLS termination
- Authentication
- Authorization
- Rate limiting
- Request validation
- Web application firewall

### Stateless API tier

Run multiple API instances behind the load balancer.

Application instances should not depend on local files or process memory for shared state.

### Durable workflow

Move long-running incident processing to a durable queue.

Workers should execute the agent workflow.

Use:

- Correlation IDs
- Idempotency keys
- Bounded retries
- Dead-letter queues
- Workflow checkpoints

### State and memory

Replace local JSON state with a transactional database.

Move governed knowledge into an approved search or retrieval platform.

Apply:

- Tenant isolation
- Retention policies
- Access controls
- Data classification

### Audit

Move audit events to a centrally managed store.

Provide:

- Access control
- Retention
- Integrity protection
- SIEM integration
- Investigation support

### Observability

Use centralized:

- Logs
- Metrics
- Distributed traces

Propagate a correlation ID across API calls, agent execution, tool invocation and LLM requests.

Do not log credentials, secrets or sensitive prompts by default.

### LLM operations

Introduce:

- Timeouts
- Exponential backoff with jitter
- Concurrency limits
- Token budgets
- Model quotas
- Circuit breakers
- Model routing
- Usage and cost attribution

### Human approval

Approval must be a durable workflow.

Record:

- Requested action
- Approver identity
- Decision
- Reason
- Timestamp
- Expiry
- Correlation ID

Do not rely on an in-memory approval branch for enterprise workflows.

### Security

Use:

- Managed identity
- Secret vault
- Least privilege
- Encryption
- Private networking where required
- Tenant isolation
- DLP controls

### Release engineering

Use:

- CI quality gates
- Security scanning
- Evaluation thresholds
- Prompt and model version tracking
- Staged deployment
- Rollback procedures

## 3. Classroom scalability experiment

Observe that the application currently has:

- One synchronous HTTP server
- Process-local metrics
- Local JSON state
- Local Markdown memory
- Local JSONL audit

Two application processes would have separate in-memory counters.

They could also attempt concurrent writes to the same local files.

This is not a safe distributed persistence design.

Do not use concurrent classroom traffic against these shared files as a production scalability test.

## 4. Production capacity planning

Measure representative approved traffic before sizing.

Required measurements:

- Requests per second
- Peak concurrency
- Average API latency
- p95 and p99 API latency
- Model calls per incident
- Tokens per incident
- Model latency
- Queue depth
- Retry rate
- Timeout rate
- Human approval backlog
- Cost per resolved incident

Never infer production capacity from the classroom demonstration.