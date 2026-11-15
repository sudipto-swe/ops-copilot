# [SYNTHETIC] Runbook: Payments Gateway Circuit Breaker Open
**Service**: payments
**Symptoms**: Payment requests immediately rejected with 503 Circuit Breaker Open.
**Triage**: Check upstream payment processor status and gateway error rate thresholds.
**Remediation**: Reset circuit breaker state after validating third-party endpoint availability.
**Recommended Action**: restart
