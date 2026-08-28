---
name: adversarial-research
description: Independently challenge a research recommendation -- attempt to refute it, find omitted or non-independent evidence, counterexamples, unsupported assumptions and uninspected surface. It is separate from the originating research run and casts sealed ballots through the framework council. It does not gather first-round evidence, decide, or authorise; a refutation is evidence for reconciliation, not a veto.
---

# adversarial-research

A subskill of `badf-research` (`../../SKILL.md`). It is the **challenge** team: given a research record
at `work/research/<BADF-RSR-NNNN>/research-record.json`, it tries to falsify the recommendation and
records the outcome as sealed ballots in `challenge.council` against
`schemas/research-record.schema.json`. It has no authority; a verdict is evidence for
`research-reconciliation`, never a decision (RSR-I01).

**It is independent of the originating research (RSR-I05).** The researcher cannot ballot on their own
research; a required challenge needs at least two distinct reviewers; one identity cannot count twice;
each reviewer declares what they did not cover. First-round ballots are sealed before synthesis.

**A refutation cannot be erased by declaring sufficiency.** Each ballot is `CONFIRMED`, `REFUTED` or
`INCONCLUSIVE`. If the council carries a `REFUTED` ballot, the record cannot reconcile to
`RESEARCH_SUFFICIENT` — an independent refutation is not overridden by a majority or by the disposition
(control 25); it reconciles to `CONTRADICTORY_EVIDENCE`, `MORE_RESEARCH_REQUIRED`, or another
non-sufficient state.

## Do

1. Receive the record's recommendation, findings and evidence — **without** having gathered them.
2. Try to **refute**: what evidence would reverse the conclusion? Which sources are not actually independent? What counterexample exists? What assumption carries the recommendation? What relevant surface was not inspected? Is an alternate causal explanation plausible? Did the researchers optimise for confirmation?
3. Cast a sealed ballot — `CONFIRMED` / `REFUTED` / `INCONCLUSIVE` — and **declare your non-coverage** (what you did not check).
4. Preserve any contradiction you surface as a `contradictions[]` entry; never discard it (RSR-I04).
5. Hand the challenged record to `research-reconciliation`; a `REFUTED` outcome forecloses `RESEARCH_SUFFICIENT`. Grant no downstream authority.
