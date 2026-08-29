# Requirements decomposition — the RTM authoring model

Status: **SKILL REFERENCE — authoring model, not a gate schema.**

This is how `badf-requirements` *authors* a Requirements Traceability Matrix. It is a thinking model,
not a second gate contract. The **canonical G02 gate** (`badf_gate.py`, `BADF-WP-0041`) is the sole
authority on what is *enforced*; this reference names both, and is explicit about the gap.

## The authoring chain

Decompose an approved PRD baseline down this spine, and never collapse product intent into
implementation tasks:

```text
OBJ → CAP → EPIC → REQ → AC → TEST → EVDREQ      (delivery spine)
              REQ → NFR → AC → TEST → EVDREQ      (quantified NFR overlay)
              SRC → REQ                            (security/compliance provenance)
```

| Prefix | Node | Purpose |
| --- | --- | --- |
| `OBJ-` | PRD objective | approved upstream outcome |
| `CAP-` | Capability | a product/system ability an objective needs |
| `EPIC-` | Epic | a coherent delivery slice of a capability |
| `REQ-` | Requirement | an atomic functional / data / security / compliance obligation |
| `NFR-` | Non-functional requirement | a quantified quality/constraint obligation |
| `AC-` | Acceptance criterion | an observable pass/fail condition |
| `TEST-` | Test obligation | a verification that must eventually run |
| `EVDREQ-` | Evidence requirement | proof that must exist for a test claim |
| `SRC-` | Security/compliance source | a threat, compliance, privacy or abuse-case driver |

Ids are stable identities; statements evolve only through a new RTM version with supersession.
Requirement-to-requirement sequencing belongs in `dependencies`, never in a traceability edge.

## What the gate consumes today (the canonical subset)

**The G02 gate enforces only the lean subset of this model** — deliberately (PR #71 deferred the
capability/epic hierarchy). Author toward these four artifacts; the gate opens each one:

| Artifact | Canonical rule the gate enforces |
| --- | --- |
| `requirements` | unique `REQ-…`, each with a statement, priority, `testable`, and `objective_refs` to ≥1 objective |
| `nfr` | each `NFR-…` carries a real, quantified target value |
| `traceability` | the bidirectional RTM — `requirement_to_objective` + `criterion_to_requirement`, complete: no orphan requirement, no uncovered acceptance criterion, no dangling id |
| `definition-of-ready` | a **human** sign-off whose checklist covers every one of G02's own `exit_criteria` |

So the gate's live graph is `OBJ ← REQ → NFR`, `REQ ↔ AC`, plus the human readiness sign-off.

## The gap, held honestly

`CAP`, `EPIC`, `TEST`, and `EVDREQ` are **authoring intermediates**, not first-class gate objects
today. Use them to reason your way from an objective to a testable requirement; do not expect the gate
to enforce them, and **do not add a schema for them here**. If real project use proves that
capability/epic (or test/evidence obligations) need machine enforcement, that is a **separate
failing-first work package** against the canonical gate — not schema growth by speculation, and never
a second validator beside `badf_gate.py`.
