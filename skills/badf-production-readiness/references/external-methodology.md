# External methodology — ADAPT / EXTEND / REJECT

Two external sources informed this capability's design. **Both were characterized from the operator's
directive, not independently fetched or executed** — that limitation is declared here rather than
implied, because a reference that presents second-hand characterization as first-hand review is the
same unverified-claim class BADF has been cataloguing.

## `final-release-review` (OpenAI)

```text
ADAPT   the previous-release-vs-candidate delta matrix — surface / previous / candidate / impact.
        Adopted in references/release-delta.md as the shape that makes "what changed" checkable.
ADAPT   the discipline of reviewing a release against its baseline rather than in isolation (PRDY-I03).
REJECT  its local `GREEN LIGHT TO SHIP` authority. A review capability declaring a release good is
        exactly the evidence-producer-as-decider collapse PRDY-I19 exists to prevent. BADF's
        equivalent conclusion is READY_FOR_AUTHORITY, and it is a recommendation.
```

## The reviewed production-readiness skill

```text
ADAPT   the readiness-dimension decomposition — that production readiness is many independent
        dimensions rather than one aggregate judgment.
EXTEND  each dimension is bound to its OWNING GATE's evidence source (readiness-dimensions.md) rather
        than re-assessed locally. This is the PRDY-I01 extension: resolve, never re-perform.
EXTEND  the bounded readiness vocabulary with STALE and INDETERMINATE, which the source lacks and
        which PRDY-I05 and PRDY-I06 require.
REJECT  its own approval decision. Same reason as above: a readiness capability that approves is not
        a readiness capability.
```

## What is not adopted at any rung

No vendored executable, no external runtime, no third-party service call. This skill has
`allowed_tools: []` and resolves artifacts already inside BADF's own ledger.
