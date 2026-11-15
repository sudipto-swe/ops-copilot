# [SYNTHETIC] Runbook: Ingress TLS Certificate Expiration
**Service**: gateway
**Symptoms**: Clients receive SEC_ERROR_EXPIRED_CERTIFICATE on HTTPS ingress endpoints.
**Triage**: Check cert-manager certificates and issuer status in ingress namespace.
**Remediation**: Trigger cert-manager renewal or reissue TLS secret.
**Recommended Action**: restart
