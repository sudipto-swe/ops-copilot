# [SYNTHETIC] Runbook: CoreDNS Internal Resolution Failures
**Service**: gateway
**Symptoms**: Microservices fail to resolve internal DNS names (e.g., orders:8002).
**Triage**: Check CoreDNS pod status, upstream forwarders, and network policies.
**Remediation**: Restart CoreDNS deployment pods and verify kube-system routing.
**Recommended Action**: restart
