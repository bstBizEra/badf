# Defect classification — ten explicit classes, none silently absorbed

UAT-I11. A `FAIL` or `BLOCKED` result without a class is not a finding — it is noise the disposition
step cannot act on.

```text
IMPLEMENTATION_DEFECT        the built candidate does not do what was specified
REQUIREMENT_DEFECT           the requirement itself is wrong or incomplete
ACCEPTANCE_CRITERION_DEFECT  the acceptance criterion itself is wrong, ambiguous, or unsatisfiable —
                              routes UPSTREAM to PRD/AC authoring, never silently reworded here
DESIGN_DEFECT                the design does not serve the approved objective
ENVIRONMENT_DEFECT           execution context was not representative (references/environment-and-data-fidelity.md)
TEST_DATA_DEFECT             the data used could not exercise the scenario as intended
ADAPTER_DEFECT                the execution adapter itself malfunctioned, not the candidate
SCENARIO_DEFECT              the derived scenario itself is malformed or mistraced
NON_REPRODUCIBLE             observed once, not reproducible under the same declared conditions
BLOCKED_BY_DEPENDENCY         scenario cannot execute due to an external/unrelated blocker
```

## Why `ACCEPTANCE_CRITERION_DEFECT` is named explicitly

The single most likely place for a business-acceptance skill to quietly absorb a bad requirement as an
"implementation bug" (and thereby let engineering silently patch around a wrong acceptance criterion) is
here. This skill never rewrites or reinterprets an acceptance criterion — a defect of this class is
routed back to PRD/AC authoring, and the disposition (`references/acceptance-disposition.md`) records it
as an open condition, not a closed one.
