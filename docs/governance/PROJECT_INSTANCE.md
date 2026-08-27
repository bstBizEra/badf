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

## Validating an instance (`BADF-WP-0022`, Issue #35)

`badf_gate.py instance <path>` is what makes `badf/` governed rather than decorative. It
runs from the framework, reads the instance at `<path>`, writes nothing, and refuses
unless every one of these is established:

- `badf/project.yaml` parses in the subset and, with `badf/state.json` and the receipt,
  passes its schema;
- the three documents **agree**: project id, work package, baseline commit, framework
  revision, repository, classification;
- the **baseline commit exists in the instance and is an ancestor of its HEAD** — a project
  keeps committing; the baseline is where BADF entered, not where the project must stay;
- the pinned **`framework_revision` is a commit this framework has** — an instance cannot
  claim a framework that does not exist;
- `badf/lockfile.json` — written by init with the same implementation as the framework's
  own lockfile — corroborates `project.yaml`, `state.json`, every receipt, and `AGENTS.md`
  **when BADF generated it**. A preserved `AGENTS.md` is the project's file: a change since
  baseline is *reported*, never refused.

A hand-edited `state.json` is drift. Re-signing (`lock --instance <path>`) makes the edit
visible, and the corroboration then refuses what the receipt cannot support — re-signing
does not launder a state; only a governed transition (later work package) may move it.

## The authority instance (`BADF-WP-0023`, Issue #37, `BADF-DEC-0006` — delegated)

> Local instructions may **narrow** authority; they can never expand it.

`badf/authority/charter.json` is that sentence made mechanical:

- **The floor is pinned.** The charter binds, by digest, the framework's
  `badf/authority-matrix.json` **at the instance's `framework_revision`** — the same commit
  everything else in the instance consumes. If the framework's matrix has moved since the
  pin, `instance` reports it; adopting it is a re-pin, not a silent drift.
- **Superset or refused.** Exactly the framework's change classes; each class's
  `required_roles` ⊇ the floor's; `reserved_actions` ⊇; `human_reserved_roles` ⊇; no rule's
  `minimum_class` lowered. The comparison is the framework's own monotonic-guard function —
  one definition of "downgrade", not two.
- **No acknowledgement path.** The framework can admit a downgrade of its own matrix under a
  decision record and an explicit ack. An instance cannot: `BADF_AUTHORITY_DOWNGRADE_ACK`
  is not read when validating a charter. A project does not ack itself below the floor.
- **Adding is free.** A project may add roles (`data_protection_officer`), reserved actions,
  human-reserved roles. Adding constraints is strengthening, which §10 permits without a
  declaration. A charter grants nothing — every dossier still needs its human approvals.
- **Status is derived.** `charter <path>` writes the default charter (floor = ceiling) and
  re-derives `state.json`: `authority.status` becomes `RESOLVED` with the charter path, and
  `project.yaml authority.policy` names it. `instance` recomputes the same derivation and
  refuses a state that says `RESOLVED` without a valid charter, or `UNRESOLVED` with one.

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
