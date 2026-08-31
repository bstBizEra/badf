---
name: badf-uat
description: >-
  G10 business-acceptance router. Takes the exact G09-validated candidate and
  records whether its observed behavior satisfies the business outcome the PRD
  and acceptance criteria approved — never whether a screen renders or a
  Playwright script completes. Derives scenarios from the existing PRD → OBJ →
  AC → REQ chain, executes them through adapters (browser/API/manual/hybrid,
  none registered as subskills yet), classifies failures, computes coverage
  against acceptance criteria (never screens), and packages a recommendation.
  Final product acceptance stays a separate human decision. Use when a G09
  release-validated candidate needs its business behavior recorded against
  approved acceptance criteria. Grants no acceptance, approval, or gate
  authority.
status: DESIGNED
gate: G10
owner_role: release_authority
allowed_tools: []
---

# badf-uat — the G10 business-acceptance router

`badf-uat` produces exactly one of G10's four evidence types: `uat`. It does not produce
`release-packet` or `operational-readiness` (`badf-production-readiness`'s — WP-PRDY-A) and
it does not issue `go-no-go` (`release_authority`'s own act). The skill's admission status is
recorded in `badf/skill-registry.json`; this file defines behavior and must not hardcode a
lifecycle status that can drift from the registry.

## Fundamental rule

```text
TECHNICAL E2E VERIFICATION ≠ USER ACCEPTANCE

E2E asks:  "Does the system technically complete the flow?"
UAT asks:  "Does this exact behavior satisfy the business outcome that was approved?"

SCENARIO ≠ PROCEDURE
AUTOMATION ESTABLISHES OBSERVATION, NOT ACCEPTANCE
```

## The chain this skill walks, and does not re-derive

```text
PRD
 └── Product Objective          OBJ-...      (schemas/prd.schema.json)
      └── Acceptance Criterion  AC-...       (schemas/acceptance-criteria.schema.json, binds prd_id)
           └── Requirement      REQ-...      (schemas/requirements.schema.json)
                └── UAT Scenario  UAT-SCN-...
                     └── Execution → Observed Evidence → Scenario Disposition
                          └── Business Acceptance Disposition → G10 `uat` evidence
```

`schemas/traceability.schema.json` **already** carries `requirement_to_objective` and
`criterion_to_requirement` — this skill resolves those existing RTM links; it does not build a
second traceability mechanism (the same "resolve, don't reperform" discipline
`badf-release-validation` and `badf-production-readiness` hold at G09/G10).

## Boundary

```text
badf-release-validation (G09)   independently validates the implementation (quality/security/performance/resilience)
badf-uat (G10, this skill)      records whether the exact candidate's BUSINESS BEHAVIOR satisfies approved intent
badf-production-readiness (G10) release-packet + operational-readiness (the other two G10 types)
release_authority                go-no-go; the human product-acceptance decision this skill's dossier feeds
BADF gate                        evaluates evidence
```

```text
G09 — Independent validation:  quality-validation · security-validation · performance-test · resilience-test
G10 — UAT & release readiness: uat · release-packet · operational-readiness · go-no-go
```

## Authority split

```text
Agent judgment MAY derive scenarios from the approved AC/REQ chain, select an execution adapter,
observe behavior, classify a failure, and compute coverage.

Agent judgment MUST NOT issue final product acceptance. Automation establishes observed scenario
outcomes; it does not establish that the business accepts the product (mirrors SEC-I13's
security-approval reservation and VER-I18's admission reservation, extended here to product
acceptance under a human-reserved role).
```

## Workflow

```text
RESOLVE ACCEPTANCE BASIS → DERIVE SCENARIOS → SELECT ADAPTER → EXECUTE →
CLASSIFY DEFECTS → COMPUTE COVERAGE → PACKAGE RECOMMENDATION → HANDOFF TO HUMAN ACCEPTANCE
```

1. **RESOLVE ACCEPTANCE BASIS** — bind the exact PRD, acceptance-criteria and RTM baselines this
   candidate is being measured against. No approved basis → **NO UAT**. See `references/acceptance-provenance.md`.
2. **DERIVE SCENARIOS** — deterministically, from AC/REQ, criticality-aware. A scenario the RTM
   cannot anchor is not derived. See `references/scenario-derivation.md`, `references/scenario-contract.md`.
3. **SELECT ADAPTER** — browser, API, manual, or hybrid; an adapter observes, it never decides.
   See `references/execution-adapters.md`.
4. **EXECUTE** — against a business-representative environment with declared test-data provenance.
   See `references/environment-and-data-fidelity.md`.
5. **CLASSIFY DEFECTS** — a failure is one of ten explicit classes; `ACCEPTANCE_CRITERION_DEFECT`
   routes upstream, it is not silently absorbed as an implementation bug. See
   `references/defect-classification.md`.
6. **COMPUTE COVERAGE** — against acceptance criteria, roles, and critical journeys — never
   screens. See `references/coverage-matrix.md`.
7. **PACKAGE RECOMMENDATION** — the two-layer artifact: scenario evidence + a *recommendation*,
   never a self-issued acceptance. See `references/acceptance-disposition.md`.
8. **HANDOFF TO HUMAN ACCEPTANCE** — the authorized human product/business principal issues
   `ACCEPTED` / `ACCEPTED_WITH_CONDITIONS` / `REJECTED`, binding the exact candidate, scenario
   set, results, and conditions. A later candidate change stales it. See
   `references/acceptance-disposition.md`, `references/reuat-and-staleness.md`.

## Invariants (frozen)

```text
UAT-I01 — Business provenance
Every UAT scenario traces to an approved PRD objective, acceptance criterion and applicable requirement.

UAT-I02 — Scenario ≠ procedure
Business scenario identity is independent from its browser/API/manual execution implementation.

UAT-I03 — Technical E2E ≠ UAT
Technical journey success cannot satisfy UAT without business acceptance provenance.

UAT-I04 — Exact candidate
Every UAT observation binds the immutable candidate being accepted.

UAT-I05 — Exact acceptance basis
The UAT run binds the exact PRD, acceptance-criteria and RTM baselines.

UAT-I06 — Business-readable oracle
Expected outcomes are stated as observable business results, not implementation details.

UAT-I07 — Representative actor
Each scenario identifies the intended business/user role.

UAT-I08 — Representative context
Environment, permissions, business rules and test data needed for the scenario are declared.

UAT-I09 — Tool output is observation
Browser/API automation may establish observed behavior but cannot declare business acceptance.

UAT-I10 — Diagnostics ≠ acceptance
Console/network/a11y/i18n checks supplement UAT but do not replace the business oracle.

UAT-I11 — Failure class explicit
A failed scenario distinguishes implementation, requirement, design, environment, test-data and acceptance defects.

UAT-I12 — Non-coverage mandatory
Material business scenarios, roles or conditions not exercised are declared.

UAT-I13 — Criticality-aware completion
Mandatory critical acceptance criteria cannot be hidden by an aggregate pass percentage.

UAT-I14 — Acceptance authority separate
The UAT skill cannot issue final product acceptance.

UAT-I15 — Human final acceptance
Where current BADF policy applies, final product acceptance is issued only by the authorized human principal.

UAT-I16 — Acceptance binds evidence
Acceptance binds exact candidate, scenario-set, results, known defects, conditions and non-coverage.

UAT-I17 — Candidate change invalidates acceptance
A material candidate change requires impact analysis and appropriate re-UAT.

UAT-I18 — UAT ≠ go-no-go
Accepted product behavior cannot self-authorize the G10 go/no-go.

UAT-I19 — G10 ≠ deployment
G10 success cannot itself deploy the product.

UAT-I20 — No second gate
No competing scripts/badf_uat.py gate authority; deterministic G10/UAT semantics remain in the canonical BADF gate.
```

## Doctrine

```text
Technical E2E verification does not establish User Acceptance.
BADF UAT begins from approved product intent, not from the application's screen inventory.
Every UAT scenario traces to an approved business acceptance criterion and requirement.
Browser, API, mobile and human-guided procedures are execution adapters, not acceptance authorities.
Automation establishes observable behavior.
The UAT capability records scenario evidence, defects, non-coverage and an acceptance recommendation.
Final product acceptance remains a separate authorized human decision under current BADF policy.
UAT acceptance binds the exact candidate, exact acceptance basis, exact scenario set,
exact observations and known conditions.
Passing UAT does not authorize release.
G10 release readiness and go/no-go remain separate.
The BADF gate validates the evidence. Authority decides progression.
```

## References

- `references/g10-uat-contract.md` — the single evidence type this skill owns; boundary vs `badf-production-readiness` and `release_authority`.
- `references/acceptance-provenance.md` — the PRD→OBJ→AC→REQ→scenario chain, reusing the existing RTM link maps.
- `references/scenario-contract.md` — the business-readable scenario object: source refs, actor, preconditions, expected business outcomes.
- `references/scenario-derivation.md` — deterministic, criticality-aware derivation; an unanchored scenario is not derived.
- `references/execution-adapters.md` — browser/API/manual/hybrid as adapters; none registered as subskills at this rung.
- `references/environment-and-data-fidelity.md` — business-representative environment; declared test-data provenance/epoch.
- `references/diagnostics-vs-oracle.md` — technical diagnostics supplement, never replace, the business oracle.
- `references/defect-classification.md` — the ten-way failure taxonomy; `ACCEPTANCE_CRITERION_DEFECT` routes upstream.
- `references/coverage-matrix.md` — AC/RTM/role/journey coverage, never screen coverage.
- `references/acceptance-disposition.md` — the two-layer artifact: recommendation vs. human acceptance.
- `references/reuat-and-staleness.md` — candidate/scenario/acceptance digest binding; staleness on change.
- `references/g09-g10-g11-boundary.md` — UAT ≠ go-no-go ≠ deployment.
- `references/acceptance.md` — the admission ladder UAT-A…E.
- `references/external-methodology.md` — `webapp-uat`: adapted, rejected, never authority.
