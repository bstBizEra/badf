# The UAT Scenario object — business-readable, adapter-independent

UAT-I02: scenario identity is independent from its execution implementation. A scenario is a business
statement; an adapter run is one way of observing whether it held.

```json
{
  "scenario_id": "UAT-SCN-...",
  "prd_id": "...",
  "objective_ref": "OBJ-...",
  "acceptance_criterion_ref": "AC-...",
  "requirement_refs": ["REQ-..."],
  "actor_role": "the business/user role this scenario represents (UAT-I07)",
  "preconditions": "business-representative starting state (UAT-I08)",
  "steps": "business actions, not implementation steps",
  "expected_business_outcome": "observable business result, stated without implementation detail (UAT-I06)",
  "criticality": "critical | major | minor (UAT-I13)"
}
```

## What a scenario is not

- Not a Playwright/Cypress script — that is an adapter's execution of the scenario
  (`references/execution-adapters.md`).
- Not a screen-by-screen checklist — coverage is measured against acceptance criteria and journeys, never
  screens (`references/coverage-matrix.md`).
- Not owned by this skill's runtime at WP-UAT-A — no adapter is registered yet
  (`references/acceptance.md`); this rung freezes the object's shape, not an execution engine.
