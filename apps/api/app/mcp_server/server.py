import os
import re
from typing import Any

import anyio
import httpx

from apps.api.app.rag.index import rag_index
from apps.api.app.safety.guard import (
    ALLOWLISTED_ACTIONS,
    ALLOWLISTED_SERVICES,
    generate_approval_token,
    is_prompt_injection,
    log_audit_event,
    redact_secrets,
    verify_approval_token,
)

SERVICE_URLS = {
    "gateway": os.getenv("GATEWAY_URL", "http://localhost:8001"),
    "orders": os.getenv("ORDERS_URL", "http://localhost:8002"),
    "payments": os.getenv("PAYMENTS_URL", "http://localhost:8003"),
}

LOG_PATHS = {
    "gateway": "logs/gateway.log",
    "orders": "logs/orders.log",
    "payments": "logs/payments.log",
}

class MCPServer:
    """Model Context Protocol Server for Ops Copilot.

    Provides standardized telemetry, RAG search, and guarded remediation tools.
    """

    def __init__(self):
        self.tool_definitions = [
            {
                "name": "list_services",
                "description": "List all monitored synthetic microservices in the shop architecture.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_service_status",
                "description": "Query live health and readiness endpoints for a given service.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "enum": ["gateway", "orders", "payments"],
                            "description": "Name of the target service",
                        }
                    },
                    "required": ["service"],
                },
            },
            {
                "name": "get_logs",
                "description": "Fetch recent container/service logs with regex filtering, secret redaction, and prompt-injection defense.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "enum": ["gateway", "orders", "payments"]},
                        "lines": {"type": "integer", "default": 50},
                        "pattern": {"type": "string", "description": "Optional regex to filter log lines"},
                    },
                    "required": ["service"],
                },
            },
            {
                "name": "query_metrics",
                "description": "Query Prometheus metrics using allowlisted PromQL templates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "metric_template": {
                            "type": "string",
                            "enum": [
                                "http_requests_total",
                                "request_duration_seconds",
                                "service_error_rate",
                            ],
                            "description": "Allowlisted metric template to evaluate",
                        },
                        "service": {"type": "string", "enum": ["gateway", "orders", "payments"]},
                    },
                    "required": ["metric_template", "service"],
                },
            },
            {
                "name": "get_recent_events",
                "description": "Fetch recent deployment, crash, and configuration change events.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "service": {"type": "string", "enum": ["gateway", "orders", "payments", "all"]}
                    },
                },
            },
            {
                "name": "search_runbooks",
                "description": "Search synthetic SRE runbooks via local RAG for remediation guidance.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query describing symptoms or errors"},
                        "top_k": {"type": "integer", "default": 3},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "propose_remediation",
                "description": "Propose an allowlisted remediation action (restart, scale, rollback). Returns proposal with cryptographic approval token without executing anything.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["restart", "scale", "rollback"]},
                        "target_service": {"type": "string", "enum": ["gateway", "orders", "payments"]},
                        "incident_id": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["action", "target_service", "incident_id", "reason"],
                },
            },
            {
                "name": "execute_remediation",
                "description": "Execute a proposed remediation action. Requires human approval token and enforces dry-run mode by default.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["restart", "scale", "rollback"]},
                        "target_service": {"type": "string", "enum": ["gateway", "orders", "payments"]},
                        "incident_id": {"type": "string"},
                        "approval_token": {"type": "string"},
                        "dry_run": {"type": "boolean", "default": True},
                    },
                    "required": ["action", "target_service", "incident_id", "approval_token"],
                },
            },
        ]

    def list_tools(self) -> list[dict[str, Any]]:
        return self.tool_definitions

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        log_audit_event("tool_call_invoked", {"tool": name, "arguments": arguments})

        if name == "list_services":
            return await self._list_services()
        if name == "get_service_status":
            return await self._get_service_status(arguments.get("service", ""))
        if name == "get_logs":
            return await self._get_logs(
                arguments.get("service", ""),
                arguments.get("lines", 50),
                arguments.get("pattern"),
            )
        if name == "query_metrics":
            return await self._query_metrics(
                arguments.get("metric_template", ""),
                arguments.get("service", ""),
            )
        if name == "get_recent_events":
            return await self._get_recent_events(arguments.get("service", "all"))
        if name == "search_runbooks":
            return self._search_runbooks(arguments.get("query", ""), arguments.get("top_k", 3))
        if name == "propose_remediation":
            return self._propose_remediation(
                arguments.get("action", ""),
                arguments.get("target_service", ""),
                arguments.get("incident_id", ""),
                arguments.get("reason", ""),
            )
        if name == "execute_remediation":
            return await self._execute_remediation(
                arguments.get("action", ""),
                arguments.get("target_service", ""),
                arguments.get("incident_id", ""),
                arguments.get("approval_token", ""),
                arguments.get("dry_run", True),
            )

        return {"error": f"Tool '{name}' not found", "success": False}

    async def _list_services(self) -> dict[str, Any]:
        return {
            "services": [
                {"name": "gateway", "url": SERVICE_URLS["gateway"], "tier": "edge"},
                {"name": "orders", "url": SERVICE_URLS["orders"], "tier": "backend"},
                {"name": "payments", "url": SERVICE_URLS["payments"], "tier": "backend"},
            ]
        }

    async def _get_service_status(self, service: str) -> dict[str, Any]:
        url = SERVICE_URLS.get(service)
        if not url:
            return {"error": f"Unknown service '{service}'", "status": "UNKNOWN"}

        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                resp = await client.get(f"{url}/health")
                is_healthy = resp.status_code == 200
                data = resp.json() if resp.status_code == 200 else {}
                return {
                    "service": service,
                    "status_code": resp.status_code,
                    "healthy": is_healthy,
                    "details": data,
                }
            except httpx.HTTPError as exc:
                return {
                    "service": service,
                    "healthy": False,
                    "status_code": 0,
                    "error": f"Connection error: {exc!s}",
                }

    async def _get_logs(
        self, service: str, lines: int = 50, pattern: str | None = None
    ) -> dict[str, Any]:
        log_file = LOG_PATHS.get(service)
        if not log_file or not os.path.exists(log_file):
            return {"service": service, "lines": [], "message": f"Log file '{log_file}' not found"}

        async with await anyio.open_file(log_file, "r") as f:
            all_lines = await f.readlines()

        selected = all_lines[-lines:] if lines > 0 else all_lines
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            selected = [ln for ln in selected if regex.search(ln)]

        clean_lines = []
        for line in selected:
            # Defend against adversarial prompt injections planted in log lines
            if is_prompt_injection(line):
                clean_lines.append("[SECURITY WARNING: Adversarial prompt-injection log line neutralized]")
                continue
            clean_lines.append(redact_secrets(line.strip()))

        return {"service": service, "total_returned": len(clean_lines), "lines": clean_lines}

    async def _query_metrics(self, metric_template: str, service: str) -> dict[str, Any]:
        url = SERVICE_URLS.get(service)
        if not url:
            return {"error": f"Unknown service '{service}'"}

        async with httpx.AsyncClient(timeout=3.0) as client:
            try:
                resp = await client.get(f"{url}/metrics")
                if resp.status_code != 200:
                    return {"error": f"Metrics endpoint returned {resp.status_code}"}

                raw_metrics = resp.text
                matched_lines = []
                for line in raw_metrics.splitlines():
                    if not line.startswith("#") and service in line:
                        matched_lines.append(line)

                return {
                    "metric_template": metric_template,
                    "service": service,
                    "matched_samples": matched_lines[:15],
                }
            except httpx.HTTPError as exc:
                return {"error": f"Failed to retrieve metrics: {exc!s}"}

    async def _get_recent_events(self, service: str = "all") -> dict[str, Any]:
        events = [
            {
                "timestamp": "2026-11-15T11:00:00Z",
                "service": "payments",
                "type": "deploy",
                "version": "v1.4.2",
                "message": "Deployed release v1.4.2 to payments",
            },
            {
                "timestamp": "2026-11-15T11:05:00Z",
                "service": "orders",
                "type": "config_change",
                "version": "v2.1.0",
                "message": "Updated cgroup memory limits to 128MB",
            },
            {
                "timestamp": "2026-11-15T11:15:00Z",
                "service": "gateway",
                "type": "deploy",
                "version": "v2.0.1",
                "message": "Updated route mapping and security filters",
            },
        ]
        if service != "all":
            events = [e for e in events if e["service"] == service]
        return {"events": events}

    def _search_runbooks(self, query: str, top_k: int = 3) -> dict[str, Any]:
        matches = rag_index.search(query, top_k=top_k)
        return {
            "query": query,
            "top_k": top_k,
            "matches": matches,
        }

    def _propose_remediation(
        self, action: str, target_service: str, incident_id: str, reason: str
    ) -> dict[str, Any]:
        if action not in ALLOWLISTED_ACTIONS:
            return {"error": f"Action '{action}' is not allowlisted (allowed: {sorted(ALLOWLISTED_ACTIONS)})"}
        if target_service not in ALLOWLISTED_SERVICES:
            return {"error": f"Target service '{target_service}' is not allowlisted"}

        token = generate_approval_token(action, target_service, incident_id)
        log_audit_event("remediation_proposed", {
            "incident_id": incident_id,
            "action": action,
            "target_service": target_service,
            "reason": reason,
            "approval_token": token,
        })
        return {
            "status": "PROPOSED",
            "incident_id": incident_id,
            "action": action,
            "target_service": target_service,
            "reason": reason,
            "approval_token": token,
            "requires_human_approval": True,
        }

    async def _execute_remediation(
        self, action: str, target_service: str, incident_id: str, approval_token: str, dry_run: bool
    ) -> dict[str, Any]:
        if action not in ALLOWLISTED_ACTIONS or target_service not in ALLOWLISTED_SERVICES:
            return {"error": "Invalid action or target service", "executed": False}

        # Verify HMAC approval token
        if not verify_approval_token(approval_token, action, target_service, incident_id):
            log_audit_event("unauthorized_remediation_attempt", {
                "incident_id": incident_id,
                "action": action,
                "target_service": target_service,
            })
            return {"error": "Invalid or forged approval token. Execution rejected.", "executed": False}

        if dry_run:
            log_audit_event("remediation_dry_run_executed", {
                "incident_id": incident_id,
                "action": action,
                "target_service": target_service,
            })
            return {
                "status": "DRY_RUN_COMPLETED",
                "message": f"Verified plan: would execute '{action}' on {target_service}.",
                "dry_run": True,
                "executed": False,
            }

        # Live execution (e.g., reset fault state to healthy)
        url = SERVICE_URLS.get(target_service)
        if url:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(f"{url}/simulate_fault", json={"type": "healthy", "latency_ms": 0})

        log_audit_event("remediation_executed", {
            "incident_id": incident_id,
            "action": action,
            "target_service": target_service,
        })
        return {
            "status": "EXECUTED",
            "action": action,
            "target_service": target_service,
            "executed": True,
            "message": f"Successfully executed '{action}' on service {target_service}.",
        }

mcp_server = MCPServer()
