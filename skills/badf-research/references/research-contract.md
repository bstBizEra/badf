# BADF Research contract

Status: frozen contract v0.2 (`BADF-WP-0031`, evolved by `WP-2026-0041`). This document defines the boundary of the `badf-research` family. It does not grant tool, decision, gate, implementation or production authority.

## Purpose

BADF Research reduces material uncertainty before a governed decision or delivery action. A research run answers one primary research question with bounded scope, provenance-bound evidence, explicit contradictions and non-coverage, and a controlled disposition.

Research is not delivery. It may establish that evidence is sufficient for a downstream decision process; it cannot make that decision authoritative, create implementation authority, waive a control, merge code, release, deploy or mutate production.

## Required framing

Every material research run records:

- the originating Issue or discovery and its `BADF-DEM-NNNN` demand;
- one primary `question`, `type` and `depth`;
- `scope.include` and `scope.exclude`;
- explicit `assumptions`;
- a non-empty `decision_context` describing the downstream uncertainty being reduced;
- one or more `stop_conditions` that make termination bounded and auditable;
- known facts, unknowns and hypotheses;
- source/data boundaries, mutation constraints and required evidence;
- the repository/revision/observation-time baseline when repository state matters.

A stop condition explains why collection may stop. Reaching one does not imply `RESEARCH_SUFFICIENT`; the run still assesses evidence, challenges when required, and reconciles to a disposition.

## Canonical contract surface

| Concern | Canonical reference |
| :--- | :--- |
| Research types | `research-types.md` |
| Depth / cost / challenge floor | `research-depth.md` |
| States and dispositions | `research-state-machine.md` |
| Sources, claims, confidence and evidence digest | `evidence-contract.md` |
| Routing, council reuse and authority boundary | `routing-authority.md` |
| Validation/admission controls | `acceptance-controls.md` |
| Machine record | `schemas/research-record.schema.json` |
| BADF integration | `docs/14-research-capability.md` |

The root `SKILL.md` is the only router for this family. Subskills implement bounded research workflows; they do not define alternate state, evidence, authority or council mechanisms.

## Output

One run produces one canonical record:

`work/research/<BADF-RSR-NNNN>/research-record.json`

The record is validated against `schemas/research-record.schema.json`. Material evidence is digest-bound. Findings cite claims; claims cite sources; contradictions and non-coverage are preserved.

## Termination

A run terminates only through the research state machine. It must not continue collecting merely because additional sources exist.

Stop when at least one declared stop condition is reached, an authority/tool/data boundary blocks further collection, or the evidence proves that the question must be reframed. Then synthesize, challenge if required, and reconcile.

`RESEARCH_SUFFICIENT` means only that bounded evidence is sufficient to support a governed downstream decision process. It is never equivalent to approval, correctness, gate passage, implementation readiness or authorization.
