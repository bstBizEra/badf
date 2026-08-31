---
name: badf-production-readiness
description: >-
  G10 readiness aggregator. Resolves upstream gate evidence against the exact
  immutable release candidate and evaluates twelve readiness dimensions, then
  packages a readiness dossier whose strongest positive conclusion is
  READY_FOR_AUTHORITY. It produces the release-packet and operational-readiness
  G10 evidence types; it never produces uat (badf-uat's) and never issues
  go-no-go or PRODUCTION_AUTHORIZED (release_authority's own act, human-reserved).
  Aggregation, not re-execution: it resolves the owning discipline's evidence and
  never re-performs it. Use when a G09-validated candidate needs its production
  readiness evidence assembled for an authority decision. Grants no release,
  deployment, or authorization authority.
status: DESIGNED
gate: G10
owner_role: release_authority
allowed_tools: []
---

# badf-production-readiness — the G10 readiness aggregator

`badf-production-readiness` produces two of G10's four evidence types: `release-packet` and
`operational-readiness`. It never produces `uat` (that is `badf-uat`'s, registered separately) and
it never issues `go-no-go` (`release_authority`'s own act, human-reserved in
`badf/authority-matrix.json`). The skill's admission status is recorded in
`badf/skill-registry.json`; this file defines behavior and must not hardcode a lifecycle status
that can drift from the registry.

## Three fundamental rules

```text
AGGREGATION NOT RE-EXECUTION
  Production readiness RESOLVES and EVALUATES the owning discipline's evidence.
  It never re-performs the discipline. A readiness skill that re-runs G09's tests
  has become a second validator with none of G09's independence.

READINESS ≠ AUTHORIZATION
  The strongest positive conclusion this skill can reach is READY_FOR_AUTHORITY.
  It is a recommendation, an input to a decision — never the decision.

PRODUCTION_AUTHORIZED IS DERIVED, NEVER WRITTEN
  PRODUCTION_AUTHORIZED is a derived predicate over valid evidence PLUS valid
  authority bound to an exact candidate, environment, scope and window.
  It is never a hand-written field any capability can set.
```

## Boundary

```text
badf-release-validation (G09)      produces independent validation evidence — this skill RESOLVES it, never re-performs it
badf-uat (G10)                     produces the `uat` evidence type — business acceptance, not this skill's
badf-production-readiness (G10)    release-packet + operational-readiness (this skill)
release_authority (G10, human)     go-no-go; derives PRODUCTION_AUTHORIZED — reserved, not delegable
G11 Deployment / Change Control    executes the deployment the authorization permitted
G12 Production Verification        proves the release in production
BADF gate                          evaluates evidence. Authority decides progression.
```

## Workflow

```text
BIND CANDIDATE → RESOLVE UPSTREAM EVIDENCE → COMPUTE RELEASE DELTA → CHECK FRESHNESS →
CHECK CONTRADICTIONS → EVALUATE DIMENSIONS → DECLARE NON-COVERAGE → PACKAGE DOSSIER → HANDOFF
```

1. **BIND CANDIDATE** — the exact immutable candidate: source, composed-tree, artifact, SBOM,
   provenance, config and migration digests. `references/candidate-binding.md` (PRDY-I02/I18/I23).
2. **RESOLVE UPSTREAM EVIDENCE** — resolve, never re-perform. `references/evidence-aggregation.md`
   carries the MAY / MUST NOT list (PRDY-I01).
3. **COMPUTE RELEASE DELTA** — against the currently released baseline, not the candidate in
   isolation. `references/release-delta.md` (PRDY-I03). *No diff ≠ ready.*
4. **CHECK FRESHNESS** — expired or stale mandatory evidence receives no readiness credit.
   `references/evidence-freshness.md` (PRDY-I05).
5. **CHECK CONTRADICTIONS** — contradictory mandatory evidence yields `NOT_READY` or
   `INDETERMINATE`; synthesis cannot pick the favorable claim.
   `references/contradiction-resolution.md` (PRDY-I06).
6. **EVALUATE DIMENSIONS** — the twelve dimensions, each resolved from its real owning source.
   `references/readiness-dimensions.md`.
7. **DECLARE NON-COVERAGE** — what was not evaluated, and why. Absence is declared, never implied.
8. **PACKAGE DOSSIER** — the readiness dossier; strongest positive conclusion `READY_FOR_AUTHORITY`.
9. **HANDOFF** — to `release_authority`, who derives the authorization this skill cannot issue.
   `references/authority-boundary.md` (PRDY-I19…I22).

## Invariants (frozen)

```text
PRDY-I01 — Aggregation, not re-execution
Production readiness resolves and evaluates upstream evidence;
it does not re-perform the owning validation discipline.

PRDY-I02 — Exact candidate
All mandatory readiness evidence resolves to the exact immutable
release candidate or an explicitly compatible baseline.

PRDY-I03 — Previous-release delta
Readiness evaluates material change from the currently released
baseline, not the candidate in isolation.

PRDY-I04 — Evidence provenance
Every readiness claim binds its canonical evidence source,
producer, observation time and digest.

PRDY-I05 — Freshness
Expired or stale mandatory evidence receives no readiness credit.

PRDY-I06 — Cross-artifact consistency
Contradictory mandatory evidence yields NOT_READY or
INDETERMINATE; synthesis cannot choose the favorable claim.

PRDY-I07 — Product acceptance required
Technical validation cannot substitute for business/product acceptance.

PRDY-I08 — Security validation required
A green engineering/test suite cannot substitute for applicable
security validation.

PRDY-I09 — Security risk ≠ accepted risk
Readiness cannot accept its own residual security/privacy risk.

PRDY-I10 — Performance budget bound
Performance readiness requires evidence against predeclared
capacity/SLO budgets.

PRDY-I11 — Recovery evidence
Resilience claims include actual recovery observations where applicable.

PRDY-I12 — Backup ≠ restore
A backup artifact alone cannot establish recoverability.

PRDY-I13 — Rollback executable
A rollback document alone does not establish rollback readiness.

PRDY-I14 — Migration/rollback compatibility
Migration state and rollback strategy must be mutually coherent.

PRDY-I15 — Observability actionable
Required production signals bind query, threshold, alert route,
owner and response/rollback action.

PRDY-I16 — Operations ownership
A mandatory production service cannot be READY without an
identified accountable service/on-call owner.

PRDY-I17 — Support ownership
Customer/user-impacting releases identify support and escalation ownership.

PRDY-I18 — Same artifact
The artifact authorized for production is the artifact that was
verified; no per-environment rebuild substitution.

PRDY-I19 — Readiness ≠ authorization
The readiness skill may recommend READY_FOR_AUTHORITY but cannot
grant production authority.

PRDY-I20 — Authorization exactness
Production authorization binds exact candidate, environment,
rollout scope, conditions and validity window.

PRDY-I21 — Authorization ≠ deployment
G10 production authorization does not satisfy G11 deployment/change control.

PRDY-I22 — Deployment ≠ production success
A successful deployment does not satisfy G12 production verification.

PRDY-I23 — Candidate mutation invalidates readiness
Any material candidate, configuration, migration or release-owned
artifact change invalidates the readiness dossier.

PRDY-I24 — No second gate
No scripts/badf_production_readiness.py becomes a competing
lifecycle authority; deterministic G10 semantics remain in badf_gate.py.```

## Doctrine

```text
Production readiness resolves; it does not authorize.
Its strongest positive conclusion is READY_FOR_AUTHORITY.
PRODUCTION_AUTHORIZED is derived from valid evidence plus valid authority
bound to the exact candidate, environment, scope and window.
G11 controls deployment. G12 proves the release in production.
The BADF gate validates the evidence. Authority decides progression.
```

## References

- `references/g10-contract.md` — the four G10 types; this skill's two vs `badf-uat`'s one vs `release_authority`'s own act.
- `references/readiness-dimensions.md` — the twelve dimensions, each naming its real evidence source; the bounded readiness vocabulary.
- `references/candidate-binding.md` — the exact immutable candidate (PRDY-I02/I18/I23).
- `references/release-delta.md` — previous-release-vs-candidate delta matrix (PRDY-I03); *no diff ≠ ready*.
- `references/evidence-aggregation.md` — the MAY / MUST NOT list (PRDY-I01).
- `references/evidence-freshness.md` — stale mandatory evidence earns no credit (PRDY-I05).
- `references/contradiction-resolution.md` — contradiction yields NOT_READY or INDETERMINATE (PRDY-I06).
- `references/security-readiness.md` — validation status and accepted residual risk; cannot self-accept (PRDY-I08/I09).
- `references/recovery-readiness.md` — backup ≠ restore; RPO/RTO (PRDY-I11/I12).
- `references/rollback-migration-readiness.md` — DEFINED/VALIDATED/REHEARSED; migration/rollback compatibility (PRDY-I13/I14).
- `references/observability-readiness.md` — signal → query → threshold → alert → owner → action (PRDY-I15).
- `references/operations-support-readiness.md` — service, on-call, support and escalation ownership (PRDY-I16/I17).
- `references/release-artifact-identity.md` — the same-artifact rule (PRDY-I18).
- `references/authority-boundary.md` — readiness ≠ authorization; G10 ≠ G11 ≠ G12 (PRDY-I19…I22).
- `references/acceptance.md` — the admission ladder PRDY-A…E.
- `references/external-methodology.md` — `final-release-review` and the reviewed readiness skill: ADAPT / EXTEND / REJECT.
