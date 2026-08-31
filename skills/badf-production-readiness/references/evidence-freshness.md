# Freshness — stale mandatory evidence receives no readiness credit

PRDY-I05. Evidence is a measurement taken at a time, against a tree. Both can expire.

```text
Staleness axis        What expires
--------------------  ----------------------------------------------------------
candidate drift       evidence measured against a superseded candidate (PRDY-I23)
declared validity     evidence carrying its own expiry (a pen-test window, a scan epoch)
baseline drift        the released baseline moved, so the delta the evidence assumed is wrong
environment drift     the environment the evidence was observed in has since changed
policy drift          the threshold or policy the evidence was judged against has changed
```

## No credit, not reduced credit

Stale mandatory evidence yields `STALE` for its dimension — it does not yield a weakened `READY` or a
`READY_WITH_CONDITIONS`. Discounting stale evidence into a partial pass is how an expired measurement
keeps contributing to a positive posture; the vocabulary is deliberately bounded
(`references/readiness-dimensions.md`) so there is no gradient to slide down.

## Freshness is checked before contradiction

Order matters: a stale artifact that contradicts a fresh one is not a contradiction to be resolved
(`references/contradiction-resolution.md`) — it is a stale artifact with no standing. Checking
contradictions first would let expired evidence force an `INDETERMINATE` and stall a candidate that is
in fact evaluable.

## Optional evidence

Non-mandatory evidence that has gone stale is dropped from the dossier with its staleness recorded,
not silently omitted. The distinction between "not gathered" and "gathered and expired" is information
the authority needs.
