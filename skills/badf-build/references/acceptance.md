# Admission ladder — badf-build

The skill's status is recorded in `badf/skill-registry.json`; this ladder is a pointer, not a second
status.

- `DESIGNED` — **WP-BLD-A** (this freeze): thin router, BLD-I01…I18, twelve-stage workflow, fourteen
  references, registered C1 with no tools; no runtime, no validator, no schema, no lifecycle change.
- `IMPLEMENTED` — **WP-BLD-B**: G07 evidence schemas (`source-change`, `build`, `unit-test`,
  `documentation`) formalized from the objects the self-dossier already produces; preflight/execution
  substrate; the build ledger. Extends the canonical producer; adds no second one.
- `VALIDATED` — **WP-BLD-C**: deterministic G07 controls in `badf_gate.py` — authority before mutation,
  exact baseline, scope containment, red-before-green evidence where TDD applies, fresh verification,
  budget/stop, delegation as a strict subset — each failing-first and mutation-killed.
- `SHADOWED` — **WP-BLD-D**: shadow on BADF's own historical builds — every G07 self-dossier since
  WP-0030 is a real case — with non-coverage declared, not implied.
- `APPROVED` / `ACTIVE` — **WP-BLD-E**: the operator's admission decision; registry status flip only,
  digest unchanged, no authority granted.
