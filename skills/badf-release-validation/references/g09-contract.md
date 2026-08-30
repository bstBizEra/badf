# g09-contract.md — the full G09 independent pre-release validation contract

`badf-release-validation` authors **G09 evidence and G09 evidence only**. It is a
**validation obligation router** over four independent risk classes, not a QA
mega-agent and not a release authority. This file is the normative contract; siblings
[candidate-binding.md](candidate-binding.md), [routing.md](routing.md),
[validation-obligations.md](validation-obligations.md) and
[class-independence.md](class-independence.md) expand its clauses.

## Purpose

Take the **exact G08-verified candidate** and attempt to **break and disqualify** it
under independent, risk-derived validation across representative conditions. G09 asks a
different question than G08: G08 established the change is internally coherent and correct
on the composed result; G09 establishes whether *that exact composed candidate* withstands
independent quality, security, performance and resilience validation (**VAL-I01**,
**VAL-I17**). It produces pre-release validation evidence — nothing more.

## What G09 owns

- The four G09 evidence types the lifecycle **already** names, composed (never replaced):
  `quality-validation` · `security-validation` · `performance-test` · `resilience-test`.
- The **risk-derived routing** that decides which classes are `REQUIRED` for this candidate
  (**VAL-I02**), and the conjunctive G09 dossier that federates their results.
- `quality_authority` ownership of the G09 verdict.

## What G09 must NOT do

- No UAT, no operational-readiness, no release-readiness, no go/no-go, no deployment, no
  production-success claim — those are **G10+** and stay `release_authority`-owned
  (**VAL-I18**, **VAL-I19**). Authority decides progression; the gate validates evidence.
- No **fifth** lifecycle evidence type, no `scripts/badf_release_validation.py`, no schema,
  no `lifecycle.json` change. Deterministic G09 semantics live in the canonical
  `badf_gate.py` at a later rung — there is **no second gate** (**VAL-I20**).
- No class impersonating another, no result copied across evidence slots (**VAL-I03/I13**).

## The four evidence types it composes

Each is a **class-aggregator** with its own risk hypothesis, method, oracle-outside-the-agent,
execution identity, runtime result and declared non-coverage (**VAL-I03**, **VAL-I04**,
**VAL-I15**). No class establishes evidence outside its own risk domain.

| Evidence type | Establishes | Guardrail |
| :--- | :--- | :--- |
| `quality-validation` | functional/non-functional quality on the candidate | oracle outside agent, not "looked fine" |
| `security-validation` | independent attack/control evidence | a finding ≠ accepted risk (**VAL-I09**) |
| `performance-test` | SLO/budget-backed observation | a metric w/o a bound SLO is not PASS (**VAL-I10**) |
| `resilience-test` | fault/recovery under hypothesis | observed recovery, not survival (**VAL-I11/I12**) |

## The G09 dossier is conjunctive

```
G09_PASS = candidate_identity_consistent AND required_classes_present
  AND class_independence_valid AND quality_thresholds_satisfied
  AND security_thresholds_satisfied AND performance_budgets_satisfied
  AND resilience_obligations_satisfied AND blocking_findings_resolved
  AND runtime_evidence_valid AND noncoverage_declared AND evidence_current
```

Never "3 of 4 → majority PASS". A security blocker cannot be outvoted by performance and
QA; normalization cannot erase, downgrade or silently accept blocking evidence (**VAL-I14**);
rerun-until-green cannot erase a failed observation (**VAL-I16**). **No collection of
passing classes grants release authority.**

## Invariant index (VAL-I01…VAL-I20)

- **VAL-I01 Exact candidate** — all G09 validation binds the same immutable candidate.
- **VAL-I02 Risk-derived routing** — required classes derive from declared risk, not a static checklist.
- **VAL-I03 Class independence** — each class keeps distinct hypothesis, oracle and evidence.
- **VAL-I04 Runtime observation** — no validation credit without approved observed execution.
- **VAL-I05 Agent output is draft** — agent scenarios/findings are non-canonical until validated + bound.
- **VAL-I06 Thresholds pre-exist outcomes** — acceptance thresholds bound before results are interpreted.
- **VAL-I07 Environment provenance** — every runtime result binds environment, config, fixtures, toolchain, time.
- **VAL-I08 Environment deviation declared** — a non-prod environment states its material differences.
- **VAL-I09 Security validation ≠ risk acceptance** — a validator cannot waive its own residual risk.
- **VAL-I10 Performance measurement ≠ conformance** — a metric without a bound budget cannot PASS.
- **VAL-I11 Resilience is hypothesis-driven** — steady state, expected behavior, bounded blast radius, abort conditions.
- **VAL-I12 Recovery observed** — resilience PASS needs observed recovery + integrity, not survival.
- **VAL-I13 No class substitution** — one class's evidence cannot silently satisfy another.
- **VAL-I14 Blocking findings preserved** — normalization cannot erase/downgrade blocking evidence.
- **VAL-I15 Non-coverage mandatory** — every class names material surfaces it did not establish.
- **VAL-I16 Flake policy explicit** — rerun-until-green cannot erase a failed observation.
- **VAL-I17 G08 ≠ G09** — engineering verification cannot substitute for risk-based validation.
- **VAL-I18 G09 ≠ G10** — a G09 result cannot issue UAT, release readiness or go/no-go.
- **VAL-I19 G09 ≠ G12** — pre-release testing cannot claim production success.
- **VAL-I20 No second gate** — no competing validator; G09 semantics stay in the canonical gate.
