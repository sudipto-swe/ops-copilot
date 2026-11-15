import os
import re
from typing import Any

import httpx

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

    Provides standardized telemetry and diagnostic tools over HTTP / JSON-RPC.
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
                "description": "Fetch recent container/service logs with optional regex filtering and redaction.",
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
        ]

    def list_tools(self) -> list[dict[str, Any]]:
        return self.tool_definitions

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
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

        import anyio
        async with await anyio.open_file(log_file, "r") as f:
            all_lines = await f.readlines()

        selected = all_lines[-lines:] if lines > 0 else all_lines
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            selected = [ln for ln in selected if regex.search(ln)]

        # Secret redaction before surfacing logs
        redacted = []
        for line in selected:
            clean = re.sub(r"(?i)(bearer\s+[A-Za-z0-9_\-\.]+)", "BEARER [REDACTED]", line)
            clean = re.sub(r"(?i)(password|secret|token)=[\"']?[^\"'\s]+", r"\1=[REDACTED]", clean)
            redacted.append(clean.strip())

        return {"service": service, "total_returned": len(redacted), "lines": redacted}

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
        # Return synthetic deployment / incident events
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

mcp_server = MCPServer()
