# Contradiction — the favorable claim is never the answer

PRDY-I06. When two mandatory evidence artifacts make incompatible claims about the same candidate, the
dimension resolves to `NOT_READY` or `INDETERMINATE`. Synthesis cannot choose.

```text
Shape of contradiction                              Resolution
--------------------------------------------------  -------------------------------
two artifacts, same dimension, opposite verdicts     INDETERMINATE
an artifact contradicts the candidate binding        NOT_READY (binding is authoritative)
an artifact contradicts a declared non-coverage      NOT_READY (a gap was claimed covered)
a fresh artifact contradicts a stale one             not a contradiction — the stale one has no standing
producers disagree on the same observation           INDETERMINATE, both recorded
```

## NOT_READY vs INDETERMINATE

`NOT_READY` is used when the contradiction itself establishes a failure — evidence disagrees with the
exact candidate binding, or a declared gap turns out to have been claimed as covered. `INDETERMINATE`
is used when the contradiction means the dimension **cannot be evaluated** — two credible producers
disagree and nothing in this skill's authority resolves which is right. The difference matters to the
authority: one says "this is not ready", the other says "I cannot tell you whether this is ready", and
collapsing them into a single negative loses the remedy.

## Both sides are recorded

An `INDETERMINATE` dimension carries both contradicting artifacts, with their producers, times and
digests. A dossier that records only "contradiction detected" gives the authority nothing to act on and
gives the next re-evaluation nothing to compare against.

## Why this cannot be delegated to judgment

The tempting failure is an aggregator that "reconciles" a contradiction by reasoning about which
producer is more likely correct. That reasoning is re-performing the owning discipline's adjudication
(PRDY-I01) using none of its instruments. Escalating an unreconcilable contradiction is the correct
output, not a failure to produce one.
