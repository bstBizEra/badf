---
name: comparative-evaluation
description: Evaluate the candidate alternatives against explicit, comparable criteria and produce an evidence-backed trade-off -- surfacing non-dominance rather than manufacturing a winner. For research type R07 (comparative). It compares; it does not gather evidence (deep-research), decide, or authorise. A recommendation is epistemic weight, never execution authority.
---

# comparative-evaluation

A subskill of `badf-research` (`../../SKILL.md`). It takes the `alternatives` an earlier
`technical-research` run produced and weighs them against explicit criteria, recording the outcome
in the research record at `work/research/<BADF-RSR-NNNN>/research-record.json` against
`schemas/research-record.schema.json`. It has no authority; a `recommendation` is evidence for a
decision, never a decision (RSR-I01).

**Research gathers; comparison decides between.** A `COMPARATIVE` (R07) run weighs **at least two**
alternatives — a comparison of one option is not a comparison (control 24). It scores them on
explicit, comparable dimensions (correctness, deterministic behaviour, security, maintainability,
auditability, agent-compatibility, operational complexity, cost, vendor lock-in, reversibility),
each backed by the record's evidence.

**It surfaces non-dominance rather than manufacturing a winner.** When the evidence does not justify a
single choice, that is the finding — the `recommendation` may be null and the trade-off stands. A
recommendation carries epistemic weight, never authorization: `RESEARCH_SUFFICIENT` still hands off to
a separate decision authority, and `implementation_authority` stays `false`.

## Do

1. Read the `alternatives` (`technical-research`) and the record's evidence.
2. Fix the **criteria** before scoring — explicit, comparable dimensions the decision actually turns on.
3. Score each alternative on each criterion from the bound evidence; record the trade-off, not a bare verdict.
4. Identify **dominance / non-dominance**: an alternative that is at least as good on every criterion and better on one dominates; where none dominates, say so.
5. Write a `recommendation` only where the evidence justifies one; otherwise leave it null and let the non-dominance stand.
6. Hand the trade-off to `adversarial-research` (challenge) and `research-reconciliation`; grant no downstream authority.
