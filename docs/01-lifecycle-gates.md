# PRD-to-Production and Post-Deployment Gates

Status: **NORMATIVE**  
Machine-readable source: `badf/lifecycle.json`

## Gate model

Each gate is a decision, not a folder-completeness check. Entry criteria authorize work inside a stage. Exit criteria authorize progression. Gate evidence must bind to the current source, target, toolchain, and policy epoch. A later source change invalidates affected approvals.

| Gate | Stage | Decision outcome |
| --- | --- | --- |
| G00 | Intake, authority and project definition | A project may enter from nothing: the instance exists (`AGENTS.md`, `badf/project.yaml`, `badf/state.json`, receipt), the product is defined, and work is legitimate, owned, classified, and bounded |
| G01 | PRD baseline | Problem, users, value, outcomes, constraints, and acceptance are approved |
| G02 | Requirement decomposition | Stories, NFRs, traceability, dependencies, and DoR are complete |
| G03 | UX and service design | Journeys, accessibility, service operations, and user validation are ready |
| G04 | Architecture, data, API | Architecture, contracts, data lifecycle, ADRs, and operability are coherent |
| G05 | Security, privacy, AI safety | Threats, abuse, privacy, supply chain, and AI risks are controlled |
| G06 | Implementation planning | Work packages, environments, rollout, rollback, and resources are executable |
| G07 | Build complete | Code, migrations, configuration, tests, and documentation are implemented |
| G08 | Engineering verification | Review and unit/integration/contract/E2E checks pass on composed code |
| G09 | Independent validation | Quality, security, performance, resilience, and data tests meet thresholds |
| G10 | UAT and release readiness | Acceptance, operations, support, compliance, and go/no-go packet are ready |
| G11 | Deployment and change control | Approved immutable artifact is deployed through controlled progression |
| G12 | Production verification | Smoke, telemetry, business controls, security, and rollback signals pass |
| G13 | Operational acceptance | SLOs, on-call, capacity, incident response, cost, and stabilization are accepted |
| G14 | Assurance closure and learning | Outcomes reconciled, evidence sealed, debt owned, and learning promoted |

## Universal exit checks

Every gate must demonstrate:

1. current authority and ownership;
2. required artifacts meeting schema;
3. forward and backward requirement traceability;
4. risk and dependency reconciliation;
5. required independent review;
6. current evidence without source, target, policy, or toolchain drift;
7. explicit disposition and conditions;
8. no unresolved blocker or expired exception.

## Stage-specific emphasis

### G00–G02: define the right work

Do not begin implementation while business outcome, affected users, scope, data classification, acceptance criteria, NFRs, or dependencies remain materially ambiguous. A minimum Definition of Ready is required at G02 and must not be deferred to implementation planning.

### G03–G05: prove coherent and safe design

Validate unhappy paths, accessibility, support journeys, integration failure modes, data ownership, tenancy/isolation, authentication/authorization, auditability, privacy, threat model, dependency posture, and AI evaluation/guardrail requirements where applicable.

### G06–G09: implement and independently challenge

Plan small work packages with explicit composition order. Build with tests and telemetry. Verify on the expected merged/composed tree. Independent validation must use production-representative conditions and must identify untested surfaces.

### G10–G12: authorize, deploy, and verify

Release readiness requires an immutable artifact digest, change ticket, rollout/rollback criteria, runbooks, observability, communications, support readiness, and approvals. Deployment success is not inferred from pipeline success; G12 requires runtime verification.

### G13–G14: stabilize and learn

Measure SLOs and business KPIs through the defined stabilization window. Reconcile actual outcomes against the PRD, close or assign residual debt, seal evidence, update knowledge, and propose skill/policy improvements through separate governed changes.

## Dispositions

- `PASS`: all mandatory controls satisfied.
- `PASS_WITH_CONDITIONS`: explicitly allowed only when lifecycle definition permits; conditions have owners and deadlines.
- `FAIL`: evidence proves criteria are not met.
- `BLOCKED`: decision cannot be made due to missing authority, evidence, dependency, or environment.
- `HUMAN_REQUIRED`: the decision exceeds delegated authority.

## G01 evidence contract (`BADF-WP-0030`, Issue #51)

G01 requires three evidence types. Each has semantics the gate checks by opening the artifact —
inside `validate_evidence`, never in a second validator:

| Evidence | Artifact | Rules the gate enforces |
| :--- | :--- | :--- |
| `prd` | `prd.artifact.json` per `schemas/prd.schema.json` | no item in both `in_scope` and `out_of_scope`; every objective's `metric_refs` names a declared success metric; no unresolved placeholder anywhere |
| `acceptance-criteria` | per `schemas/acceptance-criteria.schema.json` | non-empty; unique `AC-` ids; `prd_id` names the PRD; no placeholders |
| `product-approval` | per `schemas/product-approval.schema.json` | produced by a **human** `product_owner` whose principal is **not** the PRD's author; `prd_digest` equals the exact bytes of the `prd` artifact in the same dossier — a PRD edited after approval invalidates the approval |

The dossier's approvals stay the matrix's (C1: `engineering_owner`, `independent_reviewer`); the product
owner's act is the `product-approval` evidence. `skills/badf-prd/` (salvaged from PR #44) is the
authoring reference; it has no gate authority and there is no `badf_prd.py`.
