# Candidate change invalidates acceptance

UAT-I04, UAT-I17. Acceptance is bound to an exact candidate digest, not to "the product" in the
abstract. Once bound, three things can go stale:

```text
candidate_digest changes           the accepted build is no longer the build being shipped
acceptance_basis_digest changes    the PRD/AC/RTM the acceptance was measured against has moved
scenario_set changes materially    scenarios were added/removed/reworded after acceptance was issued
```

## Re-UAT trigger rule

A material candidate change requires an impact analysis before re-UAT is scoped:

1. Diff the new candidate against the accepted one (source-change evidence, same mechanism G07/G08
   already use for candidate identity).
2. Classify the change: cosmetic-only (no re-UAT required, but the acceptance record is amended
   extend-only to note the superseding digest), scenario-affecting (re-execute only the affected
   scenarios), or basis-affecting (the AC/RTM chain itself moved — full re-derivation per
   `references/scenario-derivation.md`).
3. A stale acceptance record is never silently treated as still valid. It is marked `SUPERSEDED` and a
   fresh Layer 2 acceptance is required against the new candidate digest before `go-no-go` can rely on
   it — mirroring the `EVIDENCE_DRIFT -> SUPERSEDED` state already established for BADF decision packets,
   never re-sent as if nothing changed.

## Extend-only record

Acceptance records are never overwritten in place. A superseded acceptance stays in the ledger with its
original digests intact; the new acceptance is a new record referencing what it supersedes.
