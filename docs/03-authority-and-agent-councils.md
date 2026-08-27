# Authority, Agents, and Councils

Status: **NORMATIVE**  
Machine-readable source: `badf/authority-matrix.json`

## Authority principles

Tool access demonstrates capability, not authorization. Authority must bind actor/role, action, target, environment, time window, work package, and conditions. Delegation cannot exceed the delegator's scope.

## Agent roles

- **Coordinator:** frames work, routes tasks, maintains state, integrates outputs, and owns evidence completeness.
- **Builder:** implements within a work package and authors verification evidence.
- **Reviewer:** performs an independent bounded review and declares non-coverage.
- **Verifier:** executes deterministic tests or reproductions independently of the author.
- **Release observer:** monitors deployment/runtime gates without altering acceptance criteria.
- **Librarian:** curates validated knowledge and provenance; cannot turn inference into fact.

## Council protocol

1. Chair defines the exact question, artifact digest, decision options, mandatory lenses, and quorum.
2. Members receive the same sealed inputs and work independently.
3. Each ballot records reviewer identity/role, artifact digest, verdict, findings, evidence, confidence, assumptions, and non-coverage.
4. Ballots are persisted before synthesis.
5. Chair checks independence, quorum, conflicts of interest, and digest equality.
6. Synthesis preserves minority risks and unresolved contradictions.
7. The authorized decision-maker accepts, rejects, conditions, or escalates the recommendation.

Council verdicts: `APPROVE`, `APPROVE_WITH_CONDITIONS`, `REJECT`, `ABSTAIN`, `INSUFFICIENT_EVIDENCE`. Majority does not override a mandatory blocking finding or reserved human authority.

## Required independent lenses

For C2/C3 changes, select applicable lenses: product/value, architecture, security/privacy, data/integration, quality/test, operations/resilience, UX/accessibility, compliance, and composition/integration. The same person or model run cannot count twice toward quorum.

## Human-reserved decisions

Unless a ratified policy says otherwise: constitutional/governance changes, production credential handling, destructive data operations, legal/privacy acceptance, high-impact release, exception approval, budget commitment, and final product acceptance require the named human authority.

