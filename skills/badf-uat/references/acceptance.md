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

---

## Standing rule for every rung

**Each rung's PR advances the registry status in the same change. A rung PR that does not is
refused at review.** Rung C shipped without the `VALIDATED` advance this ladder assigns it, and
nothing flagged it until rung D read the ladder — the co-edit-obligation-silently-unmet shape
(#268's class). The obligation lives here, in REV's path, rather than in a new checker: a doc line
consumed by an existing control beats an instrument built for a defect observed once.

## AMENDMENT — `WP-UAT-D`, detection quality deferred

**Ruled by SARCHI on #277 (2026-09-01), on BADF-WP-0131.** *Extend-only: the `SHADOWED` bullet
above is unchanged and remains the frozen rung-A text. This records what of it this rung delivers
and what moves, and why.*

**Delivered by `WP-UAT-D`:**

- the representative corpus **carries** the PRD/AC/**RTM** chain — all three of `prd_digest`,
  `acceptance_criteria_digest` and `traceability_digest` populated, well-formed and pairwise
  distinct, asserted. **The digests are synthetic, not real**: the chain is *carried*, not *real*,
  which is what a declared-representative corpus can honestly claim and is consistent with
  non-coverage **1b** (*no scenario derivation from a real PRD*). The frozen text above asks for a
  "real ... chain"; that half arrives with the real re-shadow (#291), and saying otherwise here
  would overclaim on the one surface where the representative/real distinction is the deliverable;
- **injected defects across all ten** `defect-classification.md` classes, the class set read from
  the schema enum rather than written down, so a class added later is covered or the count fails;
- four further **adversarial cases no control catches**, asserted ADMITTED and **declared** in
  `shadow-evidence.md` — gaps declared, not implied, which is this ladder's own words;
- every G10 control driven, each observed red against its own message fragment.

**Deferred to #291 (GOV-0126), trigger-gated:** *measuring true findings, false positives, missed
criteria, non-coverage quality and criticality-flattening false negatives.* These are properties of
a **judgment**. `badf-uat` is a thin router registered with `allowed_tools: []` — it detects
nothing; adapters report and humans decide. No corpus makes a tool-less router produce a false
positive, so this half of D presumes an executor and a real corpus that do not exist.

The deferral **expires by itself**: `tests/test_badf_uat_shadow.py::TripwireTests::test_no_real_g10_dossier_exists_yet`
asserts against a live scan that no real G10 dossier exists, and goes red the day one lands —
unlike #145/#166, whose prose triggers wait on a human noticing.

**Rung target:** `WP-UAT-D` advances the registry to **`SHADOWED`**; the exact status pin in
`tests/test_badf_uat_contract.py` follows this ladder.

## ADMISSION — `WP-UAT-E`, operator decision as attributed (#310)

**Extend-only: the `APPROVED`/`ACTIVE` bullet above is unchanged rung-A text.** This records the
decision taken under it.

**The decision is ATTRIBUTED, not independently verifiable.** All three agents act under the
shared `BizEraERP` account and no structural actor field discriminates authorship (#261 / #308),
so a reader cannot distinguish *"the operator ruled this"* from *"an agent recorded that the
operator ruled this."* Nothing here disputes the attribution; it is simply not checkable, and
this ladder is what a later reader consults. The qualifier comes out when `merged_by`
discriminates.

`badf-uat` is admitted **`SHADOWED` → `ACTIVE`** on WP-UAT-D's evidence (landed `272e6036a`):
eleven G10 controls each observed red against its own message fragment, ten defect classes
injected from the schema enum, a rejecting run admitted, two tripwires verified able to fire.
Precedent: `badf-solution-design` (#145) and `badf-security-design` (#166) both reached `ACTIVE`
on **representative** shadows with the caveat stated and a real re-shadow deferred.

**Admitted WITH two open defects in this capability's own control path** — recorded here because
admission must not be mistaken for a clean control path:

| | |
| :--- | :--- |
| **#289** | C7/C9 match a scenario id by **substring**: a critical failure named only by a *longer* id passes as acknowledged. Plan approved, not yet landed. |
| **#293** | C8 admits `[""]` — an empty-conditions **shape** hole a matcher fix does not touch. |

Plus four adversarial cases no control catches, declared in `shadow-evidence.md` — led by
`coverage-contradicts-observation`, where a criterion marked `covered_pass` while its own
scenario's observation is `FAIL` is **admitted today and nothing notices**. And the
detection-quality half of D, deferred to **#291**'s trigger.

**`ACTIVE` grants no authority.** `UAT-I14`/`UAT-I15` hold at every rung including this one:
`allowed_tools` stays `[]`, the recommendation vocabulary cannot express an acceptance, and the
Layer-2 acceptance pins `principal_type: human`. Those three are asserted together as a property
of the admitted state in `tests/test_badf_uat_contract.py::test_active_grants_no_acceptance_authority`
— **mechanical, not stated**, because admission is exactly when the non-grant starts mattering.
