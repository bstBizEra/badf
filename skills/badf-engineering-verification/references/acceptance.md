# Admission ladder — badf-engineering-verification

The skill's status is recorded in `badf/skill-registry.json`; this ladder is a pointer, not a second
status.

- `DESIGNED` — **WP-VER-A** (this freeze): thin router, VER-I01…I20, nine-stage workflow, sixteen
  references, registered C1 with no tools; no runtime, no validator, no schema, no lifecycle change, no
  gate change.
- `IMPLEMENTED` — **WP-VER-B**: typed G08 evidence schemas (`independent-review`, `integration-test`,
  `contract-test`, `composed-tree-test`) specializing `evidence.schema.json`; the canonical finding record
  and the verification matrix as typed artifacts; the verification run ledger beside the build ledger; a
  `badf_gate.py verify` subcommand validating a G08 dossier's typed objects — mirroring `assure` /
  `solution` / `security`. Extends the canonical gate; adds no second one.
- `VALIDATED` — **WP-VER-C**: deterministic G08 controls in `badf_gate.py` — exact target and staleness
  binding, execution-level independence and quorum, runtime-observation credit (no `agent` producer on an
  observation), provenance completeness, per-artifact non-coverage, finding preservation across synthesis,
  contract INDETERMINATE held, composed-result binding — each failing-first and mutation-killed. Lean mode
  disabled: these are HARD INVARIANTS.
- `SHADOWED` — **WP-VER-D**: shadow on the G08 material BADF has — `work/WP-2026-0010`'s G08 dossier and
  BADF's own pull-request review history — with known and injected defects, measuring true findings, false
  positives, missed defects, duplicate rate, severity drift, reviewer correlation and non-coverage quality;
  gaps declared, not implied.
- `APPROVED` / `ACTIVE` — **WP-VER-E**: the operator's admission decision, taken on VER-D's evidence and
  recorded on its own issue; registry status flip only, digest unchanged, no authority granted.
