# Acceptance and admission

Status: frozen contract v0.1. The capability's **live status is `badf/skill-registry.json`** (currently `ACTIVE`, reached at `BADF-WP-0058`) — this document defines the contract, not the status, so it never re-asserts a status line that can drift from the registry. Progression follows `docs/07-skills-governance.md`: `DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → APPROVED → ACTIVE`.

## Controls (deterministic, in the gate and its tests)

Controls 1–26 were the bar for `VALIDATED`. Control 27 extends the frozen contract after activation (RSR-I06, `BADF-WP-0061`): it only ever refuses more, never approves more, so it hardens an `ACTIVE` capability without re-opening its admission.

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
| 21 | a claim's status is consistent with its evidence (the `fact-checking` invariant): a `FALSIFIED` claim carries a contradicting source (no evidence ≠ false), and a `DISPUTED` claim carries both supporting and contradicting sources (support and contradiction coexist). Whether a source's *content* entails the claim is not machine-checkable here — that boundary is now frozen as RSR-I06 and given teeth by control 27 |
| 22 | a finding is grounded (the `evidence-synthesis` invariant): every finding references at least one claim — a synthesis conclusion rests on adjudicated evidence, not free assertion |
| 23 | a technical-solution run yields grounded options (the `technical-research` invariant): an `R04` record carries at least one `alternative`, and every id-shaped `evidence_ref` resolves to a claim, finding or source the record holds |
| 24 | a comparison weighs at least two options (the `comparative-evaluation` invariant): a `COMPARATIVE` (R07) record carries two or more `alternatives` |
| 25 | an independent refutation is not erased by declaring sufficiency (the `adversarial-research` invariant): a challenge council carrying a `REFUTED` ballot cannot reconcile to `RESEARCH_SUFFICIENT` |
| 26 | sufficiency means synthesis (the `research-reconciliation` invariant): a `RESEARCH_SUFFICIENT` record carries at least one finding -- research declared sufficient on nothing synthesised is incoherent |
| 27 | semantic support is never represented in silence (RSR-I06, `SOURCE_EXISTS != SOURCE_SUPPORTS_CLAIM`): a `VERIFIED` claim on cited support declares `semantic_support` — either `ASSESSED` (a `support_assessments` receipt with a non-empty locator, produced by `fact-checking`, for each supporting source) or `NON_COVERAGE` (the honest fallback: entailment was not machine-verified). A receipt the record's own assessment does **not** substantiate (`NOT_SUBSTANTIATED`, or a non-supporting relation) cannot back a `VERIFIED` binding. The gate verifies the assessment happened under contract; it never asserts the source entails the claim — `semantic_support` and `support_assessments` are a *reading*, excluded from the `evidence_digest` like findings/disposition |
| 28 | an empirical run measures something (the `experimental-research` invariant, `BADF-WP-0062`): an `R08` (`EMPIRICAL_EXPERIMENT`) record carries at least one experiment, and every experiment — in any record — tests a hypothesis the record actually holds (`hypothesis_ref` resolves). A controlled run that measured nothing, or an experiment on a hypothesis the record never stated, is not an experiment. Mirror of controls 23/24 |

### RSR-I06 — citation ≠ support

The deterministic gate verifies four evidence states — a source **exists** (schema + id), is **bound** to a claim (referential integrity), is **current** (`freshness`, control 6), and has been **adjudicated** (status consistency, control 21). It does **not** prove `SOURCE_SUPPORTS_CLAIM`: whether natural-language content semantically entails a claim is an evidence-assessment judgment made by `fact-checking`, recorded as a `support_assessments` receipt or declared non-coverage — never a policy-engine assertion. RSR-I06 grants no implementation authority (RSR-I01 unchanged). The four states are set out in `references/evidence-contract.md`.

## Admission

- `IMPLEMENTED`: the nine P0 subskills exist as concise `SKILL.md` files under this family. **Now met (9 of 9):** `repository-research`, `problem-framing`, `fact-checking`, `evidence-synthesis`, `deep-research`, `technical-research`, `comparative-evaluation`, `adversarial-research`, `research-reconciliation`. **P1:** `experimental-research` (the 10th subskill, `BADF-WP-0062`) is also `IMPLEMENTED` — it completes the type coverage (`R08`) and earns control 28. The family status is unchanged by a subskill addition (two-tier model).
- `VALIDATED`: the 26 controls above pass as gate tests with mutation. **Now met: all 26 enforced (1–26).** (Control 15 landed with RSR-004/`BADF-WP-0038`; the earlier admission note that mistracked it as pending is corrected here.) IMPLEMENTED (9/9 subskills), VALIDATED (all 26 controls with mutation) and SHADOWED (`BADF-WP-0055`) are met.
- `SHADOWED`: the family is run retrospectively on real historical BADF cases without knowing the answer. **Shadow evidence produced (`BADF-WP-0055`):** three gate-valid records over distinct cases and controls -- `research-record-shadow-control15.json` (R02: the control-15 mistracking, baseline `e7ea929`), `research-record-shadow-composed-red.json` (R03 root-cause: the composed-tree red at `30186c5`), `research-record-shadow-ci-parity.json` (R10: `local-green != CI-green`, FALSIFIED with the contradiction preserved). See `references/shadow-evidence.md`. Advancing the family to `SHADOWED` is the operator's admission decision.
- `APPROVED` / `ACTIVE`: **reached (`BADF-WP-0058`).** Owner + security approval given (single-collaborator repo; the owner is also the security reviewer) and the registry digest is pinned. The family root `badf-research` is `ACTIVE` (its nine subskills remain `IMPLEMENTED` -- a two-tier model: family = capability admission, subskill = implementation status). It grants no implementation authority even when ACTIVE (RSR-I01). Control 27 (RSR-I06, `BADF-WP-0061`) hardened the contract after activation — it closes the `SOURCE_EXISTS != SOURCE_SUPPORTS_CLAIM` boundary that #84 (GOV-0031) recorded as an open design decision. Activation is retained: control 21 had already declared that boundary outside its coverage, so no hidden control was ever claimed; #84 was a governance-closure defect (the discovery was not formally dispositioned before activation), now resolved.
