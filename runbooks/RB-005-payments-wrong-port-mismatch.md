# [SYNTHETIC] Runbook: Payments Wrong Port / Connection Refused
**Service**: payments
**Symptoms**: Gateway reports 502 Bad Gateway to payment backend, log 'Connection refused: payment backend failed to bind on internal port'.
**Triage**: Verify service target port configuration in deployment manifests vs Dockerfile EXPOSE.
**Remediation**: Rollback to the previous deployment revision with the correct port configuration.
**Recommended Action**: rollback
