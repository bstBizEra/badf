# The release delta — readiness is measured against what changed

PRDY-I03. Readiness evaluates material change from the **currently released baseline**, not the
candidate in isolation. A candidate can be internally consistent and still be unsafe to release because
of what it changes relative to what is running.

```text
Surface        Previous      Candidate           Impact
-------------  ------------  ------------------  ----------------------
public API     v3            v4 field added      compatible
DB schema      17            18                  migration required
runtime        Python 3.12   3.13                compatibility impact
dependency     foo 4.x       5.x                 major dependency
auth           role set A    role set B          authorization impact
config         no flag       new required flag   operations impact
queue schema   v2            v3                  rollback concern
```

Adapted from the `final-release-review` methodology's delta matrix
(`references/external-methodology.md`) — the matrix shape is adopted; its local authority to declare a
release good is not.

## No diff ≠ ready

An empty delta is not evidence of readiness. It establishes only that this release changes little
relative to the last one — which says nothing about whether the last one was ready, whether the
mandatory evidence for *this* candidate exists, or whether the environment it deploys into has moved.
A dossier that reasons "nothing changed, therefore READY" has substituted a delta for the twelve
dimensions.

## The delta drives which dimensions are mandatory

A migration in the delta makes data/migration and rollback mandatory. An auth change makes security
mandatory. A dependency major makes security and performance mandatory. The delta is the input that
makes "mandatory" a derived property rather than a fixed checklist — and it is why an out-of-date delta
invalidates the readiness conclusion drawn from it (PRDY-I23).
