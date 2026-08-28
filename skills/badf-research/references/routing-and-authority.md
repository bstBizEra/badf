# Routing and authority

Status: frozen contract v0.1.

## The chain

```text
Issue → demand record (BADF-DEM) → research record (BADF-RSR) → decision record (BADF-DEC) → work package (WP-2026) → branch → PR → main
```

Research sits between discovery and decision. A research disposition creates nothing downstream by itself: `downstream.decision_id` and `downstream.work_package_id` are filled by the decision and the work package that cite the record, never by the record. Branch class: `research/BADF-RSR-NNNN-<slug>` (already in `GITHUB_CONTROL_PLANE.md`). Research may read, search, analyse, run tests and create disposable experiments on that branch; it may not turn itself into implementation.

## Invariants

- **RSR-I01** — Research output cannot grant implementation authority. `authority.implementation_authority` is fixed to `false` by the schema. **`RESEARCH_SUFFICIENT` ≠ `IMPLEMENTATION_AUTHORIZED`.**
- **RSR-I02** — A material research conclusion must be traceable to evidence: every finding references claims, every VERIFIED claim references at least one independent primary source.
- **RSR-I03** — `OBSERVED`, `REPORTED`, `INFERRED`, `HYPOTHESIS` and `DECIDED` remain semantically distinct; an inference cannot be serialised as an observation.
- **RSR-I04** — Contradictory evidence cannot be silently discarded.
- **RSR-I05** — Required independent challenge cannot be satisfied by the originating researcher or session.

## Challenge and the council

The framework already has ONE council mechanism (`compute_council_disposition` / `verify_council` in the gate). Research adds triggers to it — depth `D4`/`D5`, type `R06`, a `CONTRADICTORY_EVIDENCE` synthesis — and reuses its ballot rules: first-round ballots independent, sealed before synthesis, reviewer ≠ originating researcher, declared non-coverage, one identity counted once, a critical factual contradiction not erased by majority, council opinion advisory unless authority policy makes it mandatory. There is no research council beside it.

## What is not built here

No router beside the root `SKILL.md`; no validator beside `scripts/badf_gate.py` (the record is checked by `check_schema("research-record")`; transitions become a `research` subcommand in a later work package); no registry beside `badf/skill-registry.json`; no memory store. Confidence is derived (see `evidence-contract.md`).
