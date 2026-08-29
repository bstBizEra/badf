# Acceptance, invariants and admission

Status: frozen contract v0.1. The capability's **live status is `badf/skill-registry.json`** (admitted `ACTIVE` at `BADF-WP-0065`) — this document defines the contract, not the status, so it never hardcodes a status line that can drift from the registry. Progression follows `docs/07-skills-governance.md`: `DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → APPROVED → ACTIVE`.

## Canonical invariants

- **ARCH-I01 — Single baseline.** Every assurance conclusion is bound to one explicit architecture baseline and one observed revision.
- **ARCH-I02 — Views are projections.** C4 and other diagrams cannot become independent architectural truth; a view must not add a claim absent from the baseline.
- **ARCH-I03 — Explicit boundaries.** Material system, module, data and trust boundaries must be represented explicitly.
- **ARCH-I04 — Direction matters.** Material dependencies carry a declared direction and intent.
- **ARCH-I05 — ADR binding.** Material architectural decisions bind to their affected architecture elements and upstream drivers.
- **ARCH-I06 — NFR traceability.** Architecture-relevant NFRs map to architectural mechanisms and to verification obligations.
- **ARCH-I07 — No inferred compliance.** Missing architecture documentation may produce observations, never compliance (`NO BASELINE ≠ COMPLIANT`).
- **ARCH-I08 — Drift is evidence, not authority.** ASSURE identifies drift; it does not authorize it.
- **ARCH-I09 — Exact-revision assurance.** Assessment against an unpinned, moving repository state is invalid for gate evidence.
- **ARCH-I10 — ADR and BADF decision separation.** `ADR-*` cannot replace `BADF-DEC-*`, and vice versa.
- **ARCH-I11 — No second gate.** No standalone `badf_architecture.py` may become a competing validator; deterministic G04 evidence semantics belong in the canonical BADF gate.
- **ARCH-I12 — Assurance is read-only.** ASSURE must not repair source, architecture or ADRs unless mutation is separately demanded and authorized.

## Controls required before `VALIDATED` (deterministic, in the gate and its tests)

| # | Control |
| :--- | :--- |
| 1 | a material relationship without a declared direction is refused |
| 2 | a material relationship without an intent is refused |
| 3 | an architecture element outside every declared boundary is refused |
| 4 | a boundary crossing not through a declared interface is refused |
| 5 | an ADR with no affected element or no decision driver is refused |
| 6 | an ADR referencing an unknown requirement/NFR is refused |
| 7 | an architecture-relevant NFR neither ALLOCATED nor DEFERRED/NOT_APPLICABLE with reason is refused |
| 8 | an NFR allocation with no mechanism and no fitness obligation is refused |
| 9 | a fitness obligation without a measurable property and scope is refused |
| 10 | operability-design that omits failure/recovery/observability is refused |
| 11 | a data flow across a trust boundary with no classification is refused |
| 12 | a C4 view element absent from the baseline is refused |
| 13 | an ASSURE run with no bound baseline + observed revision is refused |
| 14 | an ASSURE conclusion of COMPLIANT with no baseline is refused (ARCH-I07) |
| 15 | an `INDETERMINATE` ADR-compliance result cannot serialise as PASS |
| 16 | a drift finding cannot classify itself as approved evolution |
| 17 | an ASSURE run with no non-coverage declaration is incomplete |
| 18 | architecture-baseline digest changes when a material element/relationship/boundary changes |

## Admission

- `IMPLEMENTED`: the G04 DESIGN evidence semantics (`architecture`, `adr`, `data-model`, `api-contract`, `operability-design`) exist as deterministic gate rules with schemas (WP-ARCH-B).
- `VALIDATED`: **met (`BADF-WP-0057` / WP-ARCH-C).** The ASSURE substrate is deterministic -- controls 13-18 enforced by the `assure` gate command with mutation-tested tests; the `architecture-assurance` record binds one baseline + one observed revision, never infers compliance, never self-authorises drift, and grants no authority. The registry status is advanced to `VALIDATED`.
- `SHADOWED`: **met (`BADF-WP-0059` / WP-ARCH-D).** ASSURE run retrospectively on real BADF architecture cases spanning the outcome space (COMPLIANT stdlib-boundary; NONCOMPLIANT dependency drift; INDETERMINATE unobservable ADR); measured for true violations, false positives, INDETERMINATE handling and declared non-coverage -- no contract gap surfaced. See `references/assurance-shadow-evidence.md`. Registry status advanced to `SHADOWED`.
- `APPROVED` / `ACTIVE`: **reached (`BADF-WP-0065`).** The operator's admission decision, given — owner + security approval (single-collaborator repo; the owner is also the security reviewer) and the registry digest is pinned. `badf-architecture` is `ACTIVE`. It grants **no** authority even when `ACTIVE`: the ARCH-I invariants hold at every status, and `badf_gate.py` remains the sole G04/ASSURE authority (ARCH-I11). An admission advance changes status, not the contract — the DESIGN and ASSURE controls are unchanged.
