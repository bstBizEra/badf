# Environment fidelity — where the observation ran is part of the evidence (VAL-I07)

A G09 observation is only as trustworthy as the environment it ran in. So the environment is **first-class
evidence**, not a footnote. Every runtime result binds its environment identity, configuration, fixtures,
toolchain and observation time (VAL-I07) — and a non-production environment **declares how it differs from
production** (VAL-I08). Fidelity is not a vibe; it is a bound, digested statement.

## Every runtime result binds its environment

```yaml
environment:
  id: staging-eu-1
  digest: sha256:9c1f…              # resolved config + infra manifest, not a label
  toolchain: k6-0.52 / postgres-16 / node-20.11
  observation_time: 2026-08-31T04:12:07Z
  representative_of_production:
    topology: PARTIAL               # single app node vs prod 6-node autoscale group
    configuration: MATCH            # same feature flags, same resource limits
    data_volume: DEVIATES           # 40k rows vs prod ~9M
    third_party_integrations: SANDBOX   # payment + email in sandbox, not live providers
  deviations:
    - surface: data_volume
      reason: production dataset not provisioned in staging
      impact: index/scan behavior at scale not established
      declared_noncoverage: true    # carried into the dossier, VAL-I15
    - surface: third_party_integrations
      reason: live payment provider not reachable from staging
      impact: real settlement + provider rate-limit behavior not established
      declared_noncoverage: true
```

The `representative_of_production` block is the **fidelity statement**: for each axis — topology,
configuration, data volume, third-party integrations — it says `MATCH`, `PARTIAL`, `DEVIATES` or
`SANDBOX`, and every non-`MATCH` axis appears in `deviations`.

## A deviation is declared, never assumed away (VAL-I08)

> **`staging PASS` ≠ `production proven`.**

That gap does not disappear because the run was green. It becomes **declared non-coverage** — named,
owned, and carried into the dossier (VAL-I15) — not forgotten context. A non-production environment that
lists no deviations is making the strong claim that it is production-faithful on every axis; that claim is
admissible only when it is actually true and stated, never by silence.

## Fidelity binds to the exact candidate

The environment identity is bound alongside the candidate identity (VAL-I01): the observation is "this
exact candidate, in this exact environment, at this time". Change the candidate → the observation is stale.
Change the environment → the fidelity statement and its deviations must be re-declared. An environment
reused across candidates without re-binding is an unprovenance'd result, not a stronger one.

## What environment fidelity is not

Fidelity declaration is not a waiver. Declaring that staging deviates from production on data volume does
**not** convert an unmet REQUIRED obligation into a pass — it records the boundary of what was established
(see `noncoverage.md`). Nor does a faithful environment grant authority: a production-representative PASS is
G09 evidence, and G09 is not G10 (VAL-I18) and not G12 production verification (VAL-I19). Where the run
happened is part of the proof; it is never the decision.
