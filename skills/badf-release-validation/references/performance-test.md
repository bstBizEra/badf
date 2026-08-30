# performance-test — a measurement is not conformance without a pre-bound SLO (VAL-I10)

`performance-test` is a **class-aggregator** of SLO/budget-backed runtime observations,
normalized into the `performance-test` G09 evidence type the lifecycle already names. The Grafana
**k6** methodology takes precedence: functional correctness before load; SLO-backed thresholds;
load-generator self-monitoring; immutable, investigable runs.

## The critical rule — the threshold pre-exists the interpretation (VAL-I10)

```text
observed p95 = 420ms                     a MEASUREMENT
        + no bound SLO                    ✗ not a PASS — nothing to conform to
observed p95 = 420ms
        + SLO p95 ≤ 500ms (bound first)  ✓ CONFORMANT observation
```

A number is never a verdict. `performance-test` establishes conformance only when the SLO/budget
was bound **before** the result was interpreted (VAL-I06/VAL-I10). A threshold discovered by
reading the result is retro-fitting, and earns no validation credit.

## Route the workload FAMILY by the risk question (VAL-I02)

```text
smoke        does it basically function under minimal load?
average      does it meet SLO under expected load?
stress       where does degradation begin above expected load?
spike        does a sudden load surge fail — and recover?
soak         do leaks / slow degradation appear over sustained time?
breakpoint   at what capacity does it exhaust, and how does it fail?
```

The router picks the family the risk demands; running only `smoke` where the risk is capacity is
declared non-coverage (VAL-I15), not a silent PASS.

## The artifact (sketch — DESIGNED contract, not a schema)

```yaml
evidence_type: performance-test
candidate_digest: sha256:...             # the exact G08-verified candidate (VAL-I01)
environment_digest: sha256:...           # bound environment identity (VAL-I07)
slo_sources:                             # where each threshold pre-exists (VAL-I06)
  - docs/nfr/latency-budget.md#checkout
workload:
  profile: average                       # smoke | average | stress | spike | soak | breakpoint
  scenario: checkout-flow
  expected_rps: 120
thresholds:                              # bound BEFORE interpretation (VAL-I10)
  error_rate: "< 0.5%"
  p95: "<= 500ms"
  p99: "<= 900ms"
runtime:
  tool: k6
  tool_version: "<pinned>"
  script_digest: sha256:...
  run_id: RUN-...
  load_generator_profile: {vus: 200, ramp: 2m, hold: 10m}
observations:
  error_rate: "0.21%"
  p95: "420ms"
  p99: "760ms"
outcome: CONFORMANT                       # CONFORMANT | NON_CONFORMANT | BLOCKED | NOT_RUN
non_coverage:
  - surface: spike + soak profiles
    reason: out of routed scope for this change class
    impact: surge-recovery and sustained-load behavior not established
```

## Discipline

- The run is an approved runtime observation (VAL-I04); an agent's reported number is draft until
  observed and bound (VAL-I05). The load generator monitors itself so a starved generator is not
  misread as an application limit.
- A non-production run declares its deviations from production (VAL-I08): `staging CONFORMANT ≠
  production proven`.
- A failed run stays in evidence; rerun-until-green cannot erase it (VAL-I16).

## Boundary

`performance-test` is G09 evidence only. A spike-recovery run may **contribute** to a resilience
hypothesis, but a single k6 run is not automatically a `resilience-test` too (VAL-I13).
Performance conformance does not issue release readiness (VAL-I18) or claim production capacity
(VAL-I19).
