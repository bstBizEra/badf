---
name: badf-solution-design
description: Compose the detailed specialist design contracts — UX/service behavior, authorization, data, API, accessibility — into one coherent, implementable solution for a BADF work package, and reconcile the seams between them. Use when a requirement (G02) must become detailed G03/G04 design and the specialist artifacts must agree. Do not use to invent architectural boundaries, decide a gate, replace a specialist, or generate a monolithic design document.
---

# BADF Solution Design

`badf-solution-design` is the **composition and orchestration layer** for detailed solution contracts. It
routes each concern to its specialist, assembles their outputs into one solution, and **reconciles the
seams** — it is a router and constraint contract, **not** a sixth architecture skill, a new gate, a
second validator, or a document-generation mega-skill.

Its live status is `badf/skill-registry.json`; this file defines the contract, not the status, and never
hardcodes a lifecycle status that can drift from the registry.

## Canonical principle

```text
Requirements define WHAT must be satisfied.
Architecture defines WHERE responsibilities, boundaries and major mechanisms live.
Specialist design defines HOW each concern behaves.
badf-solution-design composes those specialist contracts into one coherent implementable solution.
The canonical gate validates evidence.
Authority decides whether delivery advances.
```

**Its primary job is consistency, not generation.** Five individually-reasonable designs can compose a
broken solution — UX asserts an action authorization denies, an API operation with no data state behind
it, a failure conveyed only by color. The value is `SPECIALIST DESIGN → CROSS-CONTRACT RECONCILIATION →
CONSISTENT SOLUTION`.

## Boundary with badf-architecture

`badf-architecture` is the **structural spine and G04 coherence authority** (boundaries, topology, trust,
ownership, architectural interfaces, ADRs, NFR allocation, fitness). `badf-solution-design` **MAY detail**
an architectural interface; it **MUST NOT invent** an architectural boundary, interface or owner that is
absent from — or inconsistent with — the architecture baseline. When detailed design finds the
architecture insufficient, it does **not** silently fix it:

```text
ARCHITECTURE_CHANGE_REQUIRED → ADR / architecture revision → re-baseline → resume detailed design
```

## Invariants (SOL-I01 … SOL-I12)

```text
SOL-I01  Requirement provenance   every material element resolves to a REQ / NFR / G03 need / arch constraint; no orphan design
SOL-I02  Architecture consistency every API boundary, data owner, external integration, trust transition resolves against the baseline
SOL-I03  UX ↔ API                 a system action a flow requires has an implementable contract or an explicit non-API mechanism
SOL-I04  API ↔ authorization      every protected operation has resource, action, scope, decision point, default behavior
SOL-I05  Default deny             an unmatched authorization tuple resolves to DENY (NO MATCH = DENY)
SOL-I06  Authorization ↔ audit    a security-sensitive authorization decision defines an audit obligation
SOL-I07  API ↔ data               request/response and persistence agree on identity, nullability, cardinality, state, lifecycle, ownership
SOL-I08  UX ↔ error               every material API/domain failure exposed to a user has a recovery state
SOL-I09  Accessibility binds behavior  accessibility binds interaction states (keyboard, focus, semantics, error, state-change), not a checklist
SOL-I10  Migration safety         a breaking persistence change carries a reversible/evolvable migration plan
SOL-I11  API compatibility        a breaking API change is explicitly identified and dispositioned
SOL-I12  No second gate           no scripts/badf_solution_design.py or competing validator; deterministic evidence semantics live in the canonical gate
```

See `references/cross-artifact-consistency.md` for each invariant's seam and the **solution-composition
matrix** (the detailed-design equivalent of the G02 RTM).

## Lifecycle placement

`badf-solution-design` composes into the **existing** gates — it does **not** add a "Detailed Solution
Design" gate. It emits G03 evidence (UX + accessibility) and G04 detailed evidence (API / data /
authorization detail), coherent with the architecture spine:

```text
G02 requirement → badf-solution-design → { UX+a11y → G03 ;  api+data+authz detail → G04 (against the architecture spine) }
```

## Workflow

`FRAME → INGEST → ROUTE → SPECIALIZE → COMPOSE → RECONCILE → CHALLENGE → TRACE → PACKAGE`

1. **FRAME** — scope the detailed solution and its authority boundary.
2. **INGEST** — G01/G02/G03 evidence + the architecture baseline + ADRs + NFRs.
3. **ROUTE** — select only the specialists the work needs (`references/routing.md`); external specialist skills are **reference/adapt**, never BADF authority.
4. **SPECIALIZE** — each specialist produces its domain contract (`references/ux-contract.md`, `authorization-contract.md`, `data-contract.md`, `api-contract.md`, `accessibility-contract.md`).
5. **COMPOSE** — assemble one solution and the composition matrix (`references/composition-contract.md`).
6. **RECONCILE** — detect the cross-contract inconsistencies SOL-I01…I12 name (`references/cross-artifact-consistency.md`); an inconsistency is rework, not a footnote.
7. **CHALLENGE** — failure / error / security / accessibility / evolution review; unresolved decisions stay explicit.
8. **TRACE** — bind each element back to its requirement and forward to test obligations (`references/traceability.md`).
9. **PACKAGE** — emit the canonical G03/G04 evidence; the gate validates it, an authority dispositions it. Never emit a gate outcome as this skill's own decision.

Read `references/acceptance.md` for the admission controls and the WP-SOL-A…D ladder, and
`references/external-methodology.md` for adapted external methodology (reference-only). This skill has
**no authority of its own**: it composes and constrains; the canonical gate validates and an authority
decides.
