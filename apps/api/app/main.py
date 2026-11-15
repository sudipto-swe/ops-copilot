import logging

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from apps.api.app.agent.ops_agent import OpsAgent
from apps.api.app.llm.client import get_llm_client
from apps.api.app.mcp_server.server import MCPServer
from scripts.inject_fault import inject

logger = logging.getLogger("ops_copilot.api")

class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    llm_provider: str = "mock"
    audit_log_path: str = "logs/audit.jsonl"
    dry_run_default: bool = True
    approval_secret: str = "default-ops-secret"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

app = FastAPI(title="Ops Copilot API", version="0.1.0")

class TriageRequest(BaseModel):
    scenario: str
    alert: str | None = None

@app.get("/health")
async def health():
    return {"status": "ok", "app": "ops-copilot-api"}

@app.get("/ready")
async def ready():
    return {"ready": True}

@app.post("/api/v1/triage")
async def triage_endpoint(req: TriageRequest):
    if req.scenario:
        try:
            inject(req.scenario)
        except (ValueError, RuntimeError) as exc:
            logger.warning(f"Could not inject scenario: {exc}")

    alert_text = req.alert or f"Incident alert triggered for scenario: {req.scenario}"
    llm = get_llm_client()
    mcp = MCPServer()
    agent = OpsAgent(llm_client=llm, mcp_server=mcp, max_steps=6)
    result = await agent.investigate(alert_text)
    return result
