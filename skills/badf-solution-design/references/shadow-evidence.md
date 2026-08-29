# Shadow-evidence — badf-solution-design (WP-SOL-D)

The capability's live status is `badf/skill-registry.json` (`SHADOWED` at `BADF-WP-0074`). This records
the shadow calibration that earned it.

## The honest caveat — this shadow is REPRESENTATIVE, not real-project

`badf-research` (WP-0055) and `badf-architecture` (WP-0059) shadowed on **real historical BADF cases**.
`badf-solution-design` has **no real project compositions yet** — BADF itself is a governance framework
with no UX / API / authorization surface to design. So this calibration runs on **representative**
composition matrices spanning the outcome space, and says so plainly. **A real re-shadow is owed the
first time a project actually uses the skill**, and the operator may hold `APPROVED`/`ACTIVE` until then.

## Calibration

The `solution` command (structural + matrix-internal seam controls, WP-SOL-B/C) was run over
representative matrices. Every command below is reproducible.

### True positives — every defect is refused

| Defect (mutated from a clean matrix) | Control | Outcome |
| :--- | :--- | :--- |
| empty `solutions` | no-empty-matrix | refused |
| duplicate `solution_id` | SOL-C01 | refused |
| a row binding no specialist artifact | SOL-C03 | refused |
| missing / malformed `requirement_ref` | schema (SOL-I01) | refused |
| `api_refs` without `authorization_refs` | SOL-C04 / SOL-I04 | refused |
| `authorization_refs` without `audit_refs` | SOL-C05 / SOL-I06 | refused |
| `ux_refs` without `accessibility_refs` | SOL-C06 / SOL-I09 | refused |

These are exercised as `tests/test_badf_solution_composition.py` (each mutation-killed).

### Zero false positives — clean compositions pass

| Representative matrix | Shape | Outcome |
| :--- | :--- | :--- |
| `examples/solution-composition.json` | 2 rows, all ref kinds | PASS |
| `examples/solution-composition-shadow-refund.json` | refund approve/deny, all seams satisfied | PASS |
| `examples/solution-composition-shadow-reporting.json` | report view (all seams) + a **data-only** schedule row | PASS |

The reporting matrix's data-only row is the key false-positive check: the seams are **co-occurrence**,
not blanket — a row with no `api_refs` correctly needs no `authorization_refs`, and passes.

### Declared non-coverage — what this shadow does NOT exercise

The **external-artifact** seams cannot be exercised without the specialist adapters, which do not exist:

- SOL-I02 (against the architecture baseline), SOL-I05 (default-deny in the authorization model),
  SOL-I07 (API↔data schemas), SOL-I10 / SOL-I11 (migration / API-compat);
- the *semantic* resolution of every ref against its specialist artifact (does `ACT-refund-approve`
  actually exist and grant `refund:approve`?).

Silence is not coverage: these are named here, not implied to pass.

## Result

Over the representative outcome space: **all 7 defect classes detected, zero false positives on 3 clean
compositions (including the co-occurrence data-only row), non-coverage declared** — no contract gap
surfaced at the matrix-internal level. `VALIDATED → SHADOWED`. `APPROVED`/`ACTIVE` remain the operator's
admission decision, and a real-project re-shadow is owed before the skill is trusted on production
compositions.
