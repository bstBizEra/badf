# Shadow evidence — badf-engineering-verification (WP-VER-D, `BADF-WP-0106`, Issue #207 / GOV-0089)

**What is real and what is reconstructed or representative — first sentence, as the contract requires.**
The typed-object shadow is **representative** (no typed real G08 dossier exists on `main`; a real
re-shadow is owed the first time a project passes G08 with typed objects), and the real-review class is
**RECONSTRUCTED** from prose verdict comments — encoded under the encoded reviewer's own honesty
conditions, never inflated into a council. What is fully real: `work/WP-2026-0010`'s historical G08
dossier, replayed byte-for-byte through the landed gate, and the five verdicts BARCHI-1 actually posted.

The capability's live status is `badf/skill-registry.json` (`SHADOWED` at `BADF-WP-0106`). Everything
below is recomputed from the repository on every run by `tests/test_badf_verification_shadow.py`; the
record is `examples/verification-shadow-evidence.json` (`measured_on` = the `main` that includes #205).

## Measurement

| Case class | Corpus | What the contract had to do | Outcome |
| :--- | :--- | :--- | :--- |
| `historical-generic-dossier` (1) | WP-2026-0010 — the only real G08 dossier: four binding-less, agent-produced objects, `contract-test` declared `NOT_APPLICABLE`, three carried conditions | the additive path: `check_g08_binding` passes through, `check_g08_dossier` stays silent, the dossier still validates end-to-end | **UNTOUCHED** |
| `real-review-encoded` (5) | BARCHI-1's real verdict arc — PR #196 **Request Changes** (comment 5469987101, head `2c93d60`, CI red) → **Approved** (5470235706, fix head `23866e7`), #201 (5470380581), #202 (5470510051), #205 (5470622958) | single-reviewer verification records: one ballot each, the real comment id as `reviewer_run_id`, sealed digest RECONSTRUCTED, the #196 synthetic-id collision as a genuine OPEN `MAJOR` finding then `RESOLVED` on the fix head (the `WP-2026-9999` sentinel as resolution evidence); `verify` accepts each and refuses tampering (digest changed, the finding erased, `VERIFIED` without a composed ref) | **5/5 `VERIFY_PASS`**, tamper-refused |
| `representative-typed-dossier` (14) | synthetic fixtures spanning the outcome space: 2 clean (C1; C2 with a two-ballot record), 10 injected defects | each defect refused by the control that owns it — divergent trees (C1 with a record, C2 without), author-as-reviewer uncarried (C3), one-ballot C2 (C3), missing lens (C3), untyped agent observation under `runtime_required` (C4), empty non-coverage (C5), OPEN MAJOR passed over / unmapped (C6 ×2), composed declared `NOT_APPLICABLE` (C7), plus two binding-level cases — a bare-PASS review (VER-I10) and an INDETERMINATE contract serialised as PASS (VER-I14) | **12/12 refused, 2/2 admitted**; every control C1–C7 and the binding invariants VER-I10/VER-I14 own ≥1 refusal |

## Metrics

| Metric | Result |
| :--- | :--- |
| injected defects refused | 12/12 |
| clean dossiers admitted (false refusals) | 2/2 (0 false) |
| missed defects | 0 |
| encoded real reviews verified / tamper-refused | 5/5 |
| duplicate-finding rate | 0 (single reviewer) |
| severity drift | none declared (the encoding carries only what was posted) |
| reviewer correlation | **NOT MEASURABLE — one reviewer seat** (non-coverage) |

## Non-coverage (named, not implied)

- **No typed real G08 dossier** — BADF's own work packages stop at the G07 self-dossier; the
  typed-object cases are representative fixtures. A real typed re-shadow is owed the first time a
  project passes G08 with typed objects, and the operator may hold `ACTIVE` until then.
- **One reviewer seat** — reviewer correlation and duplicate-rate metrics cannot be measured; the
  future BADF-QA / BADF-REV seats change this.
- **Prose reconstruction** — the encoded records are RECONSTRUCTED from PR comments (ids and check-runs
  cited in each record's `non_coverage`); the reviewer posted verdicts, not records. The approvals encode
  `findings: []` — the reviewer's probes are **not** encoded as pseudo-findings (a passed probe is not a
  defect, VER-I03); this deviation from the #207 plan wording is declared in each record. The #196
  Request-Changes record binds the RC head's **own** content tree (`be12ef9`, recomputed) and the base
  `main` stood at when the verdict posted (`6814a24`) — corrected under BADF-REV finding F4.
- **The per-fixture `validate_dossier` scratch-clone path** promised in the #207 wording is not shipped —
  representative cases recompute through the pure `check_g08_dossier` (and `check_g08_binding` for the two
  binding-level cases); end-to-end `validate_dossier` is exercised by the historical WP-2026-0010 case and
  by CI's composed run of this rung's own dossier. Deviation declared, not implied.
- **Conflict of interest, disclosed** — BARCHI-1 is both the encoded party and the seat's usual
  reviewer; BARCHI-2 (not encoded) co-reviews the encoding class for fidelity, and BARCHI-1's verdict
  discloses the COI.

## What this shadow earned, and what the operator then decided

The shadow shows the controls refuse what they must and touch nothing they must not — on
representative fixtures, one real dossier and five reconstructed reviews. That earned `SHADOWED`.
Admission (`VER-E`) was the **operator's decision on this evidence**, asked on its own issue — it was
never pre-granted, and the registry advances by evidence, not by instruction.

**Decided on #214 (GOV-0092): `ACTIVATE`.** The question was put with the `HOLD AT SHADOWED` alternative
stated beside it and the four gaps above named in the issue body; the operator chose to activate over
them, and the real-conditions re-shadow is deferred to its own trigger-gated issue. **The measurement on
this page is unchanged by that decision** — an admission does not retroactively widen a shadow, and the
gaps it was granted over remain exactly as declared here. The live status is `badf/skill-registry.json`.
