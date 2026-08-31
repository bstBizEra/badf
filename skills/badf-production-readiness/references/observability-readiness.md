# Observability — a signal nobody acts on is not observability

PRDY-I15. Required production signals bind the full chain. A dashboard is not readiness evidence; a
chain that ends in a human doing something is.

```text
signal → query → threshold → alert route → owner → response/rollback action
```

Every link is required, and each is where the chain actually breaks in practice:

```text
signal            the metric/log/trace actually emitted by THIS candidate (not by its predecessor)
query             the concrete query that reads it — resolvable, not described
threshold         the value that distinguishes healthy from not, declared BEFORE release (never fitted after)
alert route       where the alert goes — a channel, a pager, a rotation
owner             a named accountable party (references/operations-support-readiness.md, PRDY-I16)
response action   what that owner DOES — including whether the answer is "roll back"
```

## The two common vacuities

**A signal with no threshold** is a chart. It is visible to anyone who goes looking, and nothing makes
anyone look. **A threshold with no route and owner** is an alert that fires into an unattended channel;
the system detected the failure and told no one who could act.

Both pass a check that asks "is observability configured?" — which is why PRDY-I15 binds the whole
chain rather than its first link. The dimension is `NOT_READY` if any link is missing for a mandatory
signal, and the missing link is named.

## Thresholds are predeclared

A threshold set after observing the candidate's production behavior describes what the candidate does,
not what it must do. Predeclaration is what makes the threshold an oracle rather than a description —
the same discipline `badf-release-validation` holds at G09 (*measurement ≠ PASS*).

## Rollback is a legitimate response action

Naming rollback as the response for a signal is a strong readiness answer, not an admission of
weakness — but only when the rollback it names is `REHEARSED`
(`references/rollback-migration-readiness.md`). An observability chain terminating in a rollback that
has never been executed terminates in nothing.
