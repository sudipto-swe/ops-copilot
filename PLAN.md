# PLAN.md — Ops Copilot Execution Plan

## Milestones Overview

- [x] **Milestone 1 [MVP]**: Repo skeleton, Makefile, CI workflow, target system (`gateway`, `orders`, `payments`) with structured JSON logs & metrics.
  - Acceptance checks:
    - Target services run and return HTTP 200 on `/health`.
    - Services emit structured JSON logs and Prometheus `/metrics`.
    - Unit tests pass; `make test` succeeds.

- [x] **Milestone 2 [MVP]**: Fault injector and 3 initial reproducible scenarios with ground truth (`eval/scenarios.yaml`).
  - Acceptance checks:
    - `python3 -m scripts.inject_fault --scenario crash_loop` triggers target failure.
    - `python3 -m scripts.inject_fault --scenario oom_simulation` triggers memory failure.
    - `python3 -m scripts.inject_fault --scenario slow_db` injects latency.
    - Reset script restores normal operations.

- [x] **Milestone 3 [MVP]**: MCP server with read-only tools and unit tests.
  - Acceptance checks:
    - Tools `list_services`, `get_service_status`, `get_logs`, `query_metrics` return structured JSON.
    - Pytest suite tests each tool with positive & edge case scenarios.

- [ ] **Milestone 4 [MVP]**: Agent loop with `mock` LLM (deterministic tool-call sequences) and structured incident report output.
  - Acceptance checks:
    - Agent executes step budget, loop detection, and structured scratchpad.
    - Generates incident report citing exact log lines and metric values.
    - Unit tests verify deterministic agent run.

- [ ] **Milestone 5 [MVP]**: Real LLM provider wiring (`mock`, `gemini`, `groq`, etc.) & end-to-end incident diagnosis via `make demo`.
  - Acceptance checks:
    - `make demo` injects fault, runs agent diagnosis, prints verified incident report.
    - Zero hallucinated evidence rate verified programmatically.

- [ ] **Milestone 6 [MVP]**: Minimal Web UI (React/Vite) showing real-time agent steps, tool calls, and incident report; README status table.
  - Acceptance checks:
    - UI builds cleanly with `npm run build`.
    - Displays live/replay agent trace and incident report approval actions.

- [ ] **Milestone 7**: Runbook corpus (15–20 synthetic runbooks), chunking, local RAG index, and `search_runbooks` tool with Recall@k measurement.
  - Acceptance checks:
    - 15+ synthetic runbooks in `runbooks/`.
    - Eval script reports Recall@3 on benchmark queries.

- [ ] **Milestone 8**: Remaining scenarios (6 total) and `get_recent_events` tool.
  - Acceptance checks:
    - 6 reproducible fault injection scenarios with ground truth.
    - `get_recent_events` surfaces deployment/restart events.

- [ ] **Milestone 9**: Safety layer: secret redaction, prompt injection defense tests, approval flow (`propose_remediation`, `execute_remediation` with allowlist & dry-run), append-only audit log.
  - Acceptance checks:
    - Prompt-injection log line test passes (agent does not execute adversarial commands).
    - Unapproved remediations are rejected; dry-run defaults verified.
    - Audit log records each operation in append-only JSONL.

- [ ] **Milestone 10**: kind cluster deployment manifests (Kustomize) and deployment documentation.
  - Acceptance checks:
    - `deploy/kind/` Kustomize manifests validate cleanly.
    - `deploy/compose/` docker-compose manifests validate.

- [ ] **Milestone 11**: Evaluation harness: multi-run evaluation of all 6 scenarios, raw transcripts, baseline comparison vs no-tools LLM.
  - Acceptance checks:
    - Results committed to `results/`.
    - Hallucinated evidence rate, accuracy, and latency documented.

- [ ] **Milestone 12**: CI hardening, comprehensive documentation (`docs/INTERVIEW_NOTES.md`, `docs/CV_BULLETS.md`), final DoD run.
  - Acceptance checks:
    - `scripts/smoke.sh` passes completely.
    - Complete README with mermaid diagrams and honest status table.
