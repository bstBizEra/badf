# badf-requirements — validation evidence

Status: **VALIDATED** (`BADF-WP-0064`). The skill's live status is `badf/skill-registry.json`.

`badf-requirements` authors the four canonical G02 artifacts and validates them with the canonical
gate (`badf_gate.py dossier`) — it has no validator of its own. Validation runs that gate on three
representative cases (`tests/test_badf_requirements_validation.py`, faithful-runner shape: the shipped
G02 dossier mutated in a scratch clone, artifacts re-digested). The gate is **unchanged** by this WP.

## Case A — valid PRD → clean artifacts

The skill's model produces a complete G02 dossier that renders **`APPROVED`**:

```text
python3 scripts/badf_gate.py dossier examples/gate-dossier.G02.json   → BADF GATE APPROVED
```

## Case B — orphan requirement / qualitative NFR → rework

The canonical gate is the fitness function for the skill's discipline — it refuses exactly what
`badf-requirements` warns against:

| Defect the skill guards | Gate refusal (measured) | Invariant |
| :--- | :--- | :--- |
| a requirement tracing to no objective (`objective_refs: []`) | `requirements: REQ-… decomposes no objective` | REQ-I02 |
| a qualitative NFR (`target.value: "fast"`) | `nfr: NFR-… is not quantified` | REQ-I04 |
| an orphan requirement in the RTM | `traceability: orphan requirement …` | REQ-I05 |

The first two are asserted directly here; all three are covered by the G02 gate suite
(`tests/test_badf_g02.py`). "Rework" is the gate refusing — the skill re-authors until it passes.

## Case C — a security requirement from a G05 concern → provenance preserved

A security requirement introduced after G01 (statement naming its originating threat, `T-001` from the
G05 threat model) traces to the objective this evidence designates as the **security objective**
(`OBJ-003`) and **passes** the gate. Ids are numeric by schema, so the security designation is
semantic — carried by the statement and the trace, not the id.

**Honest boundary (REQ-I06).** The canonical G02 gate has **no** security-source (`SRC → REQ`) field:
it verifies the security requirement traces to a declared objective, but it does **not** deterministically
enforce that the provenance is present. So REQ-I06 provenance is a **skill-authoring discipline verified
by inspection** here (the test asserts the requirement names the threat and traces to the security
objective), not a gate control. Making `SRC → REQ` a deterministic control is a **candidate future
failing-first WP** — added only if real project use proves the need, never smuggled in as validation.

## Admission

`IMPLEMENTED → VALIDATED` (operator-authorized). `SHADOWED` / `APPROVED` / `ACTIVE` remain later
admission decisions. This WP adds no gate code — no new control, nothing to mutate; validation runs the
real canonical gate.
