# Shadow-evidence — badf-uat (WP-UAT-D)

The capability's live status is `badf/skill-registry.json`. This records the shadow calibration
behind it, and the two tripwires that keep the caveat below from becoming permanent by neglect.

## The honest caveat — this shadow is REPRESENTATIVE, not real-project

**BADF has never run a G10.** Measured on `main` at **`9fad369`** — the SHA is part of the claim,
because a bare count goes stale silently and this one already did (it read `91` G07 dossiers when
first written, six landings ago):

```
G10 dossiers ever assembled              0     <- the only load-bearing number; the tripwire's subject
landed evidence with evidence_type uat   1     <- work/WP-2026-0124/evidence/G07/source-change.diff,
                                                  this family's own B-rung diff shipping the schema.
                                                  NOT a produced uat artifact.
gate-dossier.G07 on main                97
```

Only the **first** line is load-bearing, and only it is asserted by a test. The other two are dated
context: pinning a count that legitimately moves every landing would be the snapshot-worn-as-an-invariant
error (#268), which is why they carry a SHA instead of a guard.

BADF builds itself. It is a governance framework with **no product and therefore no
product-acceptance event** — the same reason `badf-security-design` had no threat surface of its
own (#166) and `badf-solution-design` had no real solution matrices (#145). Both were admitted on
**representative** corpora with the caveat stated and a real re-shadow reserved as owed.

So this calibration runs on a **declared representative** product, `PRD-SHADOW-CHECKOUT`, and says
so plainly. **A real re-shadow is owed the first time any project produces an actual G10 `uat`
binding**, and the operator may hold `APPROVED`/`ACTIVE` until then.

### What was refused, and why — SARCHI's ruling on #277

Two other shapes were considered and rejected before this one:

| shape | disposition | why |
| :--- | :--- | :--- |
| **empty-corpus shadow** — declare the corpus `[]` and record non-coverage per control | **refused** | vacuous. Zero cases exercised is zero discrimination: a broken control and a correct one produce identically green runs. *A shadow that shadows nothing reports exactly as green as one that shadowed everything.* |
| **`uat` shadowed over the 91 G07 dossiers** | **refused** | different gate, different semantics. Genuinely the proxy-for-property class. |
| **declared representative corpus + live tripwire** | **adopted** | every control is driven end to end and CAN fail; what it cannot do is surface encodings nobody imagined. |

The distinction the ruling turned on:

- **Vacuity gap** — the run *cannot* fail. Disqualifying.
- **Realism gap** — the run drives every control and *can* fail, but only on imagined encodings.
  This is what a declared caveat plus a live trigger exists for.

The empty-corpus option was the *weaker* instrument wearing the honest label, and it was mine.

## Calibration — every control driven, each observed red

`check_g10_uat_binding` is exercised over the representative binding in
`examples/uat-shadow-checkout.json`. Every case is **recomputed against the live gate on every
test run**, so this record cannot drift from the code; nothing here is a stored verdict.

| Defect (mutated from the clean binding) | Control | Invariant | Outcome |
| :--- | :--- | :--- | :--- |
| observation naming a scenario absent from the binding | U2 | UAT-I01 | refused |
| `FAIL` observation with no classified defect | U3 | UAT-I11 | refused |
| two observations for one scenario | U6 | UAT-I09 / I17 | refused |
| `RECOMMEND_ACCEPT` over a critical not passing | U4 | UAT-I13 | refused |
| acceptance bound to a different candidate digest | U5a | UAT-I16 | refused |
| acceptance issued by a non-human principal | U5b | UAT-I14 / I15 | refused |
| `RECOMMEND_ACCEPT_WITH_CONDITIONS`, critical named in no condition | C7 | UAT-I13 | refused |
| `ACCEPTED_WITH_CONDITIONS` carrying no conditions | C8 | UAT-I16 | refused |
| unconditional `ACCEPTED` over an unacknowledged critical | C9 | UAT-I16 | refused |
| `scenario_set_digest` not recomputing over the carried scenarios | C10 | UAT-I17 | refused |
| criterion `not_covered` with neither reason nor declared gap | C11 | UAT-I12 | refused |

**And a refusal outcome, not only a happy path.** `examples/uat-shadow-checkout-rejected.json`
carries a critical `FAIL`, a classified defect and `RECOMMEND_REJECT` with **no acceptance object**
— and is **admitted**. The gate refuses malformed evidence, never an unfavourable result. A shadow
containing only accepted runs would not have shown that.

**Anti-vacuity.** The number of shadow cases is asserted equal to the number of `ValidationError`
sites read from the live gate **by AST**, not to a number written down here. A control added later
without a shadow case fails the suite rather than going quietly unshadowed.

**All ten defect classes injected, and the PRD/AC/RTM chain carried.** The rung-A ladder asks D for
*"known and injected defects across all ten `defect-classification.md` classes"* and a
*"PRD/AC/RTM chain"*. Both are built: the sweep walks the `defect_class` enum **read from the
schema** — one classified failure per class, each admitted — with an unknown class refused as its
negative control, and `acceptance_basis.traceability_digest` is populated and pinned.

*I first argued both requirements were unachievable. They are not:* `defect_class` is **data** in
the binding, not something the router detects, and `traceability_digest` was an optional field I
had simply left unset. That over-reach ran in the direction that excused an incomplete build and is
retracted on #277; only the detection-quality third genuinely cannot be built.

## Declared non-coverage

Stated, never implied — the `badf-build` shadow doctrine (#197) applied to a corpus that is
representative rather than partial.

| # | Not covered | Why |
| :--- | :--- | :--- |
| 1 | **Detection quality.** True findings, false positives, missed criteria and criticality-flattening false negatives are NOT measured. | These are properties of a *judgment*. `badf-uat` is a thin router with `allowed_tools: []` — it detects nothing; adapters report. No corpus makes a tool-less router produce a false positive. This is the one requirement of the rung-A ladder that cannot be built today, and the only one amended. |
| 1b | **Real-project acceptance.** No scenario derivation from a real PRD, no real execution adapter, no real triage workflow. | No G10 has ever run. This is the caveat above, and the trigger below. |
| 2 | **C7/C9 substring matching (#289, OPEN).** A failing critical scenario named only by a *longer* id passes as acknowledged. | Found while building this shadow. These two controls are **not** reported as sound; the shadow asserts the hole is still open, so it cannot be forgotten. |
| 3 | **Encodings nobody imagined.** The realism gap named above. | Inherent to a representative corpus; discharged only by the real re-shadow. |
| 4 | **Four defect shapes no control catches**, each ADMITTED by the gate today and each asserted admitted in `tests/test_badf_uat_shadow.py::DeclaredNonCoverageTests`: `coverage-contradicts-observation` (a criterion marked `covered_pass` while its own scenario's observation is `FAIL`), `scenario-dropped-entirely` (a scenario carrying no observation at all — dropped rather than reported `NOT_EXECUTED`), `critical-not-executed-unclassified` (a critical scenario `NOT_EXECUTED` with no defect class under `RECOMMEND_REJECT`), `defect-statement-empty` (a classified defect whose statement is empty). | SARCHI's #270 addition asked for **one** adversarial case beyond the ten. The search for one found **four**, and declaring only the one asked for would reproduce precisely the defect the requirement exists to prevent — a gap found and not written down. Ten cases, one per class, is the confirm-shaped form; these four test that what the shadow does not cover is **declared, never implied**. |

## Tripwires — the caveat expires by itself

`#166`'s trigger is prose and has waited on a human noticing since it was filed. These do not.

| Test | Fires when | Then |
| :--- | :--- | :--- |
| `test_no_real_g10_dossier_exists_yet` | any `work/*/gate-dossier.G10.json` appears | the caveat above is false; re-shadow for real per **#291** |
| `test_the_known_substring_hole_in_c7_c9_is_still_open` | #289 lands | remove that test **and** non-coverage row 2 together |

Neither may be deleted to make a red suite green. Both are in
`tests/test_badf_uat_shadow.py`, and each says so in its own docstring.

## Registry advance — both earned steps declared

Per SARCHI's ruling on #277, this rung advances `badf-uat` **`IMPLEMENTED` → `SHADOWED`** in one
registry edit, declaring both earned steps rather than repairing one silently:

- **`VALIDATED` was earned at rung C** (`WP-UAT-C`, landed as `bc7ca27`) **and the advance was
  omitted.** C's own exact-pin comment set the status to the unadvanced value and nothing flagged
  it — the co-edit-obligation-silently-unmet shape, **#268's class**, named here rather than
  quietly fixed. The omission was mine.
- **`SHADOWED` is earned by this rung**, on the calibration above.

The standing fix is a line in the ladder, not a new checker: *each rung's PR advances the registry
status in the same change; a rung PR that does not is refused at review.* That puts the obligation
in REV's path rather than in anyone's memory — a doc line consumed by an existing control, rather
than an instrument built for a defect observed once.

## Provenance

Ruling and its amendment: **#277**. Precedent: **#166** (`badf-security-design`), **#145**
(`badf-solution-design`). Defect found while building this: **#289** (GOV-0125). Deferred real
re-shadow, trigger explicit and ownership named: **#291** (GOV-0126). Work package:
**`WP-2026-0131`** / **`BADF-DEM-0118`** / **`GOV-0124`**.

The debt is tracked in three places that must move together: the non-coverage table above, the
tripwire tests in `tests/test_badf_uat_shadow.py`, and #291. A caveat recorded in only one of
them is the silence C11 refuses.
