# Security

## Threat model and controls

- Requirement and document text is untrusted and delimited in model messages.
- Documents cannot redefine tool or system policy.
- No general-purpose shell tool is exposed. Fixed actions map to fixed argument arrays.
- Generated paths are resolved beneath one approved directory; traversal is rejected.
- Static code policy blocks sleeps, XPath, hard-coded passwords, focused/skipped tests, and process execution.
- Execution requires schema-valid code, validation status, human approval, and matching artifact hash.
- JWT-protected operations enforce role and project/tenant scope.
- Secrets come from environment variables and are masked before logs/audit.
- Containers run non-root, read-only, without Linux capabilities, and with no-new-privileges.

The local demo password and signing secret must be changed before shared use. Production should use managed secrets, OIDC/Entra ID, short-lived access tokens, TLS, database encryption/backup, network policy, dependency scanning, signed images, and central audit retention.

Report vulnerabilities according to [SECURITY.md](../SECURITY.md). Do not include credentials in reports.

