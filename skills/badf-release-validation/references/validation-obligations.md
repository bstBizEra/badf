# validation-obligations.md — the obligation-set object

The router (see [routing.md](routing.md)) emits a **validation obligation set**: one
obligation per validation class, each **derived** from declared risk — never hand-waved.
An obligation is the unit the conjunctive G09 dossier checks for presence and satisfaction
(see [g09-contract.md](g09-contract.md)). This file specifies the obligation object.

## The obligation object

Each of the four classes carries exactly one obligation with these fields:

- **disposition** — `REQUIRED` · `NOT_APPLICABLE` · `DEFERRED_WITH_REASON`.
- **rationale** — the tie to declared risk / routed surface that produced this disposition.
- **method** *(when `REQUIRED`)* — how the class will attempt to break the candidate.
- **oracle** *(when `REQUIRED`)* — the success/failure authority **outside the agent** that
  establishes what actually happened (**VAL-I04**).

```yaml
obligation:
  class:       performance-test
  disposition: REQUIRED
  rationale:   "NFR p99 latency budget on the changed checkout endpoint"
  method:      "average + stress workload against bound candidate in repl env"
  oracle:      "k6 threshold assertion vs pre-bound p99 budget (VAL-I06)"
```

## Disposition semantics

| Disposition | Meaning | Obligation on the author |
| :--- | :--- | :--- |
| `REQUIRED` | class must establish evidence for this candidate | supply method + oracle; produce a bound runtime result |
| `NOT_APPLICABLE` | no routed surface implicates this class | justify against the routed surfaces, not by convenience |
| `DEFERRED_WITH_REASON` | risk is real but validation is deferred | record the reason; it surfaces as declared non-coverage (**VAL-I15**) |

`NOT_APPLICABLE` is **justified**, not assumed: it must point at the absence of a routed
surface (e.g. "no UI changed → no cross-browser obligation"). A bare `NOT_APPLICABLE` with no
rationale is an invalid obligation. A `DEFERRED_WITH_REASON` is **not** a pass — the deferred
risk is carried forward as non-coverage and never silently closed.

## Derived, not hand-waved

An obligation's disposition and method come from the router's derivation over risk, surface,
threat model and NFRs (**VAL-I02**) — not from an agent's preference. Consequences:

- An agent **cannot** weaken a `REQUIRED` obligation to `NOT_APPLICABLE` to make a candidate
  pass; the derivation, re-runnable from the same inputs, sets the disposition.
- A `REQUIRED` obligation without a **method + oracle** is incomplete — an intention, not an
  obligation — and cannot contribute a satisfied result.
- The obligation's `method`/`oracle` produce **draft** scenarios and interpretations until the
  runtime validates and binds them (**VAL-I05**); the obligation names *what* will be
  established and *by which oracle*, and the runtime establishes *what happened*.

## Obligation → satisfaction

An obligation is `satisfied` only when, for the exact bound candidate
(see [candidate-binding.md](candidate-binding.md)):

```
satisfied(obligation) =
    disposition == REQUIRED
    AND approved runtime observed the class's method            (VAL-I04)
    AND result judged against a pre-bound threshold             (VAL-I06)
    AND result bound to environment provenance                  (VAL-I07)
    AND no unresolved blocking finding in this class            (VAL-I14)
    AND this class's non-coverage is declared                   (VAL-I15)
```

`NOT_APPLICABLE` obligations contribute nothing to satisfy and nothing to block.
`DEFERRED_WITH_REASON` obligations contribute **declared non-coverage** — they never count as
satisfied, so a deferral cannot masquerade as a green class. Each class satisfies **only its
own** obligation; one class's satisfied result never fills another's slot
(**VAL-I13**, see [class-independence.md](class-independence.md)).
