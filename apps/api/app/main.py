from fastapi import FastAPI
from pydantic_settings import BaseSettings


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

@app.get("/health")
async def health():
    return {"status": "ok", "app": "ops-copilot-api"}

@app.get("/ready")
async def ready():
    return {"ready": True}
