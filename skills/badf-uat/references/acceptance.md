# Admission ladder — badf-uat

The skill's status is recorded in `badf/skill-registry.json`; this ladder is a pointer, not a second
status.

- `DESIGNED` — **WP-UAT-A** (this freeze): thin router, UAT-I01…I20, eight-stage workflow, fourteen
  references, registered C1 with no tools; no adapter runtime, no typed schemas, no lifecycle change, no
  gate change, no subskills registered.
- `IMPLEMENTED` — **WP-UAT-B**: typed `uat` evidence schema specializing `evidence.schema.json`; the
  UAT Scenario object, the execution-observation record and the two-layer disposition record as typed
  artifacts; a `badf_gate.py` path validating a G10 `uat` dossier's typed objects — mirroring `verify`
  for G08. Extends the canonical gate; adds no second one.
- `VALIDATED` — **WP-UAT-C**: deterministic G10/UAT controls in `badf_gate.py` — acceptance-basis digest
  binding, candidate digest binding, non-derivable-criterion declared (never dropped), critical-tier
  results always enumerated (never flattened into aggregate), Layer 1/Layer 2 digest equality, staleness
  detection on candidate/basis/scenario-set change — each failing-first and mutation-killed. Lean mode
  disabled: these are HARD INVARIANTS, the same tier as the G08 controls at VER-C.
- `SHADOWED` — **WP-UAT-D**: shadow on representative material — a real or synthesized G09-validated
  candidate with a real PRD/AC/RTM chain, with known and injected defects across all ten
  `references/defect-classification.md` classes, measuring true findings, false positives, missed
  criteria, non-coverage quality and criticality-flattening false negatives; gaps declared, not implied.
- `APPROVED` / `ACTIVE` — **WP-UAT-E**: the operator's admission decision, taken on WP-UAT-D's evidence
  and recorded on its own issue; registry status flip only, digest unchanged, no acceptance authority
  granted to the skill itself — UAT-I14/I15 hold at every rung of this ladder, including `ACTIVE`.
