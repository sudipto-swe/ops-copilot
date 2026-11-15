import hashlib
import hmac
import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger("ops_copilot.safety")

AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl")
APPROVAL_SECRET = os.getenv("APPROVAL_SECRET", "default-ops-secret").encode()

ALLOWLISTED_ACTIONS = {"restart", "scale", "rollback"}
ALLOWLISTED_SERVICES = {"gateway", "orders", "payments"}

def redact_secrets(text: str) -> str:
    """Redacts secrets, bearer tokens, api keys, and passwords from logs."""
    clean = re.sub(r"(?i)(bearer\s+[A-Za-z0-9_\-\.]+)", "BEARER [REDACTED]", text)
    clean = re.sub(r"(?i)(password|secret|token|key)=[\"']?[^\"'\s]+", r"\1=[REDACTED]", clean)
    clean = re.sub(r"ghp_[A-Za-z0-9]{36}", "[GITHUB_TOKEN_REDACTED]", clean)
    return clean

def is_prompt_injection(text: str) -> bool:
    """Detects adversarial instruction override patterns in log lines or user inputs."""
    adversarial_patterns = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)system\s+override",
        r"(?i)disregard\s+the\s+above",
        r"(?i)format\s+c:",
        r"(?i)drop\s+table",
        r"(?i)rm\s+-rf",
        r"(?i)you\s+are\s+now\s+in\s+god\s+mode",
    ]
    for pattern in adversarial_patterns:
        if re.search(pattern, text):
            return True
    return False

def generate_approval_token(action: str, target: str, incident_id: str) -> str:
    """Generates an HMAC-SHA256 signed approval token for human-in-the-loop remediation."""
    payload = f"{action}:{target}:{incident_id}"
    return hmac.new(APPROVAL_SECRET, payload.encode(), hashlib.sha256).hexdigest()

def verify_approval_token(token: str, action: str, target: str, incident_id: str) -> bool:
    """Verifies that the remediation token was genuinely issued and untampered."""
    expected = generate_approval_token(action, target, incident_id)
    return hmac.compare_digest(token, expected)

def log_audit_event(event_type: str, details: dict[str, Any]) -> None:
    """Appends an immutable JSONL event to the audit trail."""
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        "details": details,
    }
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
