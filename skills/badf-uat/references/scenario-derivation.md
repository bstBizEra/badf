# Scenario derivation — deterministic, criticality-aware, never invented

UAT-I01, UAT-I13. A scenario the RTM cannot anchor is not derived — it is authored, and authored
scenarios are out of this skill's contract at any rung.

## Derivation rule

For every `AC-...` bound to the candidate's approved PRD (via `criterion_to_requirement` and
`requirement_to_objective`):

1. Resolve the requirement(s) it traces to.
2. Resolve the objective it ultimately serves.
3. Emit one or more `UAT-SCN-...` objects whose `expected_business_outcome` is a direct, business-readable
   restatement of the acceptance criterion — not a paraphrase that drifts from it.
4. Carry the criterion's declared criticality onto the scenario; do not flatten it to a single default.

## Criticality-aware completion (UAT-I13)

An aggregate pass percentage cannot substitute for explicit accounting of every `critical`-tier scenario.
A dossier that reports "94% pass" while a critical scenario is `FAIL` or `NOT_EXECUTED` is not complete —
critical-tier results are always enumerated individually in the disposition, never folded into the
aggregate alone.

## Non-derivation is a declared gap, not a silent omission (UAT-I12)

An acceptance criterion with no derivable scenario (ambiguous, or requiring a business judgment this
skill cannot automate) is listed under non-coverage (`references/coverage-matrix.md`) — never dropped.
