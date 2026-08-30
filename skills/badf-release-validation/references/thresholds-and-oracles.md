# Thresholds and oracles — the criterion, and the mechanism that applies it (VAL-I06)

G09 acceptance turns on two distinct things that are easy to conflate. Keeping them separate is what stops
an agent from moving the goalposts after seeing the result.

```text
THRESHOLD   the bound acceptance criterion        — WHAT counts as acceptable
            (an SLO, an NFR target, an error budget, a coverage floor, a severity ceiling)

ORACLE      the out-of-agent decision function     — the MECHANISM that turns one
            that maps an observation → PASS/FAIL      observation into a class verdict
```

An agent may *attempt* a journey, propose a scenario, or run a scan. The **oracle decides** whether the
observation passes. The threshold is the line; the oracle is the ruler held against it.

## Thresholds are bound before results are interpreted (VAL-I06)

Security, performance, resilience and quality acceptance thresholds are **fixed before** the observation is
interpreted. A threshold chosen — or relaxed — after seeing the number is not a threshold; it is a
rationalization. Each threshold names its source, so it is auditable rather than asserted:

```yaml
threshold:
  class: performance-test
  metric: p95_checkout_latency_ms
  bound: 300
  operator: "<="
  source: NFR-PERF-014            # SLO / NFR / error-budget of record — not invented at eval time
  bound_at: <timestamp before observation>
oracle:
  kind: deterministic_comparator  # out-of-agent; same input → same verdict
  evaluates: p95_checkout_latency_ms <= 300
  produces: PASS | FAIL
```

## Measurement is not conformance (VAL-I10)

> **Observed 420ms without a bound SLO = measurement, not PASS.**

A metric with no threshold behind it establishes *what was measured*, nothing about *whether it is
acceptable*. Reporting a latency, an error rate or a throughput number is not a `performance-test` PASS
(VAL-I10) — the same holds for a security scan count or a resilience recovery time. No bound threshold →
no PASS; the observation is carried as measurement, and the missing criterion is declared non-coverage
(VAL-I15).

## Oracle properties (all three, or it is not an oracle)

- **Deterministic** — same observation in, same verdict out. No model call sits in the decision path.
- **Pre-declared** — defined with the threshold, before the run, as part of the class contract.
- **Out-of-agent** — the agent may attempt and may package, but the PASS/FAIL is not the agent's to
  assert. An agent-asserted verdict is DRAFT (VAL-I05) until the oracle produces the canonical one.

## What an oracle is not

An oracle is not release authority. It renders one class verdict from one observation against one bound
threshold. It does not compose the dossier, does not weigh a security FAIL against a performance PASS (see
`findings-and-disposition.md`), and does not grant progression — `quality_authority` decides G09, and G09
is not G10 (VAL-I18). A passing oracle is a necessary input to G09, never the whole of it.
