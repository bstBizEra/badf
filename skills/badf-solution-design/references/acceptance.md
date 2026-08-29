# Acceptance and admission

The capability's **live status is `badf/skill-registry.json`** (`DESIGNED` at `BADF-WP-0068` / WP-SOL-A)
— this document defines the contract, not the status, so it never hardcodes a status line that can drift
from the registry. Progression follows `docs/07-skills-governance.md`.

## Controlled admission ladder

The same pattern that worked for `badf-research`, `badf-architecture` and `badf-git` — freeze the
contract first, prove it later, in separate WPs. **Do not build every specialist in the first PR.**

| WP | Outcome | Status |
| :--- | :--- | :--- |
| **WP-SOL-A** (this) | root `SKILL.md` + references: composition model, routing, specialist ownership boundaries, cross-artifact traceability, SOL-I01…I12, G03/G04 mapping, architecture interaction, authority boundaries, external-methodology dispositions | `DESIGNED` |
| WP-SOL-B | composition schemas + the solution-composition matrix artifact + deterministic controls | `IMPLEMENTED` |
| WP-SOL-C | cross-artifact seam controls in the canonical `badf_gate.py` (failing-first) | `VALIDATED` |
| WP-SOL-D | historical shadow calibration on real BADF solutions | `SHADOWED` |
| — | owner / assurance admission, then registry activation | `APPROVED` → `ACTIVE` |

## WP-SOL-A boundaries (no scope creep)

- **No runtime, no second validator** — no `scripts/badf_solution_design.py` (SOL-I12); `badf_gate.py`
  is the sole gate authority.
- **No lifecycle change** — `lifecycle.json`, G03 and G04 required_evidence and their gate rules are
  unchanged; solution-design composes into the **existing** G03/G04 evidence.
- **No specialist activation** — routing names who would own each concern; the UX / authorization / data
  / API / accessibility adapters are not admitted here.
- **No new global ID family** — the solution-composition matrix uses a plain `solution-composition`
  object at freeze; a dedicated `SDM-NNNN` family waits for proven need (WP-SOL-B).
- **Architecture spine respected** — `badf-architecture` (ACTIVE) owns boundaries; solution-design details
  interfaces and raises `ARCHITECTURE_CHANGE_REQUIRED` rather than inventing one.

## Admission

- `DESIGNED`: the contract exists as this `SKILL.md` + references and is registered. **Met (WP-SOL-A).**
- `IMPLEMENTED` … `ACTIVE`: earned by the later WPs above, each through the full loop; a seam becomes a
  deterministic control only when a failing-first probe warrants it, never by precedent.
