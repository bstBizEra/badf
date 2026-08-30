# Shadow-evidence — badf-implementation-plan (WP-IMP-D)

The capability's live status is `badf/skill-registry.json` (`SHADOWED` at `BADF-WP-0094`). This records
the shadow calibration that earned it.

## The honest caveat — this shadow is REPRESENTATIVE, not real-project

`badf-research` and `badf-architecture` shadowed on **real** historical BADF cases. `badf-implementation-plan`
has **no real G06 planning breakdowns yet** — BADF's own work packages are governance work, not product
implementation plans that pass through G06. So this calibration runs on **representative** work-breakdowns
spanning the outcome space, and says so plainly. **A real re-shadow is owed the first time a project
actually plans through G06**, and the operator may hold `APPROVED`/`ACTIVE` until then. (This mirrors
`badf-solution-design` WP-SOL-D and `badf-security-design` WP-SEC-D.)

## Calibration

`check_work_breakdown` (the existing acyclic check + the WP-IMP-C planning controls IMP-C1…C5) was run
over representative work-breakdowns. Every command below is reproducible.

### True positives — every defect is refused

| Defect (mutated from a clean breakdown) | Control | Outcome |
| :--- | :--- | :--- |
| a cyclic `depends_on` graph | acyclic (pre-existing) | refused |
| `authority_requirement` omits a role the matrix requires for the `change_class` | IMP-C1 / IMP-I07 | refused |
| an `acceptance` claim with no `test_obligation` | IMP-C2 / IMP-I09 | refused |
| `execution_budget.max_attempts` non-positive **or a boolean** | IMP-C3 / IMP-I11 | refused |
| an empty `stop_conditions` | IMP-C4 / IMP-I12 | refused |
| a dangling or cyclic `composition_after` | IMP-C5 / IMP-I06 | refused |

These are exercised as `tests/test_badf_g06_planning_controls.py` (each mutation-killed, including an
independent gate-mutation pass — all six raise sites confirmed load-bearing).

### Zero false positives — clean breakdowns pass

| Representative breakdown | Shape | Outcome |
| :--- | :--- | :--- |
| `examples/work-breakdown-planned.json` | 2 tasks, all planning fields | PASS |
| `examples/work-breakdown-shadow-migration.json` | a wide refactor as **expand → migrate → contract** (a `composition_after` chain) | PASS |
| `examples/work-breakdown-shadow-feature.json` | a vertical-slice feature + a **minimal task carrying no planning fields** | PASS |

The feature breakdown's minimal follow-up task is the key false-positive check: the controls are
**field-scoped** — a task without `acceptance`/`execution_budget`/`stop_conditions` triggers none of them
and passes, so the extension is backward-compatible with every existing breakdown.

### Declared non-coverage — what this shadow does NOT exercise

- The **cross-WP execution frontier** (READY = blockers CLOSED ∧ baselines current ∧ authority present) —
  it spans a whole plan and a live ledger, not one breakdown artifact.
- The **semantic resolution** of every ref against its real artifact (does `AC-001` exist in the
  requirements; is `POST /refunds/approve` a real API contract) — that needs the specialist artifacts.
- The **GitHub issue projection** and the **`badf-git` execution-topology realization** are contract
  boundaries (`issue-projection.md`, the SKILL's declares-vs-realizes split), demonstrated as doctrine,
  not run here.

Silence is not coverage: these are named, not implied to pass.

## Result

Over the representative outcome space: **all six defect classes refused, zero false positives on three
clean breakdowns (including the field-scoped minimal task), non-coverage declared** — no contract gap
surfaced at the work-breakdown level. `VALIDATED → SHADOWED`. `APPROVED`/`ACTIVE` remain the operator's
admission decision, and a real-project re-shadow is owed before the skill is trusted on production plans.
