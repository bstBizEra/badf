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
| 19 | the research scope is bounded and machine-readable: a material run declares non-empty `stop_conditions`, `assumptions` distinct from evidence, and a `decision_context` naming the decision it serves (framing, excluded from the `evidence_digest`) |
| 20 | framing precedes evidence: a record in a pre-evidence state (`PROPOSED`/`FRAMED`/`BASELINED`) carries no `claims`, `sources`, or `findings` (the `problem-framing` invariant — sharpen the question, do not answer it) |
| 21 | a claim's status is consistent with its evidence (the `fact-checking` invariant): a `FALSIFIED` claim carries a contradicting source (no evidence ≠ false), and a `DISPUTED` claim carries both supporting and contradicting sources (support and contradiction coexist). Whether a source's *content* entails the claim is not machine-checkable here — the source carries no content locator — and is tracked separately |
| 22 | a finding is grounded (the `evidence-synthesis` invariant): every finding references at least one claim — a synthesis conclusion rests on adjudicated evidence, not free assertion |

## Admission

- `IMPLEMENTED`: the nine P0 subskills exist as concise `SKILL.md` files under this family (later work packages, one at a time). Present: `repository-research`, `problem-framing`, `fact-checking`, `evidence-synthesis` (4 of 9).
- `VALIDATED`: the 22 controls above pass as gate tests with mutation. Enforced today: 1–5, 7–14, 16–22 (20 of 22); control 6 (source-digest freshness) awaits a source-fetch mechanism, control 15 rides the state machine.
- `SHADOWED`: the family is run retrospectively on historical BADF findings (the authority-downgrade defect, schema drift, foreign-revision resolution, the composed-tree reds of 2026-08-28) without knowing the answer; `examples/research-record.json` is the first such shadow record.
- `APPROVED` / `ACTIVE`: owner and security approval; registry digest pinned. Until then the registry entry stays `DESIGNED`.
