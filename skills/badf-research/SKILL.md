---
name: badf-research
description: Govern evidence-based research for BADF questions, issues, defects, architecture uncertainties, solution alternatives, repositories, technologies, standards and claims. Use when material uncertainty must be reduced before a BADF decision, work package, implementation, policy change or other consequential action. Do not use to decide, authorise, or implement.
---

# BADF Research

Status: `DESIGNED`. The contract was frozen by `BADF-WP-0031` and normalized by `WP-2026-0041`. Deterministic research-record controls and individually registered subskills may exist, but the root family is not `ACTIVE` and grants no execution or implementation authority.

1. Read repository `AGENTS.md`, `docs/14-research-capability.md`, and the other documents that `AGENTS.md` marks required for the task.
2. Frame one primary research question from the originating Issue/discovery and its demand record. Record type (`references/research-types.md`), depth (`references/research-depth.md`), scope/non-goals, assumptions, decision context, source/data boundaries, authority/mutation constraints, required evidence and non-empty stop conditions (`references/research-contract.md`).
3. Establish the applicable baseline — repository, revision and observation time — before drawing conclusions.
4. Route only the subskills required by type and depth; this root `SKILL.md` is the only router.
5. Keep `OBSERVED`, `REPORTED`, `INFERRED`, `HYPOTHESIS` and `DECIDED` distinct (`references/evidence-contract.md`).
6. Bind every consequential claim to retrievable evidence; digest retrievable bytes; derive confidence from its basis and never assert agent self-confidence.
7. Seek contradictory evidence and preserve it. Declare every material surface not inspected.
8. Stop collection when a declared stop condition or governed boundary is reached; stopping collection does not imply sufficiency.
9. Require independent challenge proportional to type/depth/risk through BADF's existing council (`references/routing-authority.md`); never ballot on your own required challenge.
10. Reconcile through the research state machine (`references/research-state-machine.md`) and write one record to `work/research/<BADF-RSR-NNNN>/research-record.json` against `schemas/research-record.schema.json`.
11. Never translate `RESEARCH_SUFFICIENT` into implementation authority. The next governed object is a decision record and, if authorized, a separate work package.

Admission and deterministic controls: `references/acceptance-controls.md`.
