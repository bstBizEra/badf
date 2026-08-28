---
name: badf-research
description: Govern evidence-based research for BADF questions, issues, defects, architecture uncertainties, solution alternatives, repositories, technologies, standards and claims. Use when material uncertainty must be reduced before a BADF decision, work package, implementation, policy change or other consequential action. Do not use to decide, authorise, or implement.
---

# BADF Research

Status: `DESIGNED` (contract frozen by `BADF-WP-0031`). The `research` gate command enforces the record contract, and the `problem-framing`, `repository-research` and `fact-checking` subskills exist; the family is not yet activated for autonomous use (3 of 9 P0 subskills). Research determines what the evidence supports; `badf-delivery` governs what authorised actors may do with that conclusion.

1. Read the repository `AGENTS.md` and the documents it marks required.
2. Resolve the research question, the originating Issue and its demand record, the research type and depth (`references/research-types.md`), scope and non-goals, source and data boundaries, authority and mutation constraints, required evidence, and the bounded scope contract — non-empty **stop conditions** (when the run stops), the **assumptions** it rests on (kept distinct from evidence), and the **decision it serves** — all first-class in the record (`schemas/research-record.schema.json`, control 19).
3. Establish the baseline — repository, revision, observation time — before drawing any conclusion.
4. Route only the subskills the type and depth require, starting from `problem-framing` (the entry subskill that bounds the question before any evidence is collected) then the type's investigator (`repository-research`, …); this file is the only router.
5. Keep `OBSERVED`, `REPORTED`, `INFERRED`, `HYPOTHESIS` and `DECIDED` distinct (`references/evidence-contract.md`).
6. Bind every consequential claim to retrievable, digest-bound evidence; derive confidence from its basis, never assert it.
7. Seek contradictory evidence and preserve it; declare every surface not inspected.
8. Require independent challenge proportional to risk through the framework's council (`references/routing-and-authority.md`); never ballot on your own research.
9. Reconcile and return a controlled disposition (`references/lifecycle.md`); record it in `work/research/<BADF-RSR-NNNN>/research-record.json` against `schemas/research-record.schema.json`.
10. Never translate `RESEARCH_SUFFICIENT` into implementation authority. The next object is a decision record, then a work package — authored by their own authorities.

Admission and the controls required before this skill may run: `references/acceptance.md`.
