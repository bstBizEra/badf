# BADF Framework and BADF Project Instance

**Status:** Normative. Work package `BADF-WP-0021`, demand Issue #33, decisions
`BADF-DEC-0004` (bounded write) and `BADF-DEC-0005` (keep G00–G14, amend G00).

## Two things, named

| | Lives in | Contains |
| :--- | :--- | :--- |
| **BADF Framework** | `bstBizEra/badf` | schemas, validators (`scripts/badf_gate.py`), the canonical lifecycle and policies, templates, built-in skills, tests |
| **BADF Project Instance** | `bstBizEra/<project>` | `AGENTS.md` (agent entrypoint) + `badf/` (the project's control plane) |

A project initialised **by** BADF consumes the framework by reference — the instance
pins `framework_revision` — and never becomes a copy of it. The framework's `docs/`,
registries, skills and policies are **not** copied into projects: fifty stale copies of
`lifecycle v1.1` is the failure this rule exists to prevent. The project's `docs/` is
product documentation; governance records live under `badf/`.

## What `badf init` does (BADF-DEC-0004)

```text
DISCOVER  what the project states about itself (AGENTS.md, README, CI, admission scripts)
CLASSIFY  GREENFIELD | BROWNFIELD from the tracked tree; type/maturity from the intent or DECLARED_MISSING
BASELINE  target HEAD, tree must be CLEAN, digest of any existing AGENTS.md
GENERATE  <project>/AGENTS.md (only if absent) · badf/project.yaml · badf/state.json
VALIDATE  every generated file against its schema; refuse before writing otherwise
REGISTER  badf/evidence/receipts/init-<ts>.json in the project; the same bytes bound as
          BADF-side G00 evidence `init-receipt`; the BADF work package, dossier (HUMAN_REQUIRED),
          registry entry and ledger event as before
```

**The write is bounded.** Everything outside `<project>/AGENTS.md` and `<project>/badf/`
is byte-identical before and after — proven by digest in the tests, not asserted.
Directories materialise with their first record; there is no skeleton and no `.gitkeep`.

**Refusals (fail closed, nothing written):** the target is not a git repository · the
working tree is dirty · `badf/` already exists (never overwrite an instance) · the target
is the framework itself · the demand names another repository.

**An existing `AGENTS.md` is preserved untouched** and recorded in the receipt as
`preserved` with a conflict `PRESERVED_MERGE_PLAN_REQUIRED`; `state.json.entrypoint` says
`EXISTING_AGENTS_MD_PRESERVED`. Compatibility analysis and merge are a later work package.

## The three day-0 files

| File | Answers | Nature |
| :--- | :--- | :--- |
| `badf/project.yaml` | *what* project this is, which framework revision, where authority/state/evidence live | declared by the intent; judgment never invented (`DECLARED_MISSING`) |
| `badf/state.json` | *where* the project is: `G00 / INITIALIZED`, authority `UNRESOLVED`, readiness `NOT_STARTED` | **derived** from the baseline and receipt; never edited by hand; a stored state the gate cannot corroborate is refused (BADF-WP-0022) |
| `badf/evidence/receipts/init-<ts>.json` | *what init did*: baseline commit, classification, `generated` / `preserved` / `conflicts`, each path digest-bound | the first link of the evidence chain `INIT → PRODUCT → PRD → WORK PACKAGE → COMMIT → BUILD → ARTIFACT → DEPLOYMENT → RUNTIME` |

`project.yaml` is written in a strict YAML subset (block mappings, lists, scalars) that
the framework emits and parses without a dependency; anything outside the subset is
refused, not guessed.

## Not on day 0 — each arrives with its first record

`badf/authority/` (BADF-WP-0023: an instance charter may **narrow** the framework's
authority, never expand it; the monotonic guard runs instance-vs-framework) ·
`agents/ councils/ work/ gates/ sessions/ memory/ knowledge/ skills/ tools/ mcp/ policies/
releases/ operations/ learning/`. `policies/*.rego` needs an evaluator BADF does not have.
`badf/` is the namespace now; `.badf/` only if a collision is demonstrated.

## Lifecycle (BADF-DEC-0005)

G00–G14 keep their ids and semantics. G00 — *Intake, authority and project definition* —
now states explicitly that a project may enter from nothing: the instance exists, the
product is defined, the PRD is G01's business.
