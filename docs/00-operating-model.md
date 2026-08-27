# BADF Operating Model

Status: **NORMATIVE**

## Purpose and boundaries

BADF governs delivery; it does not replace product ownership, engineering judgment, security accountability, or production ownership. It converts authority and intent into controlled work, requires evidence at decision boundaries, and maintains traceability from requirement to runtime outcome.

## Systems of record

| Record | Canonical system | Repository representation |
| --- | --- | --- |
| Authority, assignment, status | Approved work-management system | Work-package ID and signed/exported receipt |
| Source, policy, contracts, decisions | Git | Commits, protected branches, tags, PRs |
| Build and verification | CI/CD | Run ID, immutable logs, attestations, digests |
| Release and deployment | Deployment platform | Release ID, environment, artifact digest |
| Runtime health | Observability/incident platform | SLO window, dashboard/query, incident IDs |
| Durable learning | Approved knowledge system + Git | Reviewed memory/knowledge record with provenance |

Mirrors are caches and must carry source identity and freshness. Conflicts are resolved at the canonical system, never by overwriting history.

## Control planes

1. **Authority plane** — who may request, perform, approve, waive, release, and operate.
2. **Delivery plane** — requirements, design, implementation, tests, and release.
3. **Evidence plane** — provenance, checks, attestations, and gate dossiers.
4. **Runtime plane** — deployment, observability, SLOs, incidents, rollback.
5. **Learning plane** — retrospectives, patterns, memory promotion, skills and policy improvements.

## Roles

| Role | Accountable function | Prohibited combination |
| --- | --- | --- |
| Sponsor/Product Owner | Value, priority, product acceptance | Cannot waive security/compliance alone |
| Work Authority | Creates/amends work authority | Cannot fabricate evidence |
| Implementer | Produces change and author evidence | Cannot independently approve own gate |
| Reviewer/Council | Challenges specified lenses | Cannot expand task authority |
| Security/Privacy Authority | Risk acceptance and regulated controls | Must not be replaced by majority vote |
| Release Authority | Approves production change window | Cannot approve without release evidence |
| Service Owner | Accepts SLO, runbook, on-call, operational risk | Cannot erase failed runtime evidence |
| Evidence Custodian | Maintains schemas, retention, integrity | Cannot change historical evidence in place |

## Change classes

- `C0` documentation-only, no normative behavior change.
- `C1` low-risk reversible internal change.
- `C2` user-visible, contract, data, dependency, or operational change.
- `C3` security/privacy, destructive migration, authority-policy, credential, regulated, or high-blast-radius production change.

Class is the maximum severity across affected surfaces. Ambiguity selects the higher class. Approval minimums are defined in `badf/authority-matrix.json`.

## Status vocabulary

Use only: `DRAFT`, `READY`, `IN_PROGRESS`, `BLOCKED`, `REJECTED`, `APPROVED_WITH_CONDITIONS`, `APPROVED`, `SUPERSEDED`, `VERIFIED`, and `CLOSED`. A stage is not `VERIFIED` merely because artifacts exist.

## Exception contract

An exception must name the exact control, justification, owner, compensating controls, affected targets, start and expiry, approval authority, and closure evidence. Exceptions never silently renew and cannot waive legal or platform-enforced controls.

