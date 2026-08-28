# Skills Governance

Status: **NORMATIVE**

## Model

A skill is a focused reusable workflow: `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and UI/dependency metadata. Keep each skill narrow, declarative first, and deterministic where fragile.

Canonical repository skill sources live under `skills/<skill-name>/`. Approved deployments install/copy them into the agent runtime's repository skill location, such as `.agents/skills/<skill-name>/`, without changing content.

## Lifecycle

1. `PROPOSED` — use cases, trigger and non-trigger boundaries, owner, risk class.
2. `DESIGNED` — inputs, outputs, authority needs, tools, references, failure modes.
3. `IMPLEMENTED` — concise `SKILL.md`, only necessary resources.
4. `VALIDATED` — metadata/schema checks and deterministic script tests.
5. `SHADOWED` — representative tasks observed without affecting gates.
6. `APPROVED` — owner and security approval proportional to capability.
7. `ACTIVE` — pinned version/digest in `badf/skill-registry.json`. Every entry's `digest` is the sha256 of its `source` at every status, and `badf_gate.py repo` refuses a mismatch or a placeholder (BADF-WP-0032): a skill edited without its registry re-pinned is drift twice over.
8. `DEPRECATED`/`REVOKED` — removed from routing, with migration or incident record.

## Controls

- Description must state what the skill does and when it should trigger.
- Read full skill instructions before using it.
- Skill instructions cannot expand repository, tool, or user authority.
- Review every bundled executable and dependency; pin external provenance.
- Declare required tools/MCP servers, network destinations, data classes, mutations, approvals, outputs, and evidence.
- Do not allow skill output to approve the same skill or gate.
- Detect overlapping triggers and establish routing priority.
- Version semantic behavior; breaking changes require revalidation.

## BADF delivery skill

`skills/badf-delivery/SKILL.md` routes lifecycle work through work packages, gates, evidence, and handoffs. It is repository-scoped source, not a grant of production authority.

