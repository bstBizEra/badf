# DESIGN mode

Create intended architecture. DESIGN produces the canonical baseline and the G04 evidence package; it does not approve G04.

## Workflow

```text
FRAME → INGEST → BOUND → MODEL → FLOW → DECIDE → ALLOCATE → OPERATE → CHALLENGE → PACKAGE
```

- **FRAME / INGEST** — resolve system scope, the upstream PRD, requirements/RTM, NFRs, UX/service-design inputs, architecture constraints, legacy/external systems, data classifications, deployment constraints, non-goals, and unresolved research questions. Material uncertainty routes to `badf-research`; it is not silently guessed. What is unknown becomes an explicit assumption, open decision, research question or blocker according to authority and uncertainty — never a fabricated fact.
- **BOUND** — define the system boundary and the container/service, module/bounded-context, ownership, data-ownership, trust and control-plane boundaries. Each boundary states what is inside, what is outside, and which crossings are legitimate.
- **MODEL** — the C4 baseline: Level 1 (System Context) and Level 2 (Container) are required by default; Level 3 (Component) only for complex/high-risk containers where the decomposition adds assurance value; Level 4 (Code) generated on demand only. Views project the baseline (`c4-contract.md`); they never author it.
- **FLOW** — trust boundaries and material data flows: for each crossing, source, destination, data classification, purpose, protocol, identity context, trust transition and storage/transit behaviour. This is what G05 analyses; G04 gives G05 something concrete rather than making it rediscover architecture.
- **DECIDE** — record material choices as ADRs (`adr-contract.md`); distinguish a genuine `DECISION` from a mandatory `CONSTRAINT`.
- **ALLOCATE** — consume the quantified upstream NFRs; allocate each to an element, a mechanism and a later fitness obligation (`architecture-fitness.md`). Every architecture-relevant NFR is `ALLOCATED`, `DEFERRED_WITH_REASON`, or `NOT_APPLICABLE_WITH_REASON` — never silently omitted.
- **OPERATE** — operability beyond the happy path: failure modes, timeout/retry/idempotency, degradation, recovery, backup/restore implications, observability seams, health/readiness, capacity/scaling, operational ownership, dependency-outage behaviour. Feeds G04 `operability-design`.
- **CHALLENGE / PACKAGE** — seek the ways the design fails; then package the five G04 evidence types coherently (`g04-contract.md`).

## Relationship contract

Every material relationship carries more than `A → B`. Minimum: `from`, `to`, `intent`, `direction`, `interaction_type`, `protocol`, `data_or_command`, `trust_boundary_crossing`, `criticality`. Where applicable also `authentication`, `authorization`, `encryption`, `retry_semantics`, `timeout`, `idempotency`, `consistency`, `failure_behavior`. This is what lets ASSURE compare declared architecture against implementation.
