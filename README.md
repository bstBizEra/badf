# BizEra Agent Delivery Framework (BADF)

BADF is a repository-native governance and delivery framework that moves an authorized product idea from PRD to production, then through production verification, operations, assurance closure, and reusable learning.

## What this baseline includes

- root agent operating charter (`AGENTS.md`);
- 15 lifecycle gates (`G00`–`G14`);
- advanced engineering and bounded autonomous loops;
- work-package, session, memory, evidence, and gate-dossier contracts;
- agent council and human-authority boundaries;
- skills, MCP, and tool governance;
- security, quality, release, SLO, incident, rollback, and learning controls;
- an executable fail-closed validator and CI workflow.

## Quick start

```bash
python3 scripts/badf_gate.py repo
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/badf_gate.py dossier examples/gate-dossier.G00.json
```

Start new work from `templates/work-package.json`, use `templates/session.md` for execution continuity, and create a gate dossier from `templates/gate-dossier.json` when requesting advancement.

## Repository map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Repository-wide agent operating charter |
| `docs/` | Normative operating policies and lifecycle guidance |
| `badf/` | Machine-readable lifecycle, authority, tool, MCP, and skill registries |
| `schemas/` | JSON contracts for governance artifacts |
| `templates/` | Starting artifacts for controlled work |
| `scripts/` | Deterministic policy validation |
| `tests/` | Validator regression tests |
| `skills/` | Governed repository skill sources |
| `.github/workflows/` | Continuous enforcement |

## Adoption sequence

1. Ratify owners, authority roles, risk thresholds, and systems of record.
2. Replace placeholder organizational references in registries.
3. Protect `AGENTS.md`, `badf/`, `schemas/`, gate scripts, and CI configuration.
4. Install approved skill sources into the runtime repository-skill location.
5. Run BADF in shadow mode; measure false blocks, bypasses, and evidence cost.
6. Promote gates incrementally after independent validation.

