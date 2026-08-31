# Aggregation, not re-execution — the MAY / MUST NOT list

PRDY-I01. This is the invariant the whole capability rests on. A readiness aggregator that re-performs
the owning discipline has become a second validator with none of the original's independence,
oracles, or execution identity — and its result would then need validating by something else.

## MAY

```text
MAY  resolve an upstream evidence artifact by its canonical id and digest
MAY  evaluate whether that evidence is present, fresh, and bound to the exact candidate
MAY  detect that two mandatory artifacts contradict each other
MAY  compute the release delta from released baseline to candidate
MAY  derive which dimensions are mandatory for this delta
MAY  declare a dimension NOT_READY / BLOCKED / INDETERMINATE / STALE / NOT_APPLICABLE with a reason
MAY  declare non-coverage
MAY  recommend READY_FOR_AUTHORITY
```

## MUST NOT

```text
MUST NOT  re-run G09's quality, security, performance or resilience validation
MUST NOT  re-run G08's integration, contract or composed-tree verification
MUST NOT  execute UAT scenarios or re-derive business acceptance (that is badf-uat's, PRDY-I07)
MUST NOT  substitute its own judgment for a missing upstream oracle
MUST NOT  accept residual security or privacy risk on the owning authority's behalf (PRDY-I09)
MUST NOT  choose the favorable claim when mandatory evidence contradicts (PRDY-I06)
MUST NOT  issue go-no-go, PRODUCTION_AUTHORIZED, or any authorization predicate (PRDY-I19)
MUST NOT  treat its own recommendation as satisfying the authority decision it feeds
```

## Evidence provenance is part of resolution (PRDY-I04)

Every readiness claim binds its canonical evidence source, producer, observation time and digest.
A claim that says `security: READY` without naming which G09 security-validation artifact, produced by
whom, observed when, at what digest, is not a resolution — it is an assertion wearing a resolution's
shape, and nothing downstream can re-check it.
