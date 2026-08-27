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
python3 scripts/badf_compose.py --message-file <pr-body>   # the tree that would land, not the branch
```

Start new work from `templates/work-package.json`, use `templates/session.md` for execution continuity, and create a gate dossier from `templates/gate-dossier.json` when requesting advancement.

## Initialising a project (`badf init`)

BADF governs **other** repositories. `badf init <intent>` takes a project in at G00 and
writes a bounded control plane into it — `AGENTS.md` (only if absent) and `badf/`
(`project.yaml`, `state.json`, `evidence/receipts/init-<ts>.json`) — and nothing else; the
rest of the target is byte-identical before and after. Framework vs instance is defined in
[`docs/governance/PROJECT_INSTANCE.md`](docs/governance/PROJECT_INSTANCE.md).

The intent is a JSON/YAML mapping under `project`:

| Field | Required | Meaning |
| :--- | :---: | :--- |
| `name` | yes | product name |
| `intent` | yes | one sentence: what is being built |
| `owner` | yes | the organisation or person accountable |
| `target` | yes | `production` or `sandbox` |
| `repository` | yes | `owner/name` on GitHub; must equal the demand's `source.repository` |
| `local_path` | yes | a clean git checkout of that repository (never the framework itself) |
| `demand` | yes | `BADF-DEM-NNNN` — the record in `badf/demands/` that authorises intake |
| `project_id` | no | e.g. `BST-PROPTECH`; derived from owner and name when absent |
| `type`, `maturity` | no | recorded as given, else `DECLARED_MISSING` — never guessed |

A complete example is [`examples/intent.json`](examples/intent.json). Any key outside this table is
refused, not ignored — a typo of an optional key would otherwise be invented as `DECLARED_MISSING`.

The G00 dossier renders `HUMAN_REQUIRED`: an instance is a request for authority, not a
grant of it. `python3 scripts/badf_gate.py instance <path>` validates an instance —
documents, cross-document agreement, git corroboration, and the instance lockfile — and
writes nothing. `python3 scripts/badf_gate.py charter <path>` binds an instance to the framework's
authority matrix at its pinned revision (a charter may add constraints, never remove them). `python3 scripts/badf_gate.py advance <path> <dossier>`
binds an APPROVED dossier for the instance's next gate; the instance's gate is derived from that chain. Refusals write nothing: dirty tree, existing `badf/`, the framework as target,
a demand for another repository.

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

