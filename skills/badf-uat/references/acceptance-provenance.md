# Acceptance provenance — reuse the RTM, do not re-derive it

`badf-uat` resolves the existing chain; it does not build a second one.

```text
schemas/prd.schema.json                 → Product Objectives (OBJ-...)
schemas/acceptance-criteria.schema.json → Acceptance Criteria (AC-...), binds prd_id
schemas/requirements.schema.json        → Requirements (REQ-...)
schemas/traceability.schema.json        → requirement_to_objective, criterion_to_requirement
                                           (the link maps this skill resolves, not rebuilds)
```

## Binding rule (UAT-I01, UAT-I05)

Before any scenario is derived, this skill resolves and records the **exact digests** of:

1. The PRD (`prd_id` + digest) this candidate's acceptance criteria trace to.
2. The acceptance-criteria document(s) (`schema_version, prd_id, criteria[]`) in force.
3. The traceability document binding `requirement_to_objective` and `criterion_to_requirement`.

No approved basis resolvable → **NO UAT**. A scenario that cannot be traced back through
`criterion_to_requirement` and `requirement_to_objective` to an approved `AC-...` and `OBJ-...` is not
a UAT scenario — it is an untraceable test, out of this skill's contract.

## What this skill adds on top of the existing chain

Only the leaf the RTM does not carry: the **UAT Scenario** (`references/scenario-contract.md`) and its
execution record. Nothing upstream of that leaf is re-specified here.
