# Execution contract — ISOLATE · BASELINE · SLICE · IMPLEMENT · LOCAL VERIFY

## ISOLATE

Use the isolation strategy declared by planning. Usually:

```text
badf-build
    ↓ requests workspace
badf-git
    ↓ verifies/creates governed isolation
worktree / branch
```

`badf-build` does not invent branch mechanics; repository topology is `badf-git`'s contract.

## BASELINE (BLD-I02)

Run pre-change evidence before the first mutation:

```text
repository state · baseline tests · build/typecheck baseline · known failures
environment identity · base SHA · composition baseline
```

The distinction this buys is critical and must be recorded, never inferred:

```text
PRE-EXISTING FAILURE
≠
BUILD-INTRODUCED FAILURE
```

## SLICE

One coherent acceptance slice at a time (the tracer-bullet discipline bound to WP acceptance
traceability):

```text
AC → test seam → failing observation → minimal mutation → passing observation → next acceptance slice
```

## IMPLEMENT and LOCAL VERIFY

The minimal mutation that makes the observed failure pass, inside the authorized surface. Typecheck and
focused tests run continuously; the full verification runs at finish. Verification is **fresh** — a
prior run, an inferred result or an agent's report of a result is not evidence (BLD-I09).

## Refactoring doctrine (METHOD OPTION, not invariant)

```text
RED → GREEN → optional bounded REFACTOR → GREEN AGAIN
```

with the condition that a refactor may not expand scope or alter acceptance semantics. Whether the
refactor phase sits at step three or in review is a method option; the governance-relevant part is that
behavior remains proven and scope remains bounded.

## Design drift is upstream work (BLD-I14)

Build often discovers that the planned design is wrong. The build agent must not silently redesign:

```text
need a new service boundary          → ARCHITECTURE_CHANGE_REQUIRED
need broader permission              → AUTHORIZATION_DESIGN_CHANGE_REQUIRED
need a weaker security control       → SECURITY_DESIGN_CHANGE_REQUIRED
requirement impossible as specified  → REQUIREMENT_CHANGE_REQUIRED
acceptance criterion no longer apt   → PRODUCT_REBASE_REQUIRED
```

Then return upstream. Engineering convenience is not design authority.

## Authority split, restated

```text
Agent judgment MAY resolve implementation detail inside granted scope.

Agent judgment MUST NOT resolve an authority conflict, scope expansion, risk-class change,
security acceptance, architectural deviation, acceptance weakening, or destructive escalation.
```
