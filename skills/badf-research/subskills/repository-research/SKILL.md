---
name: repository-research
description: Investigate a repository -- its commits, branches, PRs, issues, workflows, configs, tests, decision records, evidence and historical revisions -- to answer a BADF research question, binding every finding to a commit SHA. Use for research types R02 (repository investigation) and R03 (root cause). Do not use for external/web research (deep-research), for solution options (technical-research), or to decide or authorise anything.
---

# repository-research

A subskill of `badf-research` (`../../SKILL.md`). It produces a research record of type `R02`
or `R03` at `work/research/<BADF-RSR-NNNN>/research-record.json` against
`schemas/research-record.schema.json`. It has no authority; its output is evidence for a
decision, never a decision (RSR-I01).

**The invariant: current state is not historical evidence.** Every finding is bound to a
`revision` (a commit SHA that resolves in the repo) and, where possible, a path and line. A
claim read from the working tree is `OBSERVED` only against the commit it was read at; a claim
about *why* a change happened is `INFERRED` from the commits/PRs that made it.

1. **FRAME** — from the demand, state the research question, type (R02/R03), depth, scope and
   non-goals. Fix the `baseline`: the repository and the commit the investigation is anchored to.
   The baseline commit MUST resolve in the repository (the gate enforces this, control 3).
2. **DISCOVER** — read the repository as evidence: `git log`, `git blame`, the diff of the
   suspect commits, the PRs and issues that reference them, the workflows and CI runs, the
   decision records and prior evidence. Prefer primary sources (the commit, the run log, the
   spec) over reports of them.
3. **BIND** — each source carries its `uri` (e.g. `git:<repo>@<sha>:<path>`), `source_type`
   (a commit or run log is `PRIMARY`), `retrieved_at`, and a digest where the bytes are
   retrievable. A changed source digest makes dependent claims stale.
4. **CLAIM** — every material statement is a claim: `OBSERVED` (measured against a commit),
   `REPORTED`, `INFERRED`, `HYPOTHESIS` or `DECIDED`; with supporting and contradicting
   sources; a status; and a confidence DERIVED from its basis, never asserted.
5. **HYPOTHESISE (R03)** — for root cause, list hypotheses, find the discriminating commit or
   test, and eliminate or retain each on evidence — not a guessed fix.
6. **SYNTHESISE** — findings reference claims; contradictions are preserved, not buried;
   non-coverage names every surface not read.
7. **CHALLENGE** — at depth D4/D5, an independent council (never the researcher) reviews;
   each ballot declares its non-coverage.
8. **RECONCILE** — return a controlled disposition. `RESEARCH_SUFFICIENT` makes a decision
   *eligible*; it authorises nothing. The next object is a decision record, then a work package.
9. **VALIDATE** — `python3 scripts/badf_gate.py research work/research/<id>/research-record.json`.
   Exit 0 is the only pass; a refusal names the defect.

Never translate a repository finding into a change. Read, bind, conclude — a human decides.
