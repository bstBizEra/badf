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

## repository-research subskill + control 3 (`BADF-WP-0040`, RSR-006)

The first of the nine P0 research subskills. `skills/badf-research/subskills/repository-research/
SKILL.md` is the declarative workflow for investigating a repository (commits, PRs, issues,
history) and producing an `R02`/`R03` research record, binding every finding to a commit SHA;
its invariant is *current state is not historical evidence*. Control 3 is now enforced: a
repo-type record's `baseline.repository` must be registered and `baseline.revision` must resolve
there (an absent `LOCAL_MIRROR` reports `UNRESOLVABLE_HERE`, like `verify_foreign_revision`).
`examples/research-record-repo.json` is validated in CI. **Sixteen of the eighteen controls are
now enforced.** Control 6 (source-digest staleness, needs a source fetch) and the other eight P0
subskills remain, one WP each. `badf-research` stays `DESIGNED`.

## Research evidence digest (`BADF-WP-0039`, RSR-005 control 17)

A record's `evidence_digest` is the sha256 of its **material evidence** — sources, claims,
contradictions, experiments — in canonical JSON, **computed by the gate, not asserted**. A
claim or source edited without re-digesting is stale and refused; editing interpretation
(findings, recommendation, disposition) does not change it. **Fifteen of the eighteen controls
are now enforced.** The last three need machinery beyond a record check: baseline
git-resolution (3, `repository-research` subskill territory), source-digest staleness detection
(6), which need a subskill and a source-fetch respectively. `badf-research` stays `DESIGNED`.

## Research conclusion integrity and traceability (`BADF-WP-0038`, RSR-004)

Four more controls, about whether a record's conclusion holds together and traces back:
a disposition other than the in-flight `RESEARCH_BLOCKED` means the research **concluded**, so
the state must be `RECONCILED` — an invalid state fails closed (control 16); a `CHALLENGED`
state requires a council; a claim that cites contradicting sources must be **recorded** in
`contradictions[]`, not buried in the claim (control 8, RSR-I04); only `RESEARCH_SUFFICIENT`
may name a downstream work package (control 15); and the chain **Issue → demand → research →
decision → work package** must reconstruct — the demand resolves, a named decision resolves and
governs the named work package, and a named work package has a record (control 18). **Fourteen
of the eighteen controls are now enforced.** The three remaining need machinery beyond a record
check and are their own later work: baseline git-resolution (control 3, when a
repository-research subskill lands), source-digest staleness (control 6), and the record's
`evidence_digest` recomputation (control 17). `badf-research` stays `DESIGNED` until all pass.

## Research challenge and independence (`BADF-WP-0037`, RSR-003)

Four more of the 18 controls, about who challenges research and how independence is counted:
a claim's `independent_primary_sources` cannot exceed the distinct PRIMARY sources it cites
(source *count* is not independence); challenge is **required** — computed, not asserted — at
depth `D4`/`D5` or type `R06`; when required, a council must carry at least two **distinct**
reviewers; the **researcher cannot ballot** on their own research (RSR-I05); a **duplicate
reviewer identity cannot** increase quorum; and every ballot **declares non-coverage** (a list
of surfaces it did not review). The record gains a required `researcher` field. Council
structure is validated in code (a nullable object defeats the schema walker). `examples/
research-record-challenged.json` exercises the council path in CI. The state-transition and
traceability controls remain later work packages; `badf-research` stays `DESIGNED`.

## Research record checks (`BADF-WP-0036`, RSR-002)

The frozen research contract (`BADF-WP-0031`) begins to be enforced. `badf_gate.py research
<path>` validates a research record's deterministic **record/source/claim** controls: schema
conformance, referential integrity (every claim's source refs and every finding's claim refs
exist), **confidence derived not asserted** (`derive_confidence` recomputes the level from the
basis and refuses a mismatch, like the two-plane verdict), and the invariants that a `VERIFIED`
claim rests on an independent primary source (RSR-I02) and an `OBSERVED` claim on a primary
source (RSR-I03). `RESEARCH_SUFFICIENT ≠ IMPLEMENTATION_AUTHORIZED` stays schema-fixed. CI runs
it on `examples/research-record.json`. The challenge, state-transition and traceability controls
(the rest of the 18 in `skills/badf-research/references/acceptance.md`) are later work packages;
`badf-research` stays `DESIGNED`.

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

## Gate 02 — requirement decomposition (`BADF-WP-0041`, Issue #70)

`lifecycle.json` declared G02 (`requirements`, `nfr`, `traceability`, `definition-of-ready`)
before anything enforced it — a G02 dossier would have passed on names alone, the G01 defect
class one gate downstream. The four types now have per-type rules in `validate_evidence`, exactly
like G01's: the gate **opens** each artifact. `requirements` — unique `REQ-NNN`, each tracing to
at least one objective in the RTM's universe. `nfr` — each `NFR-NNN` target value must be a real
number (`"fast"` and `true` are refused); "NFRs quantified" becomes a deterministic check.
`traceability` — the RTM, bidirectional and complete: no orphan requirement, no uncovered
acceptance criterion, no id that dangles off either side. `definition-of-ready` — a **human**
sign-off whose checklist must cover every one of G02's own `exit_criteria`, read from
`lifecycle.json` (the gate checks itself against its declared exits). The `advance` machinery was
already generic over `GATE_ORDER`, so an instance at `G01/APPROVED` advances to `G02/APPROVED` on
a valid G02 dossier with no new transition code. Planned **fresh from #46** on the merged G01
substrate — reusing `validate_evidence`, no competing `scripts/badf_requirements.py`, no vendored
Spec-Kit; the `badf-requirements` authoring skill and the capability/epic hierarchy are named,
deferred WPs.

## Gate 03 — UX and service design (`BADF-WP-0042`, Issue #72)

The gate march continues one gate at a time: G03's four types (`journeys`, `service-blueprint`,
`accessibility`, `user-validation`) were declared but unenforced. Each now has a per-type rule in
`validate_evidence`, and each maps to one of G03's exit criteria. `journeys` — unique `JRN-NNN`
with non-empty steps, and the set must design **both** a happy and an unhappy path (an all-happy
design is refused). `service-blueprint` — one lane per journey, reached through the `journeys`
sibling: no uncovered journey, no lane for an unknown journey (the coverage cross-reference, G03's
RTM analogue), and every lane must define support actions. `accessibility` — a declared standard
and enumerated criteria, each `met` or `not_applicable` **with a rationale**. `user-validation` —
**human**-produced, a positive participant count, and every `major`/`critical` finding carrying a
resolution (an unresolved major finding means the design is not validated). Ships
`examples/gate-dossier.G03.json` and a G02→G03 pair-acceptance. Same lean substrate as G01/G02 —
no design-authoring skill, no vendored UX toolkit.

## Architecture capability freeze (`BADF-WP-0043`, Issue #74)

`badf-architecture` is frozen at `DESIGNED` — an architecture **engineering + assurance** capability,
not a diagram skill — the same way `badf-research` was frozen (#50): a `SKILL.md` + `references/`
contract, a registry entry with a real digest, and a doc-structural test, with **no executable and
no G04 authority change**. The four distinctions that never collapse: architecture documentation ≠
assurance ≠ gate authority ≠ implementation authorization. Two modes — DESIGN (a canonical,
machine-readable architecture **baseline** from which C4/Mermaid are rendered as *views*, plus
boundaries, trust boundaries, data flows, ADRs, NFR allocation, operability, fitness obligations)
and ASSURE (dependency direction, cycles, boundary violations, ADR compliance, drift, non-coverage —
read-only, bound to one baseline + one observed revision). Twelve invariants `ARCH-I01`..`ARCH-I12`
pin the meaning: views are projections (a diagram never adds a claim absent from the baseline), no
inferred compliance (`NO BASELINE ≠ COMPLIANT`), drift is evidence not authority, `ADR-*` ≠
`BADF-DEC-*`, and **no second gate** (no `scripts/badf_architecture.py` — deterministic G04 semantics
belong in the canonical gate). G04 is *mapped* (its five evidence types) but left exactly as declared;
the G04 DESIGN semantics (WP-ARCH-B) and the ASSURE substrate (WP-ARCH-C) are separate, later WPs.

## Gate 04 — architecture DESIGN semantics (`BADF-WP-0044`, Issue #76)

WP-ARCH-B implements the DESIGN-side controls of the frozen `badf-architecture` contract inside the
canonical gate (ARCH-I11 — no second validator), advancing the capability `DESIGNED → IMPLEMENTED`.
G04's five types now open their artifacts, with `architecture` as the **spine** the other four are
consistent with. The baseline enforces the frozen controls: a relationship with no **intent** or a
boundary crossing not through a **declared interface** is refused (an `A → B` is not architecture);
an element outside every declared boundary is refused; a trust-boundary data flow with no
**classification** is refused; an NFR that is neither `ALLOCATED` (to an element + mechanism +
fitness obligation) nor deferred-with-reason is refused; a fitness obligation with no measurable
property or scope is refused; and a C4-view element absent from the baseline is refused (ARCH-I02 —
views are projections). `adr` binds each decision to real baseline elements and to declared
requirement/NFR refs (`ADR-*` never a `BADF-DEC-*`); `data-model` entities resolve to a declared
ownership boundary; `api-contract` interfaces resolve to declared architecture interfaces and are
versioned; `operability-design` must declare failure modes with recovery and observability seams.
Ships `examples/gate-dossier.G04.json` and a G03→G04 pair-acceptance (the full G00→G04 chain). The
ASSURE substrate (controls 13–18) is WP-ARCH-C; VALIDATED awaits it.

## Research scope-contract hardening (`BADF-WP-0045`, Issue #79)

The frozen research contract (#50) had a SKILL↔schema asymmetry: `badf-research/SKILL.md`
instructs the researcher to *resolve stop conditions*, but the record schema carried no
`stop_conditions`, `assumptions`, or `decision_context`. Fixed **extend-only through a governed WP,
not by reopening #50**: the three fields are now first-class, required record fields, and
**control 19** enforces a bounded, machine-readable scope — non-empty `stop_conditions` (no
unbounded research), each `assumption` a non-empty statement kept distinct from evidence, and a
`decision_context.decision_question` naming the decision the run serves (reinforcing RESEARCH ≠
DECISION while `authority.implementation_authority` stays `false`). These are **framing, not
evidence**, so they are excluded from the `evidence_digest` — control 17 is unaffected, proven by a
test that changing only framing leaves a record valid. Research controls: **17 of 19** enforced
(control 6 freshness needs a source fetch; control 15 rides the state machine). `badf-research`
stays `DESIGNED`. Overlaps external #69/#77, built fresh under #79 with their work untouched.

## Discovery ≠ scope expansion

Work on `BADF-WP-A` that finds problem B opens an Issue for B (`status: DISCOVERED`,
`discovered-by: BADF-WP-A`) and does **not** fix B in A's branch. This is `AGENTS.md`'s
"no silent scope expansion", given a mechanism.

## Not adopted

No permanent `develop` branch. Trunk-oriented: `main` ← PR ← short-lived authorized branch.
