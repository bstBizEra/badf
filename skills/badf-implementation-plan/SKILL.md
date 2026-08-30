---
name: badf-implementation-plan
description: Compose an approved BADF design (G01–G05) into a governed Work Package DAG — bounded, authorized, independently verifiable execution units — and normalize the plan into the existing G06 evidence (work-breakdown, test-plan, release-plan, rollback-plan). Use when approved requirements/architecture/solution/security must become executable work. Do not use to execute the work, run a scanner, decide a gate, grant authority, add a fifth G06 artifact, realize Git topology, or turn a task/issue/branch into authority.
---

# BADF Implementation Plan

`badf-implementation-plan` is the **planning composition and orchestration layer** for G06. It turns an
approved design into a **governed Work Package DAG** — the point where BADF stops thinking in "tasks" and
starts producing bounded, governable execution units — and normalizes that plan into the **existing** G06
evidence. It is a router and constraint contract, **not** an execution engine, a second gate, a Git
realizer, or a source of authority.

Its live status is `badf/skill-registry.json`; this file defines the contract, not the status, and never
hardcodes a lifecycle status that can drift from the registry.

## Canonical principle

```text
A specification states what is required.
Architecture, solution and security design define what may be built.
An implementation plan determines how the approved design is decomposed into deliverable units.
A task is an execution step.  A ticket is a tracking projection.
A Governed Work Package is the bounded unit of authorized work.
The BADF gate validates the plan.  Only valid authority permits execution.
```

## The doctrine this skill freezes

```text
Task              ≠ Work Package
GitHub Issue      ≠ Work Package
Branch            ≠ Work Package
Implementation Plan ≠ Authority

Governed Work Package = the bounded execution contract
  (scope · acceptance · authority · risk · dependencies · expected surfaces ·
   tests · evidence · budget · rollback · stop conditions)
```

A task is implementation detail *inside* a Work Package. A GitHub Issue is a **projection** for tracking
and collaboration — opening or closing it never grants or revokes authority (IMP-I14).

## Boundaries

- **Composes G06's existing four artifacts; adds no fifth.** `badf-implementation-plan` authors and
  reconciles `work-breakdown`, `test-plan`, `release-plan` and `rollback-plan`; the canonical
  `badf_gate.py` validates them and `engineering_owner` dispositions the G06 dossier. No new gate, no
  `lifecycle.json` change.
- **Authority is derived, never chosen.** Required authority comes from the existing `change_class`
  (C0–C3) and the authority matrix — the plan **cannot reduce** it (IMP-I07). There is **no** parallel
  A0/A1/A2 authority-class system.
- **Declares execution topology; does not realize it.** The plan **declares** isolation / branch-class /
  workspace policy; **`badf-git`** realizes worktree creation, branch identity, baseline, staleness,
  composition and landing (§10). Planning and Git governance stay separate.
- **No execution engine, no second validator.** No `scripts/badf_implementation_plan.py`; deterministic
  G06 semantics live in the canonical gate (IMP-I17). The skill plans; it does not execute the work it
  planned (IMP-I15).
- **Does not duplicate G01–G05.** Requirements/UX/architecture/solution/security are consumed as exact
  baselines, not rediscovered (IMP-I02).

## Invariants (IMP-I01 … IMP-I17)

```text
IMP-I01  No naked task         every executable planning unit resolves to exactly one Governed Work Package
IMP-I02  Exact upstream baseline  every WP binds the exact requirements/design/security inputs it implements
IMP-I03  Acceptance coverage    every WP has measurable acceptance; every planned requirement is covered or explicitly deferred
IMP-I04  Vertical slice default a WP delivers an independently verifiable outcome; horizontal decomposition needs explicit rationale
IMP-I05  Dependency DAG         blocking dependencies are valid, resolve, and are acyclic
IMP-I06  Composition explicit   landing/composition order is represented separately from execution blockers
IMP-I07  Authority derived      the plan cannot reduce the authority required by change class, reserved actions, target env or upstream
IMP-I08  Expected surface bounded  files/services/interfaces/data expected to change are declared
IMP-I09  Test binding           every acceptance claim has a verification obligation
IMP-I10  Evidence binding       every material claim identifies the evidence required to prove it
IMP-I11  Budget mandatory       autonomous execution has bounded attempts and time/cost
IMP-I12  Stop contract mandatory  authority, safety, integrity and budget stop conditions are explicit
IMP-I13  Rollback/recovery      each WP declares reversibility or explains its irreversibility and its recovery mechanism
IMP-I14  Tracker ≠ authority    GitHub Issue state cannot grant mutation or lifecycle authority
IMP-I15  Planning ≠ execution   badf-implementation-plan cannot execute its own WPs merely because it created them
IMP-I16  Stale baseline blocks  a WP planned against superseded material input cannot silently become READY
IMP-I17  No second gate         no scripts/badf_implementation_plan.py; deterministic G06 semantics live in the canonical gate
```

See `references/work-package-contract.md` for the Governed Work Package shape and
`references/dependency-graph.md` for the DAG and the execution frontier.

## The default topology, and its exceptions

```text
DEFAULT              vertical tracer-bullet WP (an independently verifiable slice)
EXCEPTION  wide mechanical refactor   → expand / migrate / contract WP sequence
EXCEPTION  irreducible migration      → explicitly ordered integration sequence
EXCEPTION  material uncertainty       → badf-research before implementation
```

Horizontal decomposition is allowed only with explicit rationale (IMP-I04); see
`references/vertical-slicing.md`.

## Lifecycle placement

`badf-implementation-plan` composes into the **existing G06** (**Implementation planning**, owner
`engineering_owner`, min `C1`) — it adds **no** gate and changes **no** `lifecycle.json`:

```text
G01–G05 approved design → badf-implementation-plan → { work-breakdown ; test-plan ; release-plan ; rollback-plan }
                                                     engineering_owner dispositions the G06 dossier
```

## Workflow

`FRAME → INGEST → CLASSIFY → DECOMPOSE → SLICE → GRAPH → GOVERN → PROJECT → PACKAGE`

1. **FRAME** — scope the plan and its authority boundary; it is planning, not execution.
2. **INGEST** — the approved G01–G05 baselines; bind their exact digests (IMP-I02).
3. **CLASSIFY** — per-unit `change_class`, risk factors, target environment; derive the authority
   requirement from the matrix (IMP-I07).
4. **DECOMPOSE** — approved design → candidate deliverable units; every unit becomes exactly one
   Governed Work Package (IMP-I01), never a naked task.
5. **SLICE** — vertical tracer-bullet by default; wide refactors take expand/migrate/contract; material
   uncertainty routes to `badf-research` (IMP-I04).
6. **GRAPH** — the Work Package DAG: `blocked_by` / `composition_after` / `requires_artifact` /
   `conflicts_with` edges, acyclic (IMP-I05/I06); derive the **execution frontier** (READY WPs whose
   blockers are CLOSED, baselines current, authority present).
7. **GOVERN** — each WP carries scope, acceptance, expected surfaces, tests, evidence, **budget** and
   **stop conditions** (IMP-I03/08/09/10/11/12); rollback or a declared recovery mechanism (IMP-I13).
8. **PROJECT** — emit the GitHub-issue projection: a tracking view, never authority (IMP-I14).
9. **PACKAGE** — normalize into the four **existing** G06 artifacts; the canonical gate validates them and
   `engineering_owner` dispositions the dossier. Never emit a gate outcome, and never execute the plan.

Read `references/acceptance.md` for the admission controls and the WP-IMP-A…E ladder, and
`references/external-methodology.md` for the Spec Kit / Superpowers / Matt Pocock `to-tickets`
dispositions (reference-only). This skill has **no authority of its own**: it composes and constrains;
the canonical gate validates and authority decides.
