# Research acceptance controls

Status: frozen contract v0.2. The root capability remains `DESIGNED`. Progression follows `docs/07-skills-governance.md`: `DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → APPROVED → ACTIVE`.

## Controls required before `VALIDATED`

| # | Control |
| :--- | :--- |
| 1 | material research cannot start without a research question |
| 2 | scope/non-goals, assumptions, decision context and non-empty stop conditions are explicit |
| 3 | baseline is bound to a repository revision when repository research applies |
| 4 | every VERIFIED material claim has evidence |
| 5 | a missing source cannot silently resolve |
| 6 | a changed source digest makes dependent claims stale |
| 7 | an inference cannot be serialized as an observation |
| 8 | contradictory evidence is preserved |
| 9 | confidence has an explainable, derived basis |
| 10 | source count cannot substitute for source independence |
| 11 | the research author cannot satisfy required independent challenge |
| 12 | a duplicate reviewer identity cannot increase quorum |
| 13 | a reviewer must declare non-coverage |
| 14 | RESEARCH_SUFFICIENT does not authorize implementation |
| 15 | MORE_RESEARCH_REQUIRED cannot generate an implementation-ready work package |
| 16 | an invalid state transition fails closed |
| 17 | the evidence digest changes when material evidence changes |
| 18 | Research → Decision → Work Package traceability can be reconstructed |

Controls are deterministic where they can be. Substantive judgment remains evidence-backed and challengeable; it must not be disguised as a validator result.

## Admission

- `IMPLEMENTED`: the planned P0 subskills exist as concise, governed `SKILL.md` files under this family.
- `VALIDATED`: all 18 controls are enforced by the canonical gate/tests with mutation coverage where applicable.
- `SHADOWED`: representative historical BADF investigations are rerun without affecting gates and reconciled against known outcomes.
- `APPROVED`: the owner and required security/governance authorities approve the pinned capability.
- `ACTIVE`: the approved version/digest is admitted for routing in `badf/skill-registry.json`.

Until admission completes, the root `badf-research` entry remains `DESIGNED`. An individually `IMPLEMENTED` subskill does not activate the root family.
