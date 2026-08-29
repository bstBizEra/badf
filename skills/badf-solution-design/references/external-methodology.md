# External methodology provenance

Status: **REFERENCE / ADAPT ONLY — no external executable vendored, no external skill granted authority.**

`badf-solution-design` routes concerns to specialist *methodologies* and adapts their ideas into BADF
domain contracts. The external skills are references, not BADF authority; any future vendoring or direct
execution requires a separate external-skill admission WP under `docs/07-skills-governance.md`.

## Specialist methodology dispositions

| Domain | External methodology | BADF adapts | BADF does NOT adopt |
| :--- | :--- | :--- | :--- |
| UX / service | product-design-and-ux methods | task flows, interaction states, service blueprint, recovery paths | its tooling as BADF authority |
| Authorization | RBAC / ABAC / ReBAC / policy models | the `principal·resource·action·scope·context·policy·decision·audit` contract; RBAC as one model | any single model as the only model |
| Data | schema-design methods | entities, constraints, normalization, indexing, migration mechanics | data *ownership* decisions (that is architecture) |
| API | API-design + design-review methods | the DESIGN/ASSURE split and the breaking-change checklist | its verdicts as BADF authority (ASSURE emits evidence, not authority) |
| Accessibility | WCAG 2.2 AA methods | behavior bound to interaction states | a per-screen checklist as sufficient |

## Admission posture

External specialist skills are **REFERENCE / ADAPT**. They grant no tool access, no execution permission,
no gate authority and no runtime dependency. `badf-solution-design` composes their *contracts*; the
canonical gate validates the resulting evidence, and an authority dispositions delivery. This mirrors how
`badf-prd` and `badf-requirements` salvaged external methodology as reference-only.
