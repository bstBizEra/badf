# Architecture fitness obligations

DESIGN defines how important architectural properties will later be checked. At G04 a fitness obligation is a **specification**; at later lifecycle stages it can become executable verification evidence (G08/G09). This is the seam between "we intend this property" and "we proved it".

## NFR allocation drives fitness (ARCH-I06)

Every architecture-relevant NFR is consumed from the quantified upstream NFRs and traced:

```text
REQ/NFR → architecture element → architecture mechanism → fitness obligation → later verification evidence
```

Example:

```text
NFR-PERF-001 (p95 <= 300 ms)
   → API container
   → bounded synchronous dependency chain
   → PERF-FIT-001
   → G08/G09 performance evidence
```

Each architecture-relevant NFR resolves to exactly one of `ALLOCATED`, `DEFERRED_WITH_REASON`, `NOT_APPLICABLE_WITH_REASON` — never a silent omission. An allocation with no mechanism and no fitness obligation is incomplete.

## Fitness obligation types

```text
STRUCTURAL   DEPENDENCY   BOUNDARY   CONTRACT   SECURITY_BOUNDARY
DATA   OPERABILITY   PERFORMANCE   RESILIENCE   COST
```

## Fitness obligation shape

```text
FIT-ARCH-001
property:     Domain code must not depend on infrastructure adapters.
measurement:  dependency graph
scope:        src/domain/**
forbidden:    src/infrastructure/**
evaluation:   zero violating edges
```

A fitness obligation without a measurable property and a declared scope is not an obligation — it is a wish. The obligation is what ASSURE and later verification execute against a pinned observed revision.
