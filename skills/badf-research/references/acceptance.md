# Acceptance and admission

Status: frozen contract v0.1. The capability is `DESIGNED`. Progression follows `docs/07-skills-governance.md`: `DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → APPROVED → ACTIVE`.

## Controls required before `VALIDATED` (deterministic, in the gate and its tests)

| # | Control |
| :--- | :--- |
| 1 | material research cannot start without a research question |
| 2 | research scope and non-goals are explicit |
| 3 | baseline is bound to a repository revision when repository research applies |
| 4 | every VERIFIED material claim has evidence |
| 5 | a missing source cannot silently resolve |
| 6 | a changed source digest makes dependent claims stale |
| 7 | an inference cannot be serialised as an observation |
| 8 | contradictory evidence is preserved |
| 9 | confidence has an explainable, derived basis |
| 10 | source count cannot substitute for source independence |
| 11 | the research author cannot satisfy required independent challenge |
| 12 | a duplicate reviewer identity cannot increase quorum |
| 13 | a reviewer must declare non-coverage |
| 14 | RESEARCH_SUFFICIENT does not authorise implementation (schema-fixed today) |
| 15 | MORE_RESEARCH_REQUIRED cannot generate an implementation-ready work package |
| 16 | an invalid state transition fails closed |
| 17 | the record digest changes when material evidence changes |
| 18 | Research → Decision → Work Package traceability can be reconstructed |

## Admission

- `IMPLEMENTED`: the nine P0 subskills exist as concise `SKILL.md` files under this family (later work packages, one at a time).
- `VALIDATED`: the 18 controls above pass as gate tests with mutation.
- `SHADOWED`: the family is run retrospectively on historical BADF findings (the authority-downgrade defect, schema drift, foreign-revision resolution, the composed-tree reds of 2026-08-28) without knowing the answer; `examples/research-record.json` is the first such shadow record.
- `APPROVED` / `ACTIVE`: owner and security approval; registry digest pinned. Until then the registry entry stays `DESIGNED`.
