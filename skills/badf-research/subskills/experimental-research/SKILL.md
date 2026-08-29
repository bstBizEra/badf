---
name: experimental-research
description: Answer an empirical question by running a controlled experiment, not by citing sources -- state a falsifiable hypothesis, design a method that could refute it, run it under the BADF experiment mechanism, and record method and result. For research type R08 (EMPIRICAL_EXPERIMENT) at depth D5. It measures under control; it does not decide, authorise, or declare a result true because it was measured once.
---

# experimental-research

A subskill of `badf-research` (`../../SKILL.md`). It answers an `R08` (`EMPIRICAL_EXPERIMENT`)
question by adding `experiments[]` to the research record at
`work/research/<BADF-RSR-NNNN>/research-record.json` against `schemas/research-record.schema.json`.
It has no authority; a measured result is evidence for a decision, never a decision (RSR-I01).

**Its question is empirical: "what happens when we measure it under control?"** — not "what do the
sources say?" (that is `fact-checking`/`deep-research`). An experiment tests a **falsifiable
hypothesis**; a method that could not fail is not an experiment.

```text
HYPOTHESIS   states what would be observed, and what would refute it
METHOD       a controlled procedure another agent could re-run
RESULT       what was observed -- including a refuting result, preserved
```

**Bound and real (control 28).** An `R08` record carries **at least one experiment**, and every
experiment's `hypothesis_ref` resolves to a hypothesis the record actually holds. A run that measured
nothing, or an experiment on a hypothesis the record never stated, is not an experiment. The BADF
experiment mechanism *is* the method: a claim is measured under the composed-tree gate and hardened by
mutation, so "reproducible" is demonstrated, not asserted. `R08`/`D5` requires independent challenge
(computed, not asserted); a single measurement is not proof.

## Do

1. **Frame** — restate the empirical question and the decision it serves (`decision_context`).
2. **Hypothesise** — add a falsifiable `H-nnn` to `hypotheses[]`: what would be observed, and what would refute it.
3. **Design** — a controlled method another agent could re-run; name the mechanism (e.g. composed-tree gate + mutation), the variable, and the tolerance.
4. **Run and record** — add an `E-nnn` to `experiments[]` with `hypothesis_ref`, `method`, and `result`; a refuting result is preserved, never discarded.
5. **Adjudicate the hypothesis** — set its status `RETAINED` / `ELIMINATED` / `OPEN` from the result, not from preference; a single run rarely eliminates.
6. **Bind a claim** — an `OBSERVED` claim rests on the experiment as its primary evidence; confidence stays derived (reproducibility comes from re-running the method).
7. **Challenge and synthesise** — `D5` requires independent challenge; hand the adjudicated evidence to `evidence-synthesis` / `research-reconciliation`. Grant no downstream authority (RSR-I01).
