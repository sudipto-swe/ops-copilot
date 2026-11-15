# DECISIONS.md — Architecture & Technical Decision Log

## ADR-001: Execution Environment & Zero-Budget Strategy
- **Context**: The environment is Linux (Python 3.14.4, Node v20.20.0). System-level Docker/kind binaries are not installed on the host and non-interactive `sudo` is unavailable.
- **Decision**:
  1. We provide production-ready `Dockerfile`, `docker-compose.yml`, and Kustomize manifests for kind clusters in `deploy/`.
  2. For the local execution runtime and tests in this environment, services (`gateway`, `orders`, `payments`, Prometheus server mock / exporter, API) run as managed lightweight local async processes orchestrated via `make up` / `make down` (with background supervisor scripts) and virtualenv.
  3. When Docker/kind is present on any developer machine or CI runner, standard `docker compose up` and kind Kustomize apply works seamlessly.
  4. Cost: $0. No paid cloud services.
- **Alternatives Considered**: Attempting to install Docker via root (impossible without sudo password).
- **Status**: Accepted.

## ADR-002: LLM Client Multi-Provider Architecture
- **Context**: Zero-budget rule requires mock provider for deterministic tests/CI and support for local/free hosted providers (`mock`, `ollama`, `gemini`, `groq`, `openrouter`).
- **Decision**:
  - Implement a unified `LLMClient` protocol in `apps/api/app/llm/client.py`.
  - Built-in on-disk cache (`.cache/llm_responses/`), exponential backoff retry loop, and thread-safe request counters.
  - Default provider: `mock` (used in tests and CI).
  - Config driven via typed `pydantic-settings` from `.env`.
- **Status**: Accepted.

## ADR-003: Model Context Protocol (MCP) Implementation
- **Context**: Standardized tool interface between agent and environment. Python official `mcp` SDK vs lightweight JSON-RPC / SSE transport.
- **Decision**:
  - Implement an in-memory & stdio/JSON-RPC compliant MCP server & client architecture compatible with the Model Context Protocol specification (`tools/list`, `tools/call`).
  - Read-only tools for telemetry/status; explicit approval token requirement for any mutation.
- **Status**: Accepted.

## ADR-004: Vector Search & Local Runbook Retrieval
- **Context**: RAG over runbooks needs zero cloud cost and fast local execution without heavy C-extension compilation issues in Python 3.14.
- **Decision**:
  - Use TF-IDF / BM25 with cosine similarity or SQLite-based vector / lexical hybrid embeddings for runbook search, with pluggable sentence embeddings if dependencies permit.
  - Zero cost, zero external API requirement, deterministic Recall@k evaluation.
- **Status**: Accepted.

## ADR-005: Safety and Human-In-The-Loop Approval Flow
- **Context**: Agent must propose remediations without applying them automatically.
- **Decision**:
  - `propose_remediation` creates an incident recommendation object with a cryptographic token (HMAC-SHA256).
  - `execute_remediation` checks for approval token and enforces dry-run by default unless `dry_run=False` is explicitly passed with a valid approved token.
  - Secrets are sanitized from logs using regex redaction (tokens, passwords, bearer keys) before reaching LLM context.
  - Append-only JSONL audit log records all tool calls and approvals.
- **Status**: Accepted.
