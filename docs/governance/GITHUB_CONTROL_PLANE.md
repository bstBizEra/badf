# BADF GitHub Control Plane

**Status:** Normative. Work package `BADF-WP-0016`, demand record Issue #19 (the first Issue this repository has ever had).
**Enforced by:** GitHub ruleset *BADF — Main Integration Contract* (active, zero bypass actors) and
repository merge settings; the PR-traceability check in `.github/workflows/badf-gates.yml`.
Everything else in this document binds by review, and says so.

## Doctrine

> No direct mutation of `main`. No material code without a Work Package. No Work Package without an
> Issue or authorized demand. No integration without a PR. No merge because a branch is green. Merge
> only after current composed-tree verification, independent challenge, authority validation, and
> evidence binding. Every discovery becomes an Issue; every resolved Issue becomes potential
> institutional learning.

| GitHub object | BADF meaning | Can mutate `main`? |
| :--- | :--- | ---: |
| Issue | demand / problem contract — never a solution contract | no |
| Work Package | authority contract | no |
| Branch `wp/<WP>-<slug>` | execution sandbox | no |
| Draft PR | live delivery dossier | no |
| Ready PR | integration candidate | no |
| Merge (squash, via PR) | authorized state transition | **only path** |
| `main` | accepted state ledger | never directly |

## BADF-MAIN-001 — `main` is not a workspace

No actor — human, agent, automation, App, MCP tool, or administrator in normal operation — may
create commits on `main` directly. Every change to `main` originates on another branch, has a PR,
references an authorized Issue and Work Package, passes required checks against the **current**
integration target, is squash-merged, and receives post-merge reconciliation.

## What this repository did before this document, stated plainly

Measured on 2026-08-28 before any change (Issue #19):

- `main` was **not** PR-only. A direct push was refused only because `governance` was a required
  status check that had never reported on a push commit. No rule required a PR.
- Zero rulesets. Classic protection carried 6 of the 11 rules in the recommended contract.
- All 18 PRs were merged with `--merge`; three merge methods were permitted; auto-merge was off.
- **Zero Issues had ever been opened.** 23 of 23 non-merge commits reference no Issue. Every work
  package's demand was a chat message.

The doctrine above was not how BADF was built. It is how BADF is built from `BADF-WP-0016` on. A
document that read as though compliance had always held would be the "claim that outlives its
correction" this repository keeps finding in itself.

## Deviation from the recommended ruleset, recorded

`required_approving_review_count` is **0**, not the recommended 1. This repository has one
collaborator; a review requirement makes every PR permanently unmergeable (proven on secb_pf).
Independent review is enforced by BADF's own gate — `independent_reviewer` approvals, typed
principals, human-reserved roles — not by GitHub's review count. When a second identity exists,
raise this to 1 and delete this paragraph.

## Branch classes

`wp/BADF-WP-NNNN-<slug>` for authorized work · `research/BADF-RSR-NNNN-<slug>` for investigation
requiring mutation · `fix/BADF-BUG-NNNN-<slug>` · `gov/BADF-WP-NNNN-<slug>` for Tier-B/C changes.
The authority object is in the name so the chain Issue → WP → branch → PR → `main` is greppable.

## Demand records (`BADF-WP-0018`, Issue #22)

The gate makes zero network calls, so "the Issue exists" is unknowable at gate time. The
Issue is the **source**; the demand record `badf/demands/BADF-DEM-NNNN.json` is what the
gate verifies, under the integrity lockfile.

- **Allocation.** `demand_id` is sequential — the next unused number. It never encodes the
  Issue number (PRs and Issues share one number space); `source.issue` carries that.
  `BADF-DEM-0004` is Issue #19; `BADF-DEM-0005` is Issue #22.
- **Kinds.** `issue` (exported from a GitHub Issue, body digest-bound) · `token` (a
  `[WP-NNNN]`-style admission token in a repository with no Issue space) · `decision` (an
  operator decision with no Issue) · `discovery` (found by BADF itself).
- **Provenance** is how the record was produced, distinct from kind:
  `EXPORTED_FROM_SOURCE` · `RECONSTRUCTED` (written after the fact, and says so) ·
  `DISCOVERED`.
- **Authority.** `authorized_by` must be a **human** principal for every kind except
  `discovery`. A demand is where authority enters; an agent cannot manufacture one, and
  re-signing the lockfile does not change that — the gate refuses on `principal_type` after
  integrity passes. A `discovery` demand carries no authorizer, so its human gate is the merge.
- **One demand, one repository.** A work package's `repository` must equal its demand's
  `source.repository`; `badf init` refuses otherwise. This answers Issue #22's open question:
  a demand *may* originate in the target project's Issue or token space, but the record lives
  in BADF's tree, and a cross-repository demand is refused, never reinterpreted.
- **Every shipped work package carries `demand`.** Work packages that predate this record
  their demand as `RECONSTRUCTED` (`BADF-DEM-0001`, `-0002`); `WP-2026-0016`'s record was
  written late and says so. The PropTech intake's demand is the operator's decision
  (`BADF-DEM-0003`) — PropTech has no Issues, and its tokens are its own work.

## Reconciliation (`BADF-WP-0019`, Issue #26)

A work-package record cannot know its own squash SHA before it lands, and `main` is
PR-only, so nothing could update it after — `WP-2026-0018` landed as `c510516` with a
record that said `IN_PROGRESS`. Landing is a fact of the git ledger, so the gate derives
it rather than trusting the record.

- **Derived.** A self work package has landed iff a commit on the first-parent history of
  `origin/main` carries its `Work-Package:` line. No network call, no per-WP
  reconciliation PR.
- **Claims are corroborated.** A record may carry `external_target.landed_as` only if that
  commit is on the ledger and carries the record's line — and then its status must be
  `CLOSED`. A `CLOSED` record without a corroborated landing must state
  `landing_not_on_ledger: <reason>`; that statement is refused if the ledger does show a
  landing.
- **Silence is named.** A landed record that claims nothing is reported by `repo` as
  `LANDED_UNRECONCILED`. On `main` it is not a failure; it is a visible debt.
- **Debt blocks the next opening.** A tree that adds a work-package record absent from
  `origin/main` while any self work package is `LANDED_UNRECONCILED` is refused. The branch
  that opens the next WP therefore starts with `badf_gate.py reconcile <WP>`, which writes
  the corroborated claim and re-signs the lockfile — *sync before you start*, mechanized.
  Reconciliation rides in that PR under that WP's own traceability; `check_pr_traceability.py`
  is unchanged.
- Foreign work packages (`repository` ≠ this one) land in another ledger and are outside
  this rule.
- **The tree that is tested is not the tree that lands.** A PR runner's `origin/main` is the
  pre-merge ledger; the merge itself adds the new landing. `WP-2026-0019` shipped this rule
  green and turned `main` red at `30186c5` because its tests assumed a debt-free ledger
  (#31). Before merging a PR whose tests read the ledger, simulate the post-merge tree:
  squash the branch onto a local `main` in a scratch clone, point `origin/main` at it, run
  the suite. Fixtures normalise inherited debt and add only what they assert on. Since
  `BADF-WP-0024` (#21) this is a **named gate**: `scripts/badf_compose.py` does it
  deterministically and CI runs it on every pull request with the PR body as the squash
  message — the gate refuses a message the ledger would not see, nests exactly one level
  (its own tests run in the composed world; `0b88c74` went red because they did not), and
  writes nothing to the source repository. Run it locally before pushing:
  `python3 scripts/badf_compose.py --message-file <pr-body> [--ci-shape]`.
  **What it cannot see:** a composed world always has a `main` branch, but a pull-request
  runner's checkout is detached with none — a fixture that `git clone`s it gets no
  `origin/main`. The plain *Run validator tests* step on the runner is the control for that
  shape (WP-0029: 13 advance tests red there, green in the composed run). Scratch clones pin
  `origin/main` explicitly (`tests/_scratch.pin_origin_main`).

## Resolved Issues become learning (`BADF-WP-0035`, Issue #29)

The Doctrine's last clause — *every resolved Issue becomes potential institutional learning* —
is now enforced, not aspirational. A demand that reaches a terminal status (`RESOLVED` or
`REJECTED`) carries a `learning`: a `docs/learnings/<slug>.md` file that exists, or the literal
`NONE_DECLARED`. `badf_gate.py repo` refuses a terminal demand with neither — an explicit
"nothing learned" is a claim; silence is drift. Learnings are extend-only (`docs/learnings/`).
Flipping a demand from `AUTHORIZED` to `RESOLVED` when its Issue closes is not yet automatic
(the same shape as the reconciliation debt); the requirement bites the moment a demand *is*
marked terminal.

## Issue and PR body shape (`BADF-WP-0034`, Issue #27)

Shape is **requested** on GitHub and **enforced** where BADF reads it — the two are
different surfaces:

- **Requested.** `.github/ISSUE_TEMPLATE/demand.yml` is an Issue Form asking for the
  problem-contract sections (Observed / Expected / Evidence / Unknowns / Proposed work
  package); `config.yml` turns blank issues off. `.github/pull_request_template.md` asks for
  `## What`, `## Verification`, and the two trailer lines.
- **Enforced.** `gh … --body-file` bypasses the web templates (every artefact this session
  was filed that way), so the templates alone enforce nothing. The PR body is the squash
  commit message on `main` — the surface the next agent greps — so
  `scripts/check_pr_traceability.py` (a required CI step) now refuses a PR body missing
  `## What`, `## Verification`, or a trailer line, naming which.
- **Not enforced on demands.** An `issue`-kind demand's `problem` is a **verbatim,
  digest-bound** export of the source Issue; the gate never rewrites or rejects it on shape.
  `BADF-DEM-0016` (the external `#41`, structured Objective/Scope/…) is left exactly as
  exported. The Issue Form is the requested shape for *new* Issues, not a retroactive gate.

## Self-work-package dossiers (`BADF-WP-0033`, Issue #28)

BADF governs other projects through gate dossiers; its own work packages had only CI and
traceability. `badf_gate.py self-dossier <WP>` assembles a **G07 dossier** for one of BADF's own
work packages from measured evidence — the change diff, `py_compile`, a pointer to the
composed-tree gate for tests, the docs diff — as a `HUMAN_REQUIRED` request. It binds evidence;
it never approves. The composed-tree gate validates a candidate's G07 dossier on the tree that
would land (`exit 0` = APPROVED, `3` = HELD; `1`/`2` fail the gate). A self-work-package's
source-change diff is taken against `HEAD` excluding the work package's own directory and the
lockfile — its branch commits do not survive the squash, so `base..HEAD` is the same tree
comparison on the branch, in the composed tree, and on `main`. A carried `OPEN` condition records
the missing independent reviewer under a single collaborator: recorded, not hidden.

## Research records (`BADF-WP-0031`, Issue #50)

Research sits between discovery and decision: **Issue → demand → research record → decision → work
package**. A run is `work/research/<BADF-RSR-NNNN>/research-record.json` (ids sequential; `source.issue`
carries the Issue), under the lockfile, checked by the gate's schema. Its disposition creates nothing
downstream; a decision and a work package cite it. `RESEARCH_SUFFICIENT ≠ IMPLEMENTATION_AUTHORIZED` is
fixed by the schema, not by discipline. The `badf-research` skill family is `DESIGNED` and does not run;
its contract lives in `skills/badf-research/references/`.

## Discovery ≠ scope expansion

Work on `BADF-WP-A` that finds problem B opens an Issue for B (`status: DISCOVERED`,
`discovered-by: BADF-WP-A`) and does **not** fix B in A's branch. This is `AGENTS.md`'s
"no silent scope expansion", given a mechanism.

## Not adopted

No permanent `develop` branch. Trunk-oriented: `main` ← PR ← short-lived authorized branch.
