# Coverage — acceptance criteria, roles, journeys. Never screens.

UAT-I12, UAT-I13. Technical E2E tooling often reports coverage as "screens visited" or "routes hit".
That number is not evidence of business acceptance and this skill does not compute it.

## What is measured

```text
Acceptance-criterion coverage   every AC-... bound to the candidate's PRD: derived / not-derived,
                                 executed / not-executed, PASS / FAIL / BLOCKED
Role coverage                   every actor_role named in scenarios: exercised / not-exercised
Journey coverage                critical business journeys spanning multiple criteria: complete / partial
Non-coverage (declared)         material scenarios, roles or conditions NOT exercised — with reason
```

## The non-coverage declaration (UAT-I12)

Absence from the coverage matrix is not the same as "not applicable". Every acceptance criterion bound
to the candidate's PRD appears in the matrix in one of: `covered_pass`, `covered_fail`,
`covered_blocked`, or `not_covered` (with a stated reason — ambiguous criterion, no representative
environment, deferred by explicit decision, etc.). A criterion silently missing from the matrix is the
defect this reference exists to prevent.

## Criticality is never flattened into the aggregate (UAT-I13)

A single "N/M scenarios passed" figure cannot stand alone in the disposition. Every `critical`-tier
scenario's individual result is enumerated; a critical FAIL or NOT_EXECUTED blocks the recommendation
regardless of the aggregate percentage.
