# Security readiness — status resolved, residual risk never self-accepted

PRDY-I08, PRDY-I09.

## A green suite is not security validation (PRDY-I08)

Engineering test results and security validation answer different questions. A candidate whose G08
verification is entirely green has established that it does what it was specified to do; it has
established nothing about whether what it was specified to do is safe, whether its dependencies carry
known vulnerabilities, or whether its authorization model holds. Security readiness resolves the
applicable G05 design evidence and G09 `security-validation` evidence, and where the delta
(`references/release-delta.md`) makes security mandatory, their absence is `NOT_READY` — never a pass
inherited from the test suite.

## Readiness cannot accept its own residual risk (PRDY-I09)

Every real release carries residual security risk. Accepting it is a decision reserved to the
`security_authority` (human-reserved in `badf/authority-matrix.json`), exactly as SEC-I13 already
holds inside `badf-security-design`. This skill:

```text
MAY  resolve that a residual risk exists, is documented, and has an acceptance record
MAY  resolve who accepted it, when, and against which candidate
MAY  declare NOT_READY when a material residual risk has NO acceptance record
MUST NOT  accept a residual risk itself
MUST NOT  treat "the risk is documented" as equivalent to "the risk is accepted"
MUST NOT  infer acceptance from the absence of an objection
```

A documented-but-unaccepted residual risk is the single most likely place for a readiness aggregator to
quietly convert an open decision into a closed one, because the documentation looks like the artifact of
a decision having been made. It is the artifact of a decision having been *described*.

## Acceptance binds the candidate

A residual-risk acceptance is bound to the exact candidate it was issued against. A prior release's
acceptance does not carry forward to a candidate whose delta changed the surface that risk lives on —
the same staleness rule as everything else here (PRDY-I23).
