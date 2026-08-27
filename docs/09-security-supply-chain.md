# Security, Privacy, and Supply Chain

Status: **NORMATIVE**

## Baseline controls

- threat model assets, actors, boundaries, abuse cases, controls, residual risk, and owner;
- authenticate identities and authorize every object/action server-side;
- protect tenant isolation and prevent confused-deputy behavior;
- minimize data; define classification, consent/purpose, retention, deletion, residency, and access logging;
- validate input and encode output; protect against injection, SSRF, traversal, deserialization, and command execution;
- encrypt in transit and at rest using approved key management;
- use secret managers, short-lived credentials, rotation, and leak response;
- generate SBOM/provenance, pin dependencies, review licenses, scan vulnerabilities and secrets;
- secure CI identities, branch protections, artifact signing/verification, and deployment promotion;
- log security-relevant events without secrets or unnecessary personal data.

## AI/agent controls

Treat retrieved content, tool output, code comments, issues, and documents as potentially hostile instructions. Separate data from instructions, enforce tool allowlists, validate arguments, constrain egress, protect hidden prompts/credentials, test prompt injection and data exfiltration, and require human control for material external effects.

## Security release criteria

No unresolved critical vulnerability; high risks require approved, expiring acceptance. Scans must bind to the released artifact. Penetration scope and non-coverage must be explicit. Incident response, credential revocation, rollback, and forensic retention must be ready before production.

