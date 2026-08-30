# Acceptance and admission

The capability's **live status is `badf/skill-registry.json`** — this document defines the contract, not
the status, so it never hardcodes a status line that can drift from the registry. Progression follows
`docs/07-skills-governance.md`.

## Controlled admission ladder

The same pattern that carried `badf-research`, `badf-architecture`, `badf-solution-design` and
`badf-security-design` — freeze the contract first, prove it later, in separate WPs.

| WP | Outcome | Status |
| :--- | :--- | :--- |
| WP-IMP-A | root `SKILL.md` + references: WP≠task doctrine, G06 mapping, the Governed WP contract, decomposition/slicing, dependency DAG + frontier, authority-derived, test/evidence/budget/stop planning, release/rollback, issue-projection, IMP-I01…I17, external-methodology | `DESIGNED` |
| **WP-IMP-B** | backward-compatible `work-package.schema.json` extension — the governed planning fields (`dependencies`, `source_baselines`, `expected_surfaces`, `authority_requirement`, `risk_factors`, `test_obligations`, `evidence_obligations`, `execution_budget`, `stop_conditions`, `composition`) as **optional** properties (walker enforces enum/pattern/nested-required; type/coverage/DAG checks are WP-IMP-C code controls per #171); documents the ledger keys `reconcile` writes | `IMPLEMENTED` |
| **WP-IMP-C** | deterministic G06 controls in `check_work_breakdown` (the gate-enforced DAG artifact): **IMP-C1** authority-not-reduced (matrix), **IMP-C2** acceptance coverage, **IMP-C3** bounded budget, **IMP-C4** non-empty stop contract, **IMP-C5** resolvable + acyclic composition order — **code controls** (the walker doesn't type-check, #171) | `VALIDATED` |
| **WP-IMP-D** | **representative** planning shadow calibration (no real G06 breakdowns exist yet; real re-shadow owed on first real use) + the issue-projection / execution-topology doctrine exemplars; see `shadow-evidence.md` | `SHADOWED` |
| WP-IMP-E | operator admission → registry activation | `ACTIVE` |

## WP-IMP-A boundaries (no scope creep)

- **No runtime, no second validator** — no `scripts/badf_implementation_plan.py` (IMP-I17).
- **No schema, no lifecycle change** — composes the **existing** G06 artifacts; the WP-schema extension is
  WP-IMP-B, backward-compatible so historical WPs stay valid.
- **No execution** — the skill plans; it does not execute its own WPs (IMP-I15).
- **Authority derived, not invented** — from `change_class` + the matrix (IMP-I07); no A0/A2 system.
- **Declares topology; `badf-git` realizes it.**

## Admission

- `DESIGNED`: the contract exists as this `SKILL.md` + references and is registered. **Met (WP-IMP-A).**
- `IMPLEMENTED` … `ACTIVE`: earned by the later WPs above, each through the full loop; a planning field
  becomes a deterministic control only when a failing-first probe warrants it, never by precedent.
