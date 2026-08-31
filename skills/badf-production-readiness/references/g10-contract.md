# The contract — two of G10's four evidence types

`badf/lifecycle.json` G10 (`UAT and Release Readiness`, owner `release_authority`) requires four
evidence types: `uat, release-packet, operational-readiness, go-no-go`. Ownership is split three ways,
deliberately:

```text
uat                     badf-uat                      business acceptance of the exact candidate
release-packet          badf-production-readiness     THIS SKILL
operational-readiness   badf-production-readiness     THIS SKILL
go-no-go                release_authority (human)     never any skill's — human-reserved
```

## Why the split is three ways and not one

A single capability owning all four would produce the acceptance evidence, produce the readiness
evidence, and then aggregate its own output into a recommendation — grading its own work at two
removes. The same principle that reserves G08 admission (VER-I18), security approval (SEC-I13) and
UAT's final acceptance (UAT-I14) applies here at the gate level: `badf-uat` produces `uat` and cannot
see this skill's dossier; this skill **resolves** `uat` as an input it did not produce (PRDY-I07); and
neither issues the `go-no-go` that consumes both.

## What `release-packet` must carry

```text
the exact candidate binding (references/candidate-binding.md)
the release delta against the currently released baseline (references/release-delta.md)
artifact identity: the artifact authorized is the artifact verified (references/release-artifact-identity.md)
the resolved upstream evidence set, each item bound to its producer, time and digest (PRDY-I04)
```

## What `operational-readiness` must carry

```text
observability: signal → query → threshold → alert route → owner → response action (PRDY-I15)
operations ownership: an accountable service / on-call owner (PRDY-I16)
support ownership: support and escalation for user-impacting releases (PRDY-I17)
recovery: actual recovery observation, not a backup artifact (PRDY-I11/I12)
rollback: executable, not documentary (PRDY-I13), coherent with migration state (PRDY-I14)
```

## What this skill never emits

`READY_FOR_AUTHORITY` is its ceiling. The authorization vocabulary above it belongs to
`release_authority` and is defined in exactly one place — `references/authority-boundary.md` — so that
there is a single canonical statement of what this skill cannot say. Naming those predicates here too
would put the vocabulary in two files that could drift, and the contract test enforces the single
location (PRDY-I19).
