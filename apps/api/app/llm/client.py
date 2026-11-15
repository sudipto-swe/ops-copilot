import abc
import hashlib
import json
import os
from typing import Any

import httpx


class LLMResponse:
    def __init__(self, content: str, tool_calls: list[dict[str, Any]] | None = None, raw: dict[str, Any] | None = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.raw = raw or {}

    def to_dict(self) -> dict[str, Any]:
        return {"content": self.content, "tool_calls": self.tool_calls}

class BaseLLMClient(abc.ABC):
    def __init__(self, cache_dir: str = ".cache/llm_responses", max_retries: int = 3, backoff_factor: float = 1.5):
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.request_count = 0
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_key(self, prompt: str, tools: list[dict[str, Any]] | None) -> str:
        data = f"{prompt}|{json.dumps(tools or [], sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> LLMResponse | None:
        path = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                return LLMResponse(content=data["content"], tool_calls=data.get("tool_calls"))
        return None

    def _save_cached_response(self, cache_key: str, response: LLMResponse) -> None:
        path = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(path, "w") as f:
            json.dump({"content": response.content, "tool_calls": response.tool_calls}, f)

    @abc.abstractmethod
    async def _generate(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        pass

    async def generate(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        cache_key = self._get_cache_key(prompt, tools)
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        self.request_count += 1
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                resp = await self._generate(prompt, tools)
                self._save_cached_response(cache_key, resp)
                return resp
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                last_exc = exc
                wait_time = self.backoff_factor * (2**attempt)
                import asyncio
                await asyncio.sleep(wait_time)

        raise RuntimeError(f"LLM request failed after {self.max_retries} attempts: {last_exc}")

class MockLLMClient(BaseLLMClient):
    """Deterministic, scripted LLM provider for tests and CI."""

    def __init__(self, scripted_responses: list[LLMResponse] | None = None, **kwargs):
        super().__init__(**kwargs)
        self.scripted_responses = scripted_responses or []
        self._call_index = 0

    def add_response(self, response: LLMResponse) -> None:
        self.scripted_responses.append(response)

    async def _generate(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        if self._call_index < len(self.scripted_responses):
            res = self.scripted_responses[self._call_index]
            self._call_index += 1
            return res

        # Default scripted heuristic if no custom response provided
        # Step 1: call list_services
        if "list_services" not in prompt and self._call_index == 0:
            self._call_index += 1
            return LLMResponse(
                content="I will first list all monitored microservices.",
                tool_calls=[{"name": "list_services", "arguments": {}}],
            )

        # Step 2: call get_service_status on gateway
        if "get_service_status" not in prompt and self._call_index == 1:
            self._call_index += 1
            return LLMResponse(
                content="Checking status of gateway.",
                tool_calls=[{"name": "get_service_status", "arguments": {"service": "gateway"}}],
            )

        # Step 3: call get_logs
        if "get_logs" not in prompt and self._call_index == 2:
            self._call_index += 1
            return LLMResponse(
                content="Examining recent logs for errors.",
                tool_calls=[{"name": "get_logs", "arguments": {"service": "gateway", "lines": 20}}],
            )

        # Final Incident Report synthesis
        return LLMResponse(
            content="""# Incident Report: INC-10492
**Summary**: Service degradation detected in Gateway.
**Timeline**:
- 11:20:00Z: Health check failed with HTTP 500
- 11:20:05Z: Investigated logs
**Evidence**:
- Exact Log: "Fatal startup or runtime exception in core engine"
- Metric Value: gateway_requests_total{status="500"}
**Root Cause Hypothesis**: Gateway service is in a crash loop due to fatal runtime configuration exception (Confidence: 95%).
**Recommended Remediation**: restart gateway
"""
        )

class HostedLLMClient(BaseLLMClient):
    """Client for free-tier hosted APIs (Gemini, Groq, OpenRouter)."""

    def __init__(self, provider: str, api_key: str, model: str = "default", **kwargs):
        super().__init__(**kwargs)
        self.provider = provider
        self.api_key = api_key
        self.model = model

    async def _generate(self, prompt: str, tools: list[dict[str, Any]] | None = None) -> LLMResponse:
        # Standard free-tier unified adapter
        if self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            gemini_payload: dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=gemini_payload)
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return LLMResponse(content=text)

        # Groq / OpenRouter OpenAI-compatible endpoint
        base_urls = {
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        }
        url = base_urls.get(self.provider, base_urls["groq"])
        headers = {"Authorization": f"Bearer {self.api_key}"}
        openai_payload: dict[str, Any] = {
            "model": self.model if self.model != "default" else "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=openai_payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return LLMResponse(content=text)

def get_llm_client() -> BaseLLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        from apps.api.app.llm.dynamic_client import DynamicScriptedLLMClient
        return DynamicScriptedLLMClient()
    if provider in ["gemini", "groq", "openrouter"]:
        key_var = f"{provider.upper()}_API_KEY"
        key = os.getenv(key_var, "")
        model = os.getenv("LLM_MODEL", "default")
        return HostedLLMClient(provider=provider, api_key=key, model=model)
    return MockLLMClient()
