---
name: evidence-synthesis
description: Transform adjudicated claims, contradictions and non-coverage into decision-relevant findings -- organised by consensus, strength, dispute and gap, not source-by-source. Use after claims are bound and (where required) fact-checked, before challenge and reconciliation. It produces findings; it does not acquire evidence, decide, or authorise anything.
---

# evidence-synthesis

A subskill of `badf-research` (`../../SKILL.md`). It reduces the record's `claims`, `contradictions`
and `non_coverage` into `findings` in the research record at
`work/research/<BADF-RSR-NNNN>/research-record.json` against `schemas/research-record.schema.json`.
It has no authority; a finding is decision-relevant evidence, never a decision (RSR-I01).

**It organises evidence, it does not accumulate it.** The output is not "source A says … source B
says …" but findings grouped by **consensus**, **strong** vs **weak** evidence, **contradiction**,
**outlier**, **unknown** and **evidence gap**, each carrying its **decision implication**.

**Its integrity invariant: every finding is grounded in the claims it synthesises.** A finding
references at least one claim; it is a conclusion drawn *from* adjudicated evidence, never a free
assertion (control 22). Contradictions are surfaced in the finding, not buried (RSR-I04); what the
evidence does not cover is declared in `non_coverage`, not silently closed.

## Do

1. Read the record's `claims` (with their fact-checked `status`), `contradictions` and `non_coverage`.
2. Cluster claims by what they bear on; within each cluster separate agreement from dispute and strong evidence from weak.
3. Write each **finding** as a decision-relevant statement, referencing the claim(s) it rests on (`claim_refs`, non-empty).
4. Preserve every contradiction the cluster contains -- a finding that ignores an available contradiction is invalid.
5. Name the **unknowns** and **evidence gaps** the synthesis exposes; add them to `non_coverage` where they were not already declared.
6. State each finding's **decision implication** without choosing the decision -- direction, not authority.
7. Hand the findings to `adversarial-research` (challenge) and `research-reconciliation`; grant no downstream authority.
