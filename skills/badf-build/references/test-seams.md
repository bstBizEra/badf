# Test seams come from G06 — the build does not invent its test surface

The source methodology asks the human to agree test seams. BADF has a better answer: the G06
`test-plan` identifies them. `badf-build` **consumes** a test obligation:

```yaml
test_obligation:
  id: TEST-031
  acceptance_ref: AC-021
  seam:
    type: api
    ref: API-017
  behavior:
    given: ...
    when: ...
    then: ...
  required_phase:
    - red
    - green
```

The build agent then writes tests at *that* seam (BLD-I06), through the public interface it names,
never against implementation details.

## When implementation reveals the planned seam is invalid

```text
TEST_PLAN_DEFECT
        ↓
do not silently move the seam
        ↓
G06 amendment / bounded ruling
```

depending on materiality: a bounded ruling inside granted scope may pick between two declared seams;
choosing a seam the plan never declared, or dropping a red phase the plan required, is a G06 amendment
and returns upstream.

## Seam discipline (adapted)

- test behavior through public interfaces; don't test internals;
- establish the seam before writing tests;
- one vertical slice at a time; red before green;
- avoid tautological tests; don't bulk-write speculative tests.
