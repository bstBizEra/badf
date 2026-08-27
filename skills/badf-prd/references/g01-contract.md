# BADF G01 PRD Contract

Status: **skill reference**. Normative authority remains `AGENTS.md`, `docs/01-lifecycle-gates.md`, `badf/lifecycle.json`, and the applicable work package.

## Purpose

`badf-prd` turns product intent and evidence into a reviewable PRD baseline candidate. It proves structural and decision readiness; it does not authorize the lifecycle transition.

## Required G01 content

| PRD area | Required content | Gate concern |
| --- | --- | --- |
| Product identity | name, type, stage, owner, target market | ownership and target are explicit |
| Overview | concise product definition | common product boundary |
| Problem | statement, affected users, current limitations, business impact, why-now | problem is specific and material |
| Target users | segment, role, needs, pain points | value recipient is defined |
| Value proposition | statement and concrete benefits | intended value is testable |
| Vision | desired strategic end state | direction is coherent |
| Objectives | stable IDs, measurable statements, KPI references | outcomes are measurable |
| Scope | explicit in-scope and out-of-scope | scope cannot silently expand |
| Capabilities | capability, description, priority | initial solution boundary is visible |
| Differentiation | why this product/process is materially different | product rationale is explicit |
| Success metrics | stable KPI ID, baseline, target, measurement | success is measurable |
| Stakeholders | role and accountability | decision ownership is visible |
| Assumptions | explicit list, even when empty | silence is not an assumption register |
| Constraints | explicit list, even when empty | delivery boundaries are visible |
| Initial RAID | risks, assumptions, issues, dependencies | material uncertainty is recorded |
| Legal/regulatory/data | legal, regulatory, data classification, privacy | early obligations are surfaced |
| Acceptance criteria | stable IDs, statements, verification method | product acceptance is testable |
| Challenge | method, sources, findings, unresolved decisions | the PRD has been stress-tested |
| Baseline | version, source revision, author, status, approval record | candidate is versioned and reviewable |
| Evidence refs | stable references to supporting evidence | claims can be audited |

## Challenge contract

Challenge is not an approval vote. It must identify decision weaknesses before baseline review.

Each finding records a stable finding ID, `Critical`/`Major`/`Minor` severity, challenged claim, supporting evidence, and one disposition: `RESOLVED`, `ACCEPTED_AS_RISK`, or `BLOCKING`.

Any `BLOCKING` finding or any non-empty `unresolved_decisions` makes the candidate `REWORK_REQUIRED`.

## Baseline states

`DRAFT -> CANDIDATE -> APPROVAL_PENDING -> APPROVED | REJECTED`

The validator may confirm that an approval record is structurally credible. It does not create the approval. When approval state is `APPROVED`, an independent `product_owner` identity, timestamp, and evidence reference are mandatory, and the approver cannot be the candidate author.

## Validator dispositions

- `ELIGIBLE_FOR_G01_REVIEW` — structurally complete and no blocking challenge item is open. This is **not** `PRD_BASELINED`.
- `REWORK_REQUIRED` — structurally valid but blocking challenge findings or unresolved product decisions remain.
- `BADF PRD FAIL` — malformed, contradictory, placeholder-filled, or unverifiable structure; exit code `2`.

Only the repository's gate/authority path may decide G01 and advance lifecycle state.

## Evidence relationship

A normal G01 packet should ultimately provide the lifecycle-required evidence classes `prd`, `acceptance-criteria`, and `product-approval`. Supporting evidence should retain product research, stakeholder input, challenge findings, assumptions/constraints, initial RAID, and source revisions where material.
