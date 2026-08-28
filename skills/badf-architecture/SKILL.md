---
name: badf-architecture
description: Govern architecture design, architectural decisions, architecture fitness and drift assurance for BADF-controlled delivery. Use when a system's structure, boundaries, decisions, NFR allocation or operability must be designed (DESIGN), or when an implementation, PR, branch or composed tree must be checked against declared architectural intent (ASSURE). Do not use to approve a gate, advance lifecycle state, or authorise implementation.
---

# BADF Architecture

Status: `DESIGNED` (contract frozen by `BADF-WP-0043`; nothing here runs yet). This is an architecture **engineering + assurance** capability, not a diagram skill. Its primary lifecycle gate is **G04 — Architecture, Data and API**; it also feeds G05 (trust boundaries + data flows), G08/G09 verification and post-merge drift review.

Fundamental rule — four distinctions that never collapse:

```text
Architecture documentation  ≠  Architecture assurance
Architecture assurance      ≠  Gate authority
Architecture approval       ≠  Implementation authorization
```

`badf-architecture` produces architecture artifacts and assurance evidence consumed by the canonical BADF gate. It does **not** approve G04 and does **not** advance lifecycle state. A human and the gate do that.

## Two modes

- **DESIGN** — create intended architecture: a canonical baseline, C4 views, boundaries, trust boundaries, data flows and ownership, interfaces, ADRs, NFR allocation, operability and architecture-fitness obligations. Workflow and contract: `references/design-mode.md`.
- **ASSURE** — test whether reality conforms to that intent: dependency direction, boundary violations, cycles, ADR compliance, drift, NFR coverage, operability, declared non-coverage. **Read-only unless mutation is separately demanded and authorized.** Workflow and contract: `references/assure-mode.md`.

## Do

1. Read the repository `AGENTS.md` and the documents it marks required.
2. Route DESIGN vs ASSURE from the request; this file is the only router ("design/C4/topology/create ADR" → DESIGN; "review/drift/boundaries/cycles/ADR compliance/fitness" → ASSURE).
3. In DESIGN, treat the structured **architecture baseline** as the source of truth (`references/architecture-model.md`); C4/Mermaid/Structurizr are **views** (`references/c4-contract.md`). A diagram must never introduce a claim absent from the baseline.
4. Give every material relationship a direction and intent; make every material system/module/data/trust boundary explicit; keep assumptions separate from facts, and route material uncertainty to `badf-research` rather than guessing.
5. Record material decisions as `ADR-NNNN` (`references/adr-contract.md`) — never conflated with a governance `BADF-DEC-NNNN`; allocate every architecture-relevant NFR (ALLOCATED / DEFERRED_WITH_REASON / NOT_APPLICABLE_WITH_REASON) to a mechanism and a later fitness obligation (`references/architecture-fitness.md`).
6. In ASSURE, bind every conclusion to one explicit baseline and one observed revision; never infer an architecture from code and declare that inference compliant; report drift as evidence, never authorise it; declare what you did not inspect.
7. Package the five G04 evidence types coherently (`references/g04-contract.md`) without claiming a C4 diagram alone satisfies G04. The gate renders the verdict.

Invariants `ARCH-I01`..`ARCH-I12`, the acceptance controls and the admission ladder: `references/acceptance.md`. External methodology disposition: `references/external-methodology.md`.
