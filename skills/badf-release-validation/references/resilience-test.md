# resilience-test — hypothesis-driven fault + observed recovery, not survival (VAL-I11/I12)

`resilience-test` is a **class-aggregator** of hypothesis-driven fault-injection and recovery
observations, normalized into the `resilience-test` G09 evidence type the lifecycle already names.
It adapts `qa-skills`' chaos-engineering structure: **controlled experimentation, never random
destruction.**

## The freeze — capability is not authority (VAL-I11)

```text
the runtime CAN inject a fault           ≠   it is authorized to
resilience is hypothesis-driven          →   steady state + expected behavior + bounded blast
                                             radius + executable abort conditions come first
survival during injection                ≠   PASS
observed recovery + integrity checks     =   PASS (VAL-I12)
```

A fault injected without a prior steady-state baseline and a falsifiable hypothesis is vandalism,
not evidence. "It didn't fall over while we broke it" is not recovery — recovery is **observed**
return to steady state with data integrity verified (VAL-I12).

## The experiment structure (adapted from chaos-engineering)

```text
1 steady state          measurable normal behavior, bound before the fault
2 hypothesis            "under fault X, the system holds SLO / recovers within RTO"
3 controlled fault      the smallest fault that tests the hypothesis
4 bounded blast radius  named services + SYNTHETIC users only — never real users
5 abort conditions      executable stop rules; the experiment self-halts on breach
6 observation           deterministic runtime facts, not narration (VAL-I04)
7 recovery analysis     observed return to steady state within expected RTO
8 data-integrity        no silent loss / corruption — checked, not assumed (VAL-I12)
```

## The artifact (sketch — DESIGNED contract, not a schema)

```yaml
evidence_type: resilience-test
hypothesis: "on primary-DB failover, checkout recovers within 30s with zero data loss"
candidate_digest: sha256:...             # the exact G08-verified candidate (VAL-I01)
environment: staging-representative      # bound + deviations declared (VAL-I07/I08)
steady_state:
  metric: checkout_success_rate
  normal: ">= 99.5%"
fault:
  kind: dependency-failover
  target: primary-db
  duration: 60s
blast_radius:
  services: [checkout, inventory]
  users: synthetic_only                  # never real users
abort_conditions:
  - "error_rate > 20% for 30s → halt"
expected_recovery:
  rto_seconds: 30
  data_loss: none
observed:
  recovery_seconds: 22
  data_loss: none
outcome: CONFORMANT                       # CONFORMANT | NON_CONFORMANT | BLOCKED | NOT_RUN
```

## Discipline

- The experiment is an approved runtime observation (VAL-I04); the agent authors the hypothesis
  and scenario as draft (VAL-I05), a deterministic runtime establishes what happened. Thresholds
  (RTO, integrity, steady state) pre-exist the run (VAL-I06).
- Every run names the fault modes it did **not** exercise (VAL-I15); a failed recovery stays in
  evidence and rerun-until-green cannot erase it (VAL-I16).

## Boundary — performance-test ≠ resilience-test (VAL-I13)

A performance **spike** run tests fail-and-recover under load and may **contribute** evidence to a
resilience hypothesis — but a single k6 spike run does not automatically earn a second,
independent `resilience-test` class. Each class keeps its own hypothesis, oracle and evidence
(VAL-I03). `resilience-test` is G09 evidence only: it does not issue release readiness (VAL-I18)
or claim production resilience (VAL-I19).
