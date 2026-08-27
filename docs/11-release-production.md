# Release, Deployment, and Production Verification

Status: **NORMATIVE**

## Release packet

Require immutable artifact digest, source revision/result tree, SBOM/provenance, change ticket, approved dossier, migration plan, feature flags, rollout segments, monitoring queries, SLO/KPI baselines, rollback triggers and procedure, runbooks, support/comms, owners, window, and approvals.

## Deployment

- Promote the same verified artifact; do not rebuild per environment.
- Apply least-privilege deployment identity and environment separation.
- Use progressive delivery for C2/C3 where feasible.
- Define automatic and manual stop/rollback thresholds before starting.
- Record every environment transition and configuration/migration digest.
- Separate deploy permission from final production approval when required.

## Production verification

G12 requires direct evidence of availability, errors, latency, saturation, security signals, critical user journeys, data integrity, integrations, queues/jobs, and business controls. Compare against baseline and release thresholds over the prescribed observation window.

Pipeline success is not production success. If telemetry is missing or contradictory, stop progression. A rollback is a controlled outcome, not evidence to suppress.

## Emergency change

Emergency authority must be explicit and time-bounded. Minimize scope, preserve logs, run available safety checks, require real-time owner approval, and complete retrospective review, evidence reconstruction, and permanent remediation within the defined SLA.

