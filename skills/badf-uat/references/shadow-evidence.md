# Shadow-evidence — badf-uat (WP-UAT-D)

The capability's live status is `badf/skill-registry.json`. This records the shadow calibration
behind it, and the two tripwires that keep the caveat below from becoming permanent by neglect.

## The honest caveat — this shadow is REPRESENTATIVE, not real-project

**BADF has never run a G10.** Measured on `main` when this was written:

```
G10 dossiers ever assembled              0
landed evidence with evidence_type uat   0   (only hits are this family's own tests)
gate-dossier.G07 on main                91
```

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

## Declared non-coverage

Stated, never implied — the `badf-build` shadow doctrine (#197) applied to a corpus that is
representative rather than partial.

| # | Not covered | Why |
| :--- | :--- | :--- |
| 1 | **Real-project acceptance.** No scenario derivation from a real PRD, no real execution adapter, no real defect triage, no real coverage matrix. | No G10 has ever run. This is the caveat above, and the trigger below. |
| 2 | **C7/C9 substring matching (#289, OPEN).** A failing critical scenario named only by a *longer* id passes as acknowledged. | Found while building this shadow. These two controls are **not** reported as sound; the shadow asserts the hole is still open, so it cannot be forgotten. |
| 3 | **Encodings nobody imagined.** The realism gap named above. | Inherent to a representative corpus; discharged only by the real re-shadow. |

## Tripwires — the caveat expires by itself

`#166`'s trigger is prose and has waited on a human noticing since it was filed. These do not.

| Test | Fires when | Then |
| :--- | :--- | :--- |
| `test_no_real_g10_dossier_exists_yet` | any `work/*/gate-dossier.G10.json` appears | the caveat above is false; re-shadow for real |
| `test_the_known_substring_hole_in_c7_c9_is_still_open` | #289 lands | remove that test **and** non-coverage row 2 together |

Neither may be deleted to make a red suite green. Both are in
`tests/test_badf_uat_shadow.py`, and each says so in its own docstring.

## Provenance

Ruling and its amendment: **#277**. Precedent: **#166** (`badf-security-design`), **#145**
(`badf-solution-design`). Defect found while building this: **#289**. Work package:
**`WP-2026-0131`** / **`BADF-DEM-0118`** / **`GOV-0124`**.
