# [SYNTHETIC] Runbook: Redis Cache Memory Eviction Spike
**Service**: gateway
**Symptoms**: Increased response times for product catalog, Redis maxmemory reached.
**Triage**: Inspect Redis memory info and eviction policy (volatile-lru vs allkeys-lru).
**Remediation**: Scale Redis memory capacity or flush stale temporary session keys.
**Recommended Action**: scale
