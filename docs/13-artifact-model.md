# Artifact and Traceability Model

Status: **NORMATIVE**

## Core entities

| Entity | Purpose | Stable bindings |
| --- | --- | --- |
| Product intent/PRD | Defines value and accepted outcome | sponsor, baseline, acceptance |
| Requirement | Testable functional/non-functional need | PRD, design, tests, release |
| Work package | Grants bounded execution authority | owner, scope, gate, target |
| Decision record | Captures choice and consequences | inputs, authority, supersession |
| Change set | Source/config/data mutation | base, head, result tree |
| Evidence object | Proves a claim | producer, toolchain, artifact digest |
| Gate dossier | Requests stage transition | evidence index, approvals, disposition |
| Release | Promotes an immutable artifact | artifact, environment, change authority |
| Runtime observation | Proves deployed behavior | release, query/window, result |
| Memory/learning | Preserves reviewed knowledge | source evidence, scope, freshness |

## Traceability requirements

Maintain both directions:

`PRD outcome <-> requirement <-> design/decision <-> work package <-> change <-> test/evidence <-> release <-> runtime KPI <-> learning`

Orphan requirements, changes without authority, tests without claims, releases without candidate digests, and memories without sources block the relevant gate.

## Identity

Use stable opaque IDs with type prefixes, for example `WP-2026-0042`, `EVD-...`, `ADR-...`, `REL-...`. Names are labels, not identifiers. Timestamps use UTC ISO 8601. Digests use `sha256:<64 lowercase hex>`.

## Immutability

Approved baselines and evidence are append-only. Corrections create a new version that cites and supersedes the old. Schema evolution includes a version and migration/compatibility policy.

