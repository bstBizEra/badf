# routing.md — the validation obligation router

Routing is **risk-derived, not "run all QA"** (**VAL-I02**). The router reads the candidate's
context and derives which of the four independent classes are `REQUIRED` for *this* change —
it does not run a static checklist, and an agent cannot weaken a required class ad hoc. The
router's output is a **validation obligation set** (see
[validation-obligations.md](validation-obligations.md)); each class it routes then validates
independently (see [class-independence.md](class-independence.md)) against the exact bound
candidate (see [candidate-binding.md](candidate-binding.md)).

## Router inputs

The obligation set is derived — never hand-picked — from:

- **G02–G08 evidence** — prior-gate findings, risks and unresolved surfaces flowing forward.
- **Work Package / change class** — the declared nature and blast radius of the change.
- **changed surfaces** — the concrete APIs, schemas, UI, flows and infra actually touched.
- **threat model** — declared adversaries, trust boundaries and abuse cases.
- **NFRs** — SLOs, budgets, availability and recovery objectives in force.
- **release candidate** — the exact G08-verified candidate identity (**VAL-I01**).

```
G02–G08 evidence ─┐
Work Package/class ┤
changed surfaces  ─┼─► ROUTER ─► validation obligation set
threat model      ─┤            {quality, security, performance, resilience}
NFRs              ─┤            each ∈ REQUIRED | NOT_APPLICABLE | DEFERRED_WITH_REASON
release candidate ─┘
```

## Surface → class routing (illustrative, not exhaustive)

A changed surface implies risk domains; each risk domain routes to the class that owns it.
One surface commonly routes multiple classes — the router adds obligations, it never trades
one class for another (**VAL-I13**).

| Changed surface | Quality | Security | Performance | Resilience |
| :--- | :---: | :---: | :---: | :---: |
| API change | contract/E2E behavior | authz/input abuse | latency + throughput budget | dependency-timeout recovery |
| Database migration | data-integrity/rollback | injection / data exposure | migration duration under load | mid-migration failure recovery |
| Browser UI | cross-browser + a11y | XSS / client trust | render/interaction budget | offline/degraded-network behavior |
| Payment flow | flow correctness (oracle-backed) | fraud/authz, secret handling | peak-load latency | provider-outage recovery + integrity |
| Agentic system | eval/behavior correctness | prompt-injection/tool abuse | token/step budget | tool-failure + loop-abort recovery |
| Infra change | config/wiring correctness | exposure/least-privilege | capacity/scaling budget | node/zone-loss failover |

The cells are **method examples**, not the whole obligation — each becomes a full obligation
with disposition, rationale, method and oracle in
[validation-obligations.md](validation-obligations.md).

## A sample obligation set

For a payment-API change with no UI touched, no infra change, and a soak concern deferred to
a later window:

```yaml
obligation_set:
  candidate: "a1b2c3d4 @ vpol-2026.08"     # bound identity, see candidate-binding.md
  classes:
    quality-validation:
      disposition: REQUIRED
      rationale:  "payment flow correctness is customer-facing"
    security-validation:
      disposition: REQUIRED
      rationale:  "threat model flags authz + secret handling on the payment path"
    performance-test:
      disposition: REQUIRED
      rationale:  "NFR: p99 checkout latency budget on the changed endpoint"
    resilience-test:
      disposition: DEFERRED_WITH_REASON
      reason:     "soak/provider-outage window scheduled post-freeze; tracked as non-coverage"
```

## What routing may and may not do

- **May** mark a class `NOT_APPLICABLE` — but only justified against the routed surfaces
  (e.g. no UI changed → no cross-browser obligation).
- **May** mark a class `DEFERRED_WITH_REASON` — the reason is recorded and surfaces as
  declared non-coverage (**VAL-I15**), never as silent absence.
- **Must not** silently drop or downgrade a `REQUIRED` class; a required class absent from the
  dossier fails `required_classes_present` in the conjunctive verdict
  (see [g09-contract.md](g09-contract.md)).
- **Must not** let an agent reclassify `REQUIRED → NOT_APPLICABLE` to make a candidate pass;
  the routing derivation, not agent preference, sets the disposition (**VAL-I02**).
