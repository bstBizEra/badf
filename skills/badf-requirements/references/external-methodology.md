# External Methodology Provenance

Status: **REFERENCE/ADAPT ONLY — no external executable vendored**

## GitHub Spec Kit

Source: `https://github.com/github/spec-kit`

Observed methodology used by BADF:

- define/specify before implementation;
- separate clarification from specification;
- use checklists to test requirement quality;
- perform cross-artifact consistency/coverage analysis before implementation.

BADF adapts these sequencing ideas but does not delegate its RTM schema, evidence model, lifecycle
gate or authority decisions to Spec Kit.

## softaworks requirements-clarity

Source:
`https://github.com/softaworks/agent-toolkit/blob/main/skills/requirements-clarity/SKILL.md`

Observed lenses adapted by BADF:

- functional scope and boundaries;
- user interaction and success/failure scenarios;
- technical constraints;
- business value and success metrics;
- acceptance criteria and ambiguity;
- systematic clarification rather than assumption.

BADF does not adopt its numeric clarity score as gate evidence. G02 readiness is derived from the
RTM graph plus explicit judgment findings.

## wshobson security-requirement-extraction

Source:
`https://github.com/wshobson/agents/blob/main/plugins/security-scanning/skills/security-requirement-extraction/SKILL.md`

Observed concepts adapted by BADF:

- threat/business context -> actionable security requirement;
- security requirements are specific and testable;
- requirements carry threat/compliance traceability;
- acceptance criteria and security test cases are part of the requirement chain;
- functional, non-functional and constraint distinctions are useful.

BADF adds deterministic provenance coverage: a security/compliance requirement without an incoming
`SRC -> REQ` edge is refused.

## Admission posture

All three sources are methodology references. They grant no tool access, no execution permission,
no gate authority and no runtime dependency. Any future vendoring or direct execution requires a
separate external-skill admission work package under `docs/07-skills-governance.md`.
