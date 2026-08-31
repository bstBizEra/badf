---
name: badf-release-validation
description: >-
  G09 independent pre-release validation orchestrator. Routes a G08-verified
  candidate through independent quality, security, performance and resilience
  validation classes, binds each to the exact candidate under pre-existing
  thresholds and an out-of-agent oracle, and normalizes the result into the four
  G09 evidence types the lifecycle already names. It establishes pre-release
  validation evidence — it does NOT establish UAT, operational readiness, or
  release authority. G09 is quality_authority-owned; G10 (release readiness /
  go-no-go) stays release_authority-owned and untouched.
status: IMPLEMENTED
gate: G09
owner_role: quality_authority
allowed_tools: []
---

# badf-release-validation — the G09 independent pre-release validation router

`badf-release-validation` is a **G09 validation obligation router**, not "one QA agent
that tests everything" and not a G10 go/no-go authority. It takes the **exact** candidate
that G08 verified and attempts to **break and disqualify** it across four independent
validation classes — **quality, security, performance, resilience** — then normalizes the
observed evidence into the four G09 evidence types the lifecycle already owns:
`quality-validation` · `security-validation` · `performance-test` · `resilience-test`.

It composes those existing types. **It does not add a fifth `release-validation` lifecycle
evidence type, a `scripts/badf_release_validation.py`, a schema, or a `lifecycle.json`
change** — the deterministic G09 semantics live inside the canonical `badf_gate.py`
(delivered at WP-VAL-C), never in a competing validator (**VAL-I20**).

## The lifecycle boundary this capability defends

```
G08 Engineering Verification        →  independent-review · integration-test ·
                                        contract-test · composed-tree-test
G09 Independent Quality & Security   →  quality-validation · security-validation ·
    Validation  (quality_authority)     performance-test · resilience-test
G10 UAT & Release Readiness          →  uat · release-packet ·
    (release_authority)                 operational-readiness · go-no-go
G11 Deployment & Change Control
G12 Production Verification
```

`badf-release-validation` authors **G09 only**. It never issues UAT, release readiness,
go/no-go, deployment or production claims. **Authority decides progression; the BADF gate
validates evidence.**

## Core doctrine (frozen)

- A validation agent may decide **what to investigate**.
- A deterministic runtime establishes **what actually happened**.
- A validation class establishes evidence **only for its own risk domain**.
- **No single class may impersonate another.**
- **No collection of passing validation classes grants release authority.**

## Architecture — a risk-routed evidence federation

```
              EXACT G08-VERIFIED CANDIDATE
                          │
                          ▼
            VALIDATION OBLIGATION ROUTER   (derives required classes from
                          │                 risk / surfaces / NFRs / threat
        ┌───────────┬─────┴─────┬───────────┐   model / change class)
        ▼           ▼           ▼           ▼
     QUALITY    SECURITY   PERFORMANCE  RESILIENCE     (each: own hypothesis,
        │           │           │           │          method, ORACLE, identity,
        └────► DETERMINISTIC OBSERVATION ◄───┘          runtime result, non-coverage)
                          │
                          ▼
                EVIDENCE NORMALIZATION
                          │
                          ▼
   quality-validation · security-validation · performance-test · resilience-test
                          │
                          ▼
                    G09 DOSSIER  (conjunctive)
                          │
                          ▼
                 canonical BADF gate  →  quality_authority
                          │
                    G09 PASS only
                          ▼
                 G10 release readiness  (release_authority owns this)
```

## Routing is risk-derived, not "run all QA"

The router derives a **validation obligation set** from G02–G08 evidence, the Work
Package / change class, changed surfaces, threat model, NFRs and the release candidate —
and may mark each obligation `REQUIRED` / `NOT_APPLICABLE` / `DEFERRED_WITH_REASON`
(**VAL-I02**). An agent cannot silently weaken a required class. See
[references/routing.md](references/routing.md) and
[references/validation-obligations.md](references/validation-obligations.md).

## The four classes (each a class-aggregator, not one test)

- **`quality-validation`** — normalized functional/non-functional quality evidence
  (E2E/exploratory, cross-browser, accessibility, DB/migration, visual, AI evals, payment/
  email flows). Each runtime observation needs a **stable oracle outside the agent** — an
  agent may *attempt* a journey; a deterministic oracle establishes success (order_id
  exists, sandbox reports success, inventory mutation matches, no forbidden state), never
  "it looked successful". See [references/quality-validation.md](references/quality-validation.md).
- **`security-validation`** — independent attack-oriented / security-control evidence,
  preferably routed through the future `badf-security-assurance`; OWASP is the primary
  methodology, scanners are observation producers. **A security finding is not an accepted
  risk** (**VAL-I09**). See [references/security-validation.md](references/security-validation.md).
- **`performance-test`** — SLO/budget-backed observations with exact workload + environment
  provenance; a metric without a bound SLO is a *measurement*, not a PASS (**VAL-I10**);
  routes the workload family (smoke/average/stress/spike/soak/breakpoint). See
  [references/performance-test.md](references/performance-test.md).
- **`resilience-test`** — hypothesis-driven fault/recovery validation with steady state,
  bounded blast radius, executable abort conditions, and **observed recovery + integrity**,
  not mere survival (**VAL-I11/I12**). See [references/resilience-test.md](references/resilience-test.md).

## Class independence (stronger than G08 reviewer independence)

Each class has its own **risk hypothesis · method · oracle · execution identity · runtime
result · non-coverage**. Classes may share infrastructure, but **one result cannot be
copied into several required evidence slots** (**VAL-I03/I13**): a k6 average-load run is a
`performance-test`, not also a `resilience-test`; a Semgrep-green is one security
observation, not `security-validation` complete. See
[references/class-independence.md](references/class-independence.md).

## Candidate binding — inherit G08's strongest controls, raise the bar

G08 asks *is the engineered change internally coherent and correct on the composed
result?* G09 asks *does that exact composed candidate withstand independent risk-based
validation under representative conditions?* Every G09 artifact binds the **same** source
revision · composed content tree · build artifact digest(s) · configuration/environment
identity · validation policy epoch (**VAL-I01**). If any mandatory class tested a different
candidate → `MIXED_CANDIDATE_EVIDENCE` → REFUSE. See
[references/candidate-binding.md](references/candidate-binding.md).

## Thresholds, oracles, runtime evidence

Acceptance thresholds (security, performance, resilience, quality) are **bound before
results are interpreted** (**VAL-I06**); a claim earns no validation credit without an
approved observed runtime where the claim is mechanically observable (**VAL-I04**);
agent-authored scenarios/findings/interpretations are **draft until validated and bound**
(**VAL-I05**). See [references/runtime-evidence.md](references/runtime-evidence.md) and
[references/thresholds-and-oracles.md](references/thresholds-and-oracles.md).

## Environment fidelity is first-class

Every runtime result binds environment identity, configuration, fixtures, toolchain and
observation time (**VAL-I07**); a non-production environment **states its material
deviations** from production, so `staging PASS ≠ production proven` becomes declared
non-coverage, not forgotten context (**VAL-I08**). See
[references/environment-fidelity.md](references/environment-fidelity.md).

## The G09 dossier is conjunctive

```
G09_PASS = candidate_identity_consistent AND required_validation_classes_present
  AND class_independence_valid AND quality_thresholds_satisfied
  AND security_thresholds_satisfied AND performance_budgets_satisfied
  AND resilience_obligations_satisfied AND blocking_findings_resolved
  AND runtime_evidence_valid AND noncoverage_declared AND evidence_current
```

Not "3 of 4 passed → majority PASS". A security blocker cannot be outvoted by performance
and QA (**VAL-I14**). Normalization cannot erase/downgrade/silently accept blocking
evidence; rerun-until-green cannot erase a failed observation (**VAL-I16**); every class
names material surfaces it did not establish (**VAL-I15**). See
[references/findings-and-disposition.md](references/findings-and-disposition.md) and
[references/noncoverage.md](references/noncoverage.md).

## Invariants (VAL-I01…VAL-I20)

- **VAL-I01 Exact candidate** — all G09 validation binds the exact same immutable candidate / composed result.
- **VAL-I02 Risk-derived routing** — required classes derive from declared risk, surface, NFRs, security obligations and change class; an agent cannot weaken them ad hoc.
- **VAL-I03 Class independence** — quality, security, performance and resilience retain distinct hypotheses, oracles and evidence.
- **VAL-I04 Runtime observation** — claims receive no validation credit without approved observed execution where the claim is mechanically observable.
- **VAL-I05 Agent output is draft** — agent-authored scenarios, findings and interpretations are non-canonical until validated and bound.
- **VAL-I06 Thresholds pre-exist outcomes** — security, performance, resilience and quality acceptance thresholds are bound before results are interpreted.
- **VAL-I07 Environment provenance** — every runtime result binds environment identity, configuration, fixtures, toolchain and observation time.
- **VAL-I08 Environment deviation declared** — a non-production validation environment explicitly states material differences from production.
- **VAL-I09 Security validation ≠ risk acceptance** — no security validator may waive or accept its own discovered residual risk.
- **VAL-I10 Performance measurement ≠ conformance** — a metric without a bound SLO/budget cannot establish PASS.
- **VAL-I11 Resilience is hypothesis-driven** — fault injection requires steady state, expected behavior, bounded blast radius and executable abort conditions.
- **VAL-I12 Recovery observed** — resilience PASS requires observed recovery and relevant integrity checks, not merely survival during injection.
- **VAL-I13 No class substitution** — evidence from one validation class cannot silently satisfy another.
- **VAL-I14 Blocking findings preserved** — normalization cannot erase, downgrade or silently accept blocking evidence.
- **VAL-I15 Non-coverage mandatory** — every validation class names material surfaces it did not establish.
- **VAL-I16 Flake policy explicit** — rerun-until-green cannot erase a failed validation observation.
- **VAL-I17 G08 ≠ G09** — engineering verification evidence cannot substitute for independent risk-based release validation.
- **VAL-I18 G09 ≠ G10** — a G09 validation result cannot issue UAT, release readiness or go/no-go.
- **VAL-I19 G09 ≠ G12** — pre-release testing cannot claim production success.
- **VAL-I20 No second gate** — no competing `badf_release_validation.py` authority; deterministic G09 semantics stay inside the canonical BADF gate.

## Workflow

`FRAME → BIND_CANDIDATE → ROUTE (derive validation obligations) → CLASS_VALIDATE (quality ·
security · performance · resilience, each with its own oracle + approved runtime) →
OBSERVE (deterministic runtime facts) → THRESHOLD (bound before interpretation) →
NORMALIZE (into the four G09 evidence types) → DECLARE_NONCOVERAGE → COMPOSE (conjunctive
G09 dossier) → HANDOFF (canonical gate → quality_authority).` The capability stops at G09
evidence; **quality_authority decides G09 PASS, and only then does G10 own release
readiness.**

## External methodology — adapt, not authority

- `petrkindlmann/qa-skills` → validation-method **taxonomy + adapter catalog** (risk
  routing, E2E, accessibility, DB/migration, chaos). Its `release-readiness` skill is
  **G10**, not G09 — adopt its evidence/check patterns, never its decision authority.
- Grafana `k6` skills → **performance methodology** (SLO-backed thresholds, workload
  classes, load-generator monitoring, immutable run investigation).
- OWASP Secure Agent Playbook → **primary security methodology**.
- Individual scanners/test tools → **observation producers, never authority**.

See [references/external-methodology.md](references/external-methodology.md). Full contract:
[references/g09-contract.md](references/g09-contract.md); boundary:
[references/g08-g09-g10-boundary.md](references/g08-g09-g10-boundary.md); acceptance:
[references/acceptance.md](references/acceptance.md).

## Delivery ladder

WP-VAL-A contract freeze (**DESIGNED**, this WP) → WP-VAL-B typed G09 evidence contracts
(IMPLEMENTED) → WP-VAL-C canonical deterministic controls (VALIDATED) → WP-VAL-D
representative/historical validation shadow (SHADOWED) → WP-VAL-E quality_authority/operator
admission (ACTIVE). ACTIVE grants no new authority; the human/quality_authority gates hold.
