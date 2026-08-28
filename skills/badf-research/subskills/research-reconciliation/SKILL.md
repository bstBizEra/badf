---
name: research-reconciliation
description: The terminal research subskill -- decide whether the evidence is enough to support a governed decision, and return a controlled disposition. Its question is not "what is our recommendation?" but "do we know enough?". It never returns PASS/FAIL, never authorises implementation, and never generates a work package: RESEARCH_SUFFICIENT hands off to a separate decision authority.
---

# research-reconciliation

A subskill of `badf-research` (`../../SKILL.md`). It is the **last** step: after synthesis and
challenge, it sets the record's `disposition` in the research record at
`work/research/<BADF-RSR-NNNN>/research-record.json` against `schemas/research-record.schema.json`.
It has no authority; a disposition is the end of research, never the start of implementation (RSR-I01).

**Its question is "do we know enough?" — not "what do we recommend?".** The controlled dispositions:

```text
RESEARCH_SUFFICIENT        the evidence supports a governed decision
MORE_RESEARCH_REQUIRED     a gap must close first
EXPERIMENT_REQUIRED        a discriminating experiment is needed
PROTOTYPE_REQUIRED         a build is needed to reduce the uncertainty
CONTRADICTORY_EVIDENCE     the evidence conflicts and does not resolve
SOURCE_INSUFFICIENT        the sources cannot bear the weight
EXTERNAL_AUTHORITY_REQUIRED a decision beyond research is needed
NO_ACTION_RECOMMENDED      the evidence supports doing nothing
RESEARCH_BLOCKED           the research itself cannot proceed
```

**`RESEARCH_SUFFICIENT ≠ IMPLEMENTATION_AUTHORIZED`.** Reconciliation makes a record
*decision-eligible*, never *implementation-authorized*. The gate holds the boundary: only a
`RESEARCH_SUFFICIENT` record may name a downstream work package (control 15); a `REFUTED` challenge
forecloses sufficiency (control 25); and **sufficiency means the evidence was synthesised into at
least one finding** — a `RESEARCH_SUFFICIENT` record carries findings (control 26). The next object is
a `BADF-DEC-*` decision, then a `BADF-WP-*`, authored by their own authorities.

## Do

1. Read the record's findings, contradictions, non-coverage and the challenge outcome.
2. Ask **do we know enough to support a governed decision?** — not what the recommendation is.
3. Choose the controlled disposition above from the evidence; a `REFUTED` challenge cannot reconcile to `RESEARCH_SUFFICIENT`.
4. If `RESEARCH_SUFFICIENT`, confirm the record carries synthesised findings; otherwise it is not sufficient.
5. Leave `downstream.work_package_id` null unless the disposition is `RESEARCH_SUFFICIENT`; never author the decision or the work package here.
6. Return the disposition; hand off to a separate decision authority. Grant no downstream authority.
