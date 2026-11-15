# [SYNTHETIC] Runbook: Envoy Sidecar Outlier Ejection
**Service**: payments
**Symptoms**: Envoy proxies consecutive 5xx errors and ejects payments backend hosts from cluster.
**Triage**: Check Envoy cluster stats and healthy endpoints count.
**Remediation**: Verify payment host health and trigger warm restart of sidecar proxy.
**Recommended Action**: restart
