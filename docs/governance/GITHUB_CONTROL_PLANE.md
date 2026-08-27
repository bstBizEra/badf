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

## Discovery ≠ scope expansion

Work on `BADF-WP-A` that finds problem B opens an Issue for B (`status: DISCOVERED`,
`discovered-by: BADF-WP-A`) and does **not** fix B in A's branch. This is `AGENTS.md`'s
"no silent scope expansion", given a mechanism.

## Not adopted

No permanent `develop` branch. Trunk-oriented: `main` ← PR ← short-lived authorized branch.
