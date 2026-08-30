# The Governed Work Package contract

A Work Package is BADF's **bounded execution contract** — it *grants bounded execution authority*. Its
canonical form (the fields WP-IMP-B adds to the schema as optional governed properties, then WP-IMP-C
enforces with code controls):

```yaml
id: WP-2026-NNNN
demand: BADF-DEM-NNNN
objective: one measurable delivery outcome

source_baselines:            # IMP-I02: exact upstream inputs
  requirements: <digest/ref>
  architecture: <digest/ref>
  solution: <digest/ref>
  security: <digest/ref>

scope: { in: [...], out: [...] }
expected_surfaces:           # IMP-I08: what may change
  files: [...]; services: [...]; interfaces: [...]; data: [...]
acceptance: { criteria: [AC-...] }   # IMP-I03

change_class: C2             # authority DERIVED from this (IMP-I07), never chosen
authority_requirement:
  derived_from: C2
  required_roles: [...]      # from the authority matrix
risk_factors: [...]

dependencies:                # IMP-I05/I06
  blocked_by: [WP-...]
  composition_after: [WP-...]

test_obligations: [{ id: TEST-..., claim: AC-..., level: unit }]   # IMP-I09
evidence_obligations: [source-change, build, unit-test, documentation]  # IMP-I10

execution_budget: { max_attempts: 3, max_elapsed_minutes: 120, max_cost: <policy> }  # IMP-I11
stop_conditions: [AUTHORITY_CONFLICT, BASELINE_STALE, CREDENTIAL_EXPOSURE, ...]        # IMP-I12
rollback: { reversible: true, method: revert via governed PR }                        # IMP-I13
```

**Task ≠ Work Package.** A task is an execution step *inside* a WP. A WP is independently reviewable,
verifiable, and (where possible) reversible, with bounded authority and bounded blast radius.
