# Shadow-evidence — badf-security-design (WP-SEC-D)

The capability's live status is `badf/skill-registry.json` (`SHADOWED` at `BADF-WP-0085`). This records
the shadow calibration that earned it.

## The honest caveat — this shadow is REPRESENTATIVE, not real-project

`badf-research` and `badf-architecture` shadowed on **real historical BADF cases**.
`badf-security-design` has **no real security-composition matrices yet** — BADF is a governance framework
with no UX / API / authorization / threat surface of its own to model. So this calibration runs on
**representative** threat matrices spanning the outcome space, and says so plainly. **A real re-shadow is
owed the first time a project actually uses the skill**, and the operator may hold `APPROVED`/`ACTIVE`
until then. (This mirrors `badf-solution-design` WP-SOL-D exactly.)

## Calibration

The `security` command (structural SEC-C01/02/03 + matrix-internal seam SEC-C04/05 controls) was run over
representative matrices. Every command below is reproducible.

### True positives — every defect is refused

| Defect (mutated from a clean matrix) | Control | Outcome |
| :--- | :--- | :--- |
| empty `threats` | no-empty-matrix | refused |
| duplicate `security_id` | SEC-C01 | refused |
| a threat binding no provenance `source` | SEC-C02 / SEC-I02 | refused |
| a `controlled` threat with no `control_refs` | SEC-C03 / SEC-I03 | refused |
| a `controlled` threat with no `verification_refs` | SEC-C04 / SEC-I04 | refused |
| `residual_risk` = `ACCEPTED-PENDING-AUTHORITY` on a non-`pending-authority` disposition | SEC-C05 / SEC-I12 | refused |
| a bare `ACCEPTED` residual risk | SEC-I12 (schema) | refused |

These are exercised as `tests/test_badf_security_composition.py` (each mutation-killed).

### Zero false positives — clean matrices pass

| Representative matrix | Shape | Outcome |
| :--- | :--- | :--- |
| `examples/security-composition.json` | 4 threats, 3 controlled + 1 pending-authority | PASS |
| `examples/security-composition-shadow-api.json` | API/payment threat model, all seams satisfied | PASS |
| `examples/security-composition-shadow-data.json` | data/privacy model, incl. a **`deferred`** threat with no control/verification | PASS |

The data matrix's `deferred` row is the key false-positive check: SEC-C03/C04 are **disposition-scoped** —
a threat not yet `controlled` legitimately carries neither a control nor a verification obligation, and
passes. SEC-C05 is **one-directional** — a `pending-authority` threat need not have declared its residual
risk yet.

### Declared non-coverage — what this shadow does NOT exercise

The **external-artifact** seams cannot be exercised without the specialist artifacts and registries,
which do not exist:

- the FULL SEC-I04 **bidirectional** traceability (a `security_requirement_ref` resolving *up* to a real
  threat/requirement/NFR against a sec-req registry);
- SEC-I01 exact-baseline **digest** binding (that `architecture_baseline`/`solution_baseline` name the
  real committed digests);
- the *semantic* resolution of every ref against its artifact (does `API-017` exist and is
  `ACT-payment-create` actually the tuple that guards it?).

Silence is not coverage: these are named here, not implied to pass.

## Result

Over the representative outcome space: **all seven defect classes detected, zero false positives on three
clean matrices (including the disposition-scoped `deferred` row), non-coverage declared** — no contract
gap surfaced at the structural + matrix-internal level. `VALIDATED → SHADOWED`. `APPROVED`/`ACTIVE`
remain the operator's admission decision, and a real-project re-shadow is owed before the skill is trusted
on production threat models.
