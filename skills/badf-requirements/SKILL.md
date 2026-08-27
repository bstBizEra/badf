---
name: badf-requirements
description: Decompose an approved PRD baseline into a governed Requirements Traceability Matrix (RTM) for BADF Gate G02. Use when converting product objectives into capabilities, epics, functional/security requirements, quantified NFRs, acceptance criteria, test obligations, and evidence requirements. Do not use to approve G02, replace PRD authority, design architecture, or create implementation work packages.
---

# BADF Requirements

`badf-requirements` owns the **RTM contract**, not Gate G02 authority.

## Preconditions

1. Read repository `AGENTS.md`, `docs/00-operating-model.md`, `docs/01-lifecycle-gates.md`,
   `docs/05-evidence-and-provenance.md`, `docs/07-skills-governance.md`, and
   `docs/13-artifact-model.md`.
2. Resolve the active work package and confirm requirement decomposition is in scope.
3. Require a versioned upstream PRD-baseline reference carrying G01 disposition and approval
   evidence. Treat the reference as an input claim; do not manufacture or upgrade G01 authority.
4. If the PRD baseline is absent, stale, contradictory, or not approved, stop and report the
   missing upstream condition.

## Workflow

Follow:

`FRAME -> INGEST -> CLARIFY -> DECOMPOSE -> QUANTIFY -> TRACE -> CHALLENGE -> VALIDATE -> EVIDENCE -> DELIVER`

1. **FRAME** — bind the task to work package, G02, source revision, PRD baseline and scope.
2. **INGEST** — enumerate every approved PRD objective and its immutable baseline reference.
3. **CLARIFY** — identify ambiguity in functional scope, user interaction, technical constraints,
   business value, acceptance, dependencies and security/compliance sources. Do not invent answers.
4. **DECOMPOSE** — build the mandatory spine:
   `PRD objective -> capability -> epic -> requirement`.
5. **QUANTIFY** — attach at least one quantified NFR to every requirement. Shared NFRs may link to
   multiple requirements. Each NFR needs metric, operator, target, unit and measurement method.
6. **TRACE** — continue each delivery path through acceptance criterion, test obligation and
   evidence requirement. Security/compliance requirements must trace to threat, compliance,
   privacy or abuse-case sources.
7. **CHALLENGE** — record unresolved decisions and review findings. Blocking open findings and
   unresolved decisions remain explicit; silence is not evidence of completeness.
8. **VALIDATE** — run `python3 scripts/badf_requirements.py <rtm.json>`.
9. **EVIDENCE** — retain the RTM digest and validator output as requirement evidence for the G02
   dossier. Bind evidence to the exact source, target, policy/toolchain epoch and work package.
10. **DELIVER** — report `ELIGIBLE_FOR_G02_REVIEW`, `REWORK_REQUIRED`, or fail-closed validation
    failure. Never emit `G02 PASS`, `DESIGN_READY`, or an equivalent authority decision.

## Canonical traceability

The mandatory delivery spine is:

`OBJ -> CAP -> EPIC -> REQ -> AC -> TEST -> EVDREQ`

The mandatory NFR overlay is:

`REQ -> NFR -> AC -> TEST -> EVDREQ`

Security/compliance provenance is:

`SRC -> REQ`

All canonical nodes must be reachable from an approved PRD objective and must terminate in an
evidence requirement. Bidirectional coverage is computed from the link graph; redundant
hand-maintained reverse links are prohibited.

## Deterministic versus judgment controls

The validator proves structural properties: identity, allowed graph edges, complete coverage,
quantified NFR fields, security-source linkage, dependency acyclicity, placeholder absence and
blocker state. It does **not** prove that a requirement is commercially correct, that a threshold is
the right threshold, or that a product owner should approve G02. Those remain review/authority
judgments.

Read `references/rtm-contract.md` for the canonical graph contract and
`references/external-methodology.md` for methodology provenance.
