---
name: badf-requirements
description: Decompose an approved PRD baseline into the four canonical BADF Gate G02 evidence artifacts — requirements, quantified NFRs, a bidirectional traceability matrix (RTM), and a definition-of-ready packet. Use when converting product objectives into testable, traceable requirements for a G02 decision. Do not use to approve G02, replace PRD authority, design architecture, create implementation work packages, or decide any gate.
---

# BADF Requirements

This skill authors the four G02 evidence artifacts for an independent BADF `G02` decision. It has
**no gate authority** and **no validator of its own**: the canonical gate opens the artifacts
(`docs/01-lifecycle-gates.md`, *G02 evidence contract*; `BADF-WP-0041`). It owns the RTM *contract*,
not the G02 *authority* — it authors, the gate verifies, an authority decides.

## Invariants

```text
REQ-I01 — No Gate Authority
  badf-requirements may create, normalize, decompose and repair G02 evidence.
  It MUST NOT: emit a G02 PASS or an "eligible-for-review" verdict; advance
  lifecycle state; approve Definition of Ready; impersonate product_owner;
  modify gate policy; or weaken G02 acceptance criteria.

REQ-I02 — PRD Traceability
  Every material requirement traces to an approved G01 objective, or to an
  explicitly declared external requirement source.

REQ-I03 — Testability
  Every priority requirement is testable and carries downstream acceptance and
  test obligations.

REQ-I04 — Quantified NFRs
  A qualitative NFR ("fast", "secure", "scalable", "highly available") is
  incomplete until a measurable threshold exists (metric, operator, target, unit,
  method).

REQ-I05 — Bidirectional RTM
  PRD objective <-> requirement <-> acceptance criterion must remain
  reconstructable in both directions; no orphan requirement, no uncovered
  criterion, no dangling id.

REQ-I06 — Security Provenance
  A security/privacy/compliance requirement introduced after G01 retains its
  originating threat, privacy, compliance or policy provenance.
```

## Preconditions

1. Read repository `AGENTS.md`, `docs/00-operating-model.md`, `docs/01-lifecycle-gates.md`, `docs/05-evidence-and-provenance.md`, and `docs/07-skills-governance.md`.
2. Resolve the active work package and confirm requirement decomposition is in scope, with `G02` as the gate.
3. Require a versioned upstream PRD baseline carrying `G01` disposition and approval evidence. Treat it as an input claim; never manufacture or upgrade G01 authority.
4. If the PRD baseline is absent, stale, contradictory, or not approved, stop and report the missing upstream condition.

## Workflow

`FRAME → INGEST → CLARIFY → DECOMPOSE → QUANTIFY → TRACE → CHALLENGE → VALIDATE → EVIDENCE → DELIVER`

1. **FRAME** — bind the task to work package, `G02`, source revision, PRD baseline, change/data class, and the authority boundary.
2. **INGEST** — enumerate every approved PRD objective (`OBJ-…`) and its immutable baseline reference.
3. **CLARIFY** — surface ambiguity in functional scope, interaction, technical constraints, business value, acceptance, dependencies, and security/compliance sources. Do not invent answers.
4. **DECOMPOSE** — author the `requirements` artifact: unique `REQ-…`, each with a statement, priority, `testable`, and `objective_refs` to ≥1 objective (REQ-I02). Use `references/requirements-decomposition.md` for the authoring model.
5. **QUANTIFY** — author the `nfr` artifact: every quality/constraint obligation gets a measurable target (REQ-I04).
6. **TRACE** — author the `traceability` artifact: the bidirectional RTM (`requirement_to_objective`, `criterion_to_requirement`) — complete, no orphan requirement, no uncovered acceptance criterion (REQ-I05). Security/compliance requirements carry their provenance (REQ-I06).
7. **CHALLENGE** — record unresolved decisions and review findings; blockers stay explicit. Silence is not completeness.
8. **VALIDATE** — assemble the G02 dossier with the four evidence records and run `python3 scripts/badf_gate.py dossier <dossier>`. Exit 0 is the only pass; a refusal names the defect. **There is no `badf-requirements` validator** — the canonical gate is the sole G02 authority.
9. **EVIDENCE** — the `definition-of-ready` packet is a **human** sign-off whose checklist covers every one of G02's own exit criteria; the requirements author must not produce it (REQ-I01).
10. **DELIVER** — report the gate's verdict and the unresolved items. Never emit a G02 outcome, a "ready" score, or an approval as this skill's own decision.

Read `references/requirements-decomposition.md` for the RTM authoring model (and which of its nodes the gate consumes today) and `references/methodology-provenance.md` for adapted external methodology. This skill is `IMPLEMENTED`; its status lives in `badf/skill-registry.json`.
