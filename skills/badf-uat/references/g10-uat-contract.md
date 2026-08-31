# The contract — `uat` is the only evidence type this skill produces

`badf/lifecycle.json` G10 (`UAT and Release Readiness`, owner `release_authority`) requires four
evidence types: `uat, release-packet, operational-readiness, go-no-go`. `badf-uat` produces exactly
one — `uat`. It never produces `release-packet` or `operational-readiness` (`badf-production-readiness`
— WP-PRDY-A, issue #237) and it never issues `go-no-go` (`release_authority`'s own act, human-reserved
per `badf/authority-matrix.json`).

## What `uat` evidence must carry

```text
uat evidence =
  candidate digest (exact G09-validated build)
  acceptance basis (exact PRD / acceptance-criteria / RTM digests)
  scenario set (derived, source-referenced)
  execution results (per scenario: PASS / FAIL / BLOCKED / NOT_EXECUTED, with adapter + observation)
  defect classification (per failure)
  coverage matrix (criteria / roles / journeys, with declared non-coverage)
  recommendation (not an acceptance) + human acceptance record, once issued
```

A `uat` record missing the acceptance-basis digest is not evidence of business acceptance — it is
evidence that something ran. UAT-I01, UAT-I04, UAT-I05.

## What this skill does NOT own

- The release packet, deployment plan, or rollback plan — `badf-production-readiness`.
- Operational readiness (observability, support runbooks, on-call) — `badf-production-readiness`.
- The go/no-go decision — `release_authority`, human, out of any skill's authority.
- Independent technical validation (quality/security/performance/resilience) — `badf-release-validation`
  at G09, already landed upstream of this gate.
- A second gate authority — the canonical BADF gate (`scripts/badf_gate.py`) remains the sole
  deterministic evaluator of any evidence this skill produces. UAT-I20.
