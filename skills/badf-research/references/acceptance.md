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
| 6 | a changed source digest makes dependent claims stale: `deep-research` sets each source's `freshness` (CURRENT / STALE / UNKNOWN) on re-resolution, and a claim may not rest on a STALE or UNKNOWN source (fail closed) |
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
| 23 | a technical-solution run yields grounded options (the `technical-research` invariant): an `R04` record carries at least one `alternative`, and every id-shaped `evidence_ref` resolves to a claim, finding or source the record holds |
| 24 | a comparison weighs at least two options (the `comparative-evaluation` invariant): a `COMPARATIVE` (R07) record carries two or more `alternatives` |
| 25 | an independent refutation is not erased by declaring sufficiency (the `adversarial-research` invariant): a challenge council carrying a `REFUTED` ballot cannot reconcile to `RESEARCH_SUFFICIENT` |
| 26 | sufficiency means synthesis (the `research-reconciliation` invariant): a `RESEARCH_SUFFICIENT` record carries at least one finding -- research declared sufficient on nothing synthesised is incoherent |

## Admission

- `IMPLEMENTED`: the nine P0 subskills exist as concise `SKILL.md` files under this family. **Now met (9 of 9):** `repository-research`, `problem-framing`, `fact-checking`, `evidence-synthesis`, `deep-research`, `technical-research`, `comparative-evaluation`, `adversarial-research`, `research-reconciliation`.
- `VALIDATED`: the 26 controls above pass as gate tests with mutation. **Now met: all 26 enforced (1–26).** (Control 15 landed with RSR-004/`BADF-WP-0038`; the earlier admission note that mistracked it as pending is corrected here.) The registry status advance DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → APPROVED → ACTIVE is the operator's admission decision; the family stays `DESIGNED` until then.
- `SHADOWED`: the family is run retrospectively on real historical BADF cases without knowing the answer. **Shadow evidence produced (`BADF-WP-0055`):** three gate-valid records over distinct cases and controls -- `research-record-shadow-control15.json` (R02: the control-15 mistracking, baseline `e7ea929`), `research-record-shadow-composed-red.json` (R03 root-cause: the composed-tree red at `30186c5`), `research-record-shadow-ci-parity.json` (R10: `local-green != CI-green`, FALSIFIED with the contradiction preserved). See `references/shadow-evidence.md`. Advancing the family to `SHADOWED` is the operator's admission decision.
- `APPROVED` / `ACTIVE`: owner and security approval; registry digest pinned. Until then the registry entry stays `DESIGNED`.
