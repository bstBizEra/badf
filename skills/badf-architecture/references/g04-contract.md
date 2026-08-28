# G04 mapping

G04 (Architecture, Data and API; owner `architecture_authority`; minimum change class C1) already requires five evidence types. `badf-architecture` coordinates their coherence; it does not add a sixth gate and it does not approve G04 (ARCH-I11 — no `scripts/badf_architecture.py`; deterministic G04 evidence semantics belong in the canonical BADF gate, delivered by WP-ARCH-B).

## Ownership of the five G04 evidence types

| Evidence type | Owns |
| :--- | :--- |
| `architecture` | the canonical baseline: identity, system/context model, containers/topology, dependencies, boundaries, trust boundaries, material data flows, NFR allocations, fitness obligations, and references to the other four artifacts |
| `adr` | material architecture decisions (`adr-contract.md`) |
| `data-model` | data entities, ownership, lifecycle and persistence contract |
| `api-contract` | external/internal interface contracts and versioning |
| `operability-design` | failure, recovery, observability, capacity and operational behaviour |

The `architecture` artifact is the spine; the other four are detailed views that must be consistent with it (a data-model entity's owner must be a declared ownership boundary; an api-contract interface must be a declared crossing; an operability failure mode must name a declared dependency).

## How G04 feeds downstream

```text
G01 PRD → G02 requirements + NFRs → G03 UX/service design
   → badf-architecture DESIGN → G04 architecture evidence package → canonical BADF gate → G04 decision
```

Trust boundaries and data flows declared here become G05's threat model / privacy assessment inputs, rather than making G05 rediscover the architecture. Later, `badf-architecture` ASSURE runs against the implementation/composed tree and yields architecture assurance evidence for G08/G09 and change review.

## What this WP does and does not do

This contract freeze (WP-ARCH-A) documents the mapping. It changes nothing in `lifecycle.json`, adds no schema and no `check_*` rule, and leaves G04 exactly as declared. The deterministic G04 DESIGN evidence semantics are WP-ARCH-B; the ASSURE substrate is WP-ARCH-C.
