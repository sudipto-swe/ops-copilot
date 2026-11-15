from typing import Any

from apps.api.app.llm.client import BaseLLMClient, LLMResponse


class DynamicScriptedLLMClient(BaseLLMClient):
    """Context-aware multi-scenario SRE reasoning engine for unit tests and local eval."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step_tracker: dict[str, int] = {}

    async def _generate(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        # Extract the original alert text specifically
        alert_line = ""
        for line in prompt.splitlines():
            if line.startswith("Alert:"):
                alert_line = line.lower()
                break

        # Determine target service from alert text
        target_service = "gateway"
        if "orders" in alert_line or "oom" in alert_line or "pool" in alert_line or "dependency" in alert_line:
            target_service = "orders"
        elif "payment" in alert_line or "slow" in alert_line or "port" in alert_line or "latency" in alert_line:
            target_service = "payments"

        # Determine scenario action
        action = "restart"
        if "oom" in alert_line or "pool" in alert_line:
            action = "scale"
        elif "port" in alert_line:
            action = "rollback"

        # Step 1: list_services
        if "Action: {'name': 'list_services'" not in prompt:
            return LLMResponse(
                content="Listing monitored microservices to understand topology.",
                tool_calls=[{"name": "list_services", "arguments": {}}],
            )

        # Step 2: get_service_status
        if f"Action: {{'name': 'get_service_status', 'arguments': {{'service': '{target_service}'}}}}" not in prompt:
            return LLMResponse(
                content=f"Checking health and readiness of {target_service}.",
                tool_calls=[{"name": "get_service_status", "arguments": {"service": target_service}}],
            )

        # Step 3: get_logs
        if f"Action: {{'name': 'get_logs', 'arguments': {{'service': '{target_service}'" not in prompt:
            return LLMResponse(
                content=f"Examining recent logs for {target_service} to identify root cause.",
                tool_calls=[{"name": "get_logs", "arguments": {"service": target_service, "lines": 25}}],
            )

        # Step 4: search_runbooks
        if "Action: {'name': 'search_runbooks'" not in prompt:
            return LLMResponse(
                content="Searching RAG runbook repository for triage and remediation procedure.",
                tool_calls=[{"name": "search_runbooks", "arguments": {"query": f"{target_service} failure {action}", "top_k": 2}}],
            )

        # Step 5: propose_remediation
        if "Action: {'name': 'propose_remediation'" not in prompt:
            return LLMResponse(
                content=f"Proposing remediation action '{action}' for {target_service}.",
                tool_calls=[{
                    "name": "propose_remediation",
                    "arguments": {
                        "action": action,
                        "target_service": target_service,
                        "incident_id": "INC-AUTO-TRIAGE",
                        "reason": f"Remediate {target_service} failure via verified SRE runbook."
                    }
                }],
            )

        # Final Incident Report
        return LLMResponse(
            content=f"""# Incident Report: INC-AUTO-TRIAGE
**Summary**: Automatic triage completed for {target_service}.
**Target Service**: {target_service}
**Recommended Action**: {action}
**Root Cause Hypothesis**: Service instability detected in {target_service} matching SRE runbook.
"""
        )
