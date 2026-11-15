# [SYNTHETIC] Runbook: Edge Rate Limiter Dropping Legitimate Requests
**Service**: gateway
**Symptoms**: Surge in HTTP 429 Too Many Requests reported by valid client apps.
**Triage**: Review rate limit bucket configs in Redis and client IP aggregation rules.
**Remediation**: Scale rate limit token thresholds or whitelist impacted partner CIDRs.
**Recommended Action**: scale
