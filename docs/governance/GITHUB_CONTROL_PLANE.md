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

`wp/WP-2026-NNNN-<slug>` for every pull request to `main` — the canonical machine work-package id
in the name, lowercase kebab slug, **enforced by CI since `BADF-WP-0070`** (badf-git GIT-B; the
tier of a change lives in the work package's `change_class`, not in a branch prefix). The
`research/BADF-RSR-NNNN-<slug>` class remains declared for investigation requiring mutation but
has never carried a PR (0 of 61); the former `fix/…` and `gov/…` prefixes are retired display
conventions — a PR from them is refused. The authority object is in the name so the chain
Issue → WP → branch → PR → `main` is greppable and, now, checkable.

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

## problem-framing — the entry research subskill (`BADF-WP-0046`, Issue #81)

The second P0 research subskill (after `repository-research`), mirroring its shape: a concise
`SKILL.md` under `skills/badf-research/subskills/problem-framing/`, registered `IMPLEMENTED`, on the
frozen contract. It is the **entry** point — it turns a demand into a bounded, machine-readable
research *admission* (question, type, depth, scope/non-goals, known/unknown, hypotheses, and the
WP-0045 framing fields `assumptions`/`decision_context`/`stop_conditions`) — and its one invariant
is that it **sharpens the question but never researches or answers it**. That invariant is now a
deterministic refusal: **control 20** — a record in a pre-evidence `state` (`PROPOSED`/`FRAMED`/
`BASELINED`) carries no `claims`, `sources`, or `findings`; evidence appears only from
`EVIDENCE_COLLECTING` onward. Research controls: **18 of 20** (control 6 freshness deferred until
`deep-research` owns source acquisition; control 15 rides the state machine). The root `SKILL.md`'s
stale *"nothing here runs yet"* line is corrected; `badf-research` stays `DESIGNED` (2 of 9 P0).

## fact-checking — verification primitive, control earned not assumed (`BADF-WP-0047`, Issue #85)

The third P0 research subskill, a cross-cutting verification primitive:
`skills/badf-research/subskills/fact-checking/SKILL.md`
adjudicates claim `status` over evidence **already bound** to the record — it does not acquire
sources (that is `deep-research`). It reuses the frozen statuses; it adds no new vocabulary. Its
invariants: `NO EVIDENCE ≠ FALSE`, `NO CONTRADICTION ≠ VERIFIED`, `CITATION ≠ SUPPORT`.

The control was **earned by failing-first, not assumed**: adversarial probes against the current gate
showed a `FALSIFIED` or `DISPUTED` claim passed with *no contradicting evidence*. That gap is
deterministically enforceable, so **control 21** now requires a `FALSIFIED` claim to carry a
contradicting source and a `DISPUTED` claim to carry both sides (composing with the existing
contradiction-preservation control 8). The *semantic* half of `CITATION ≠ SUPPORT` — whether a
source's content entails the claim — has no content locator in the machine contract and is therefore
**not** forced into a weak verifier here; it is filed as its own issue (RSR-I06 candidate). Research
controls: **19 of 21**. `badf-research` stays `DESIGNED` (3 of 9 P0).

## evidence-synthesis — grounded findings (`BADF-WP-0048`, Issue #87)

The fourth P0 research subskill: `skills/badf-research/subskills/evidence-synthesis/SKILL.md`
reduces adjudicated `claims`, `contradictions` and `non_coverage` into decision-relevant `findings`
organised by consensus / strength / dispute / gap — *organising* evidence, not accumulating it
source-by-source. **Control 22, earned by failing-first**: a probe showed an *ungrounded* finding
(empty `claim_refs`) passed the gate, so the gate now requires every finding to reference at least
one claim — a synthesis conclusion rests on adjudicated evidence, not free assertion. (A second
measured gap — `RESEARCH_SUFFICIENT` with zero findings — is genuinely the disposition owner's, and
is left for `research-reconciliation` to earn rather than grabbed here.) Research controls: **20 of
22**. `badf-research` stays `DESIGNED` (4 of 9 P0).

## deep-research — acquisition contract, no control by design (`BADF-WP-0049`, Issue #89)

The fifth P0 research subskill and the named prerequisite for control 6:
`skills/badf-research/subskills/deep-research/SKILL.md` is the **read-only** external
source-acquisition plane — query decomposition, primary/authoritative-source preference, independent
corroboration, provenance capture (the source receipt), contradiction preservation — bounded by the
untrusted-environment authority boundary (it fetches; it never mutates, decides, or authorises).
**It earns no gate control, by design.** Its enforcement teeth are control 6 (the next WP), which
adds the receipt fields (retrieval outcome, resolved revision) and the staleness semantics. This is a
deliberate demonstration of the discipline that not every subskill lands with a control — a control
is earned by a measured, enforceable gap, not by precedent. Research controls unchanged at **20 of
22**. `badf-research` stays `DESIGNED` (5 of 9 P0).

## Control 6 — source-digest freshness (`BADF-WP-0050`, Issue #91)

The long-deferred acceptance control 6, unblocked now that `deep-research` owns acquisition. A source
carries a receipt field `freshness` (`CURRENT` / `STALE` / `UNKNOWN`) and an optional
`resolved_revision`; `deep-research` sets `freshness` on re-resolution — `CURRENT` when an immutable
revision resolves or the digest is unchanged, `STALE` when the bytes changed, `UNKNOWN` when it could
not be resolved. **Control 6 fails closed: a claim may not rest on a `STALE` or `UNKNOWN` source.** The
gate reads the receipt; it does not fetch (deterministic, no network) — the re-fetch is
`deep-research`'s, the consequence is the gate's. `freshness` is inside the `evidence_digest` (a source
going stale *is* an evidence change, so control 17 stays coherent); the three examples were migrated
with recomputed digests. This distinguishes *a URL still exists* from *the evidence is current*.
Research controls: **21 of 22** — only control 15 remains, owned by `research-reconciliation`.

## technical-research — grounded options (`BADF-WP-0051`, Issue #93)

The sixth P0 research subskill: `skills/badf-research/subskills/technical-research/SKILL.md` asks
*what approaches exist to solve it?* and yields an **option set** — candidate approaches with their
mechanism, limitations, security, compatibility, cost, migration and reversibility — without ranking
or choosing (that is `comparative-evaluation`). **Control 23, earned by failing-first**: probes showed
an `R04` (TECHNICAL_SOLUTION) record passed with *zero alternatives*, and an alternative could cite
*non-existent evidence*. So an `R04` record must now carry at least one `alternative`, and every
alternative's `evidence_refs` must resolve to a claim, finding or source the record holds — an option
is proposed on the strength of gathered evidence, not asserted. Research controls: **22 of 23**.
`badf-research` stays `DESIGNED` (6 of 9 P0).

## comparative-evaluation — a comparison weighs two (`BADF-WP-0052`, Issue #95)

The seventh P0 research subskill: `skills/badf-research/subskills/comparative-evaluation/SKILL.md`
weighs the `alternatives` `technical-research` produced against explicit comparable dimensions and
records the trade-off, **surfacing non-dominance rather than manufacturing a winner** (a null
`recommendation` is valid) — a recommendation is epistemic weight, never authorization. **Control 24,
earned by failing-first**: a probe showed a `COMPARATIVE` (R07) record passed with zero or one
alternative, so an R07 run must now carry ≥2 alternatives — a comparison of one option is not a
comparison. What the gate does *not* enforce is whether the evidence justifies a winner (it cannot),
so honest non-dominance stays a null recommendation. Research controls: **23 of 24** — only control 15
remains, for `research-reconciliation`, the last P0 subskill. `badf-research` stays `DESIGNED` (7 of 9).

## adversarial-research — a refutation is not erased (`BADF-WP-0053`, Issue #97)

The eighth P0 research subskill: `skills/badf-research/subskills/adversarial-research/SKILL.md` is the
**independent** challenge team — it tries to refute the recommendation (omitted/non-independent
evidence, counterexamples, unsupported assumptions, uninspected surface, confirmation bias), separate
from the originating run, casting sealed `CONFIRMED`/`REFUTED`/`INCONCLUSIVE` ballots through the
framework council (the independence/quorum/non-coverage controls 11–13 already hold). **Control 25,
earned by failing-first**: a probe showed a council carrying a `REFUTED` ballot could still reconcile
to `RESEARCH_SUFFICIENT`, so a `REFUTED` ballot now forecloses `RESEARCH_SUFFICIENT` — an independent
refutation is not overridden by a majority or by the disposition; it reconciles to
`CONTRADICTORY_EVIDENCE`, `MORE_RESEARCH_REQUIRED`, or another non-sufficient state. What the gate does
*not* check is whether a ballot genuinely attempted refutation (the reviewer's honesty, declared via
non-coverage). Research controls: **24 of 25** — only control 15 remains, for the last subskill,
`research-reconciliation`. `badf-research` stays `DESIGNED` (8 of 9 P0).

## research-reconciliation — sufficiency means synthesis; the P0 family complete (`BADF-WP-0054`, Issue #99)

The ninth and **final** P0 research subskill: `skills/badf-research/subskills/research-reconciliation/SKILL.md`
is the terminal step — its question is *do we know enough?*, not *what do we recommend?*. It returns a
controlled disposition (`RESEARCH_SUFFICIENT` … `RESEARCH_BLOCKED`), never PASS/FAIL, and holds the
`RESEARCH_SUFFICIENT ≠ IMPLEMENTATION_AUTHORIZED` boundary. **Control 26, earned by failing-first** (the
gap deferred from `evidence-synthesis`): a probe showed a `RESEARCH_SUFFICIENT` record passed with
*zero findings*, so sufficiency now requires at least one synthesised finding — research declared
sufficient on nothing synthesised is incoherent. An **accounting correction** rides here too: control 15
(`only RESEARCH_SUFFICIENT → downstream work package`) was **already enforced** since RSR-004/`BADF-WP-0038`;
an earlier admission note that mistracked it as pending is corrected. **With this WP the P0 family is
complete: 9 of 9 subskills, all 26 controls enforced** — the `IMPLEMENTED` and `VALIDATED` criteria are met.
The registry status advance (`DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → APPROVED → ACTIVE`) is the
operator's admission decision, so `badf-research` stays `DESIGNED`.

## Shadow evidence — the research family run on real history (`BADF-WP-0055`, Issue #101)

The completed `badf-research` P0 family (9/9 subskills, 26/26 controls) was `DESIGNED` but validated
only against synthetic examples. This WP produces the **`SHADOWED` admission evidence**: three
gate-valid research records over **real historical BADF cases**, framed blind, each exercising a
distinct part of the contract — `research-record-shadow-control15.json` (R02: the control-15
mistracking, baseline `e7ea929`, control-3 resolution), `research-record-shadow-composed-red.json`
(R03 root-cause: the composed-tree red at `30186c5`, hypothesis elimination), and
`research-record-shadow-ci-parity.json` (R10: `local-green ≠ CI-green`, a **FALSIFIED** claim with its
contradiction preserved — controls 21 + 8). The measurement (`references/shadow-evidence.md`): the
contract represented all three faithfully — derived confidence matched each basis, baselines resolved,
the falsification kept its contradiction, findings were grounded, sufficiency rested on synthesis —
**no contract gap surfaced under real conditions**. This is stronger than the synthetic examples
because the cases actually happened. `badf-research` stays `DESIGNED`; advancing it up the ladder
(`… → SHADOWED → APPROVED → ACTIVE`) is the operator's admission decision, now backed by shadow data.

## Router hardening — no unnamed hops (`BADF-WP-0056`, Issue #83)

The research router (`references/research-types.md`) left two routes ending in an **unnamed conceptual
hop**: R08 (EMPIRICAL_EXPERIMENT) → "experimental loop", R09 (STANDARDS) → "authoritative sources". A
route that ends unnamed cannot be followed deterministically — a pre-`ACTIVE` gap (#83). Now, with all
9 P0 subskills present, **R09 is named to existing subskills** (`framing → deep → fact-check →
synthesis`) and **R08 is pinned to the existing BADF experiment mechanism** (composed-tree gate +
mutation + `experiments[]`), with a dedicated `experimental-research` subskill **deferred to P1** —
*not* a tenth P0 subskill. The teeth are doc-structural, not a record control (the router is
documentation): `RouterDeterminismTests` refuses a reintroduced unnamed hop and asserts every route
token resolves to a registered subskill. Closes #83. `badf-research` stays `DESIGNED`.

## Architecture ASSURE substrate — `badf-architecture` VALIDATED (`BADF-WP-0057`, Issue #104)

WP-ARCH-C builds the read-only ASSURE side of the frozen `badf-architecture` contract: an
`architecture-assurance` record schema and an **`assure`** gate command enforcing controls 13–18.
Per ARCH-I11 the structural analysis (dependency graph, cycles) is the skill's read-only work — the
deterministic gate makes no network/exec call; it validates the record's integrity. The controls: an
assurance run **binds one baseline and one observed revision** (13, ARCH-I09); a `COMPLIANT`
conclusion **requires a baseline digest** — `NO BASELINE ≠ COMPLIANT` (14, ARCH-I07); an
`INDETERMINATE` ADR result **cannot serialise as a pass** (15); a drift finding **cannot self-classify
as approved evolution** — only independent authority may (16, ARCH-I08); the run **declares its
non-coverage** (17); and **every finding is assessed against the single bound baseline** (18,
ARCH-I01). The record is read-only — `implementation_authority` is schema-fixed `false` (ARCH-I12).
This meets the `VALIDATED` criterion, so **`badf-architecture` advances `IMPLEMENTED → VALIDATED`**
(the operator's stated expectation). `SHADOWED`/`APPROVED`/`ACTIVE` remain the operator's admission
decisions.

## badf-research finished — DESIGNED → ACTIVE (`BADF-WP-0058`, Issue #106)

The `badf-research` family was deliberately held at `DESIGNED` through every build WP while the
capability was assembled. With all prior ladder criteria met — **IMPLEMENTED** (9/9 subskills),
**VALIDATED** (26/26 controls, mutation-tested), **SHADOWED** (`BADF-WP-0055`, three real-history
shadow records, no gap) — and the operator's explicit approval ("finish badf-research"), the family
root is advanced **`DESIGNED → ACTIVE`**, the terminal admission status. The nine subskills remain
`IMPLEMENTED` — a two-tier model: the family status is the capability's admission gate, the subskill
status is implementation. Crucially, **activation grants no implementation authority**:
`implementation_authority` is schema-fixed `false` (RSR-I01), so an ACTIVE research family still only
produces evidence — a decision (`BADF-DEC-*`) and a work package (`BADF-WP-*`), authored by their own
authorities, remain between research and execution. This WP is governance-only (docs + registry
status; empty gate diff). `badf-architecture` sits at `VALIDATED`; `badf-research` is now the first
research capability to reach `ACTIVE`.

## ASSURE shadow calibration + a status-drift fix — VALIDATED → SHADOWED (`BADF-WP-0059`, Issue #108)

WP-ARCH-D does two things the operator's review surfaced. First, it **fixes a documentation-state
drift**: `badf-architecture`'s `acceptance.md` still called the capability `DESIGNED` (line 3) and said
it "stays `DESIGNED`" (line 48) while the registry, `SKILL.md`, and the same doc's middle said
`VALIDATED` — the claim-that-outlives-its-correction defect this repo keeps finding in itself; both
stale lines are corrected. Second, it **shadow-calibrates the ASSURE substrate** on real BADF
architecture cases spanning the outcome space: `COMPLIANT` (the stdlib-only boundary holds),
`NONCOMPLIANT` (the #57 PyYAML dependency drift — a true `UNAUTHORIZED_DRIFT` / `NONCONFORMANT` with a
MAJOR finding), and `INDETERMINATE` (an ADR not statically observable — which does *not* serialise as a
pass, ARCH-I07/control 15). Measurement (`references/assurance-shadow-evidence.md`): 1/1 true violation
detected, 0 false positives, INDETERMINATE handled without a false pass, no drift self-approved, every
run declares non-coverage — **no contract gap surfaced**. `badf-architecture` advances
`VALIDATED → SHADOWED`; `APPROVED`/`ACTIVE` remain the operator's admission decision.

## Gate 05 — security, privacy and AI safety (`BADF-WP-0060`, Issue #110)

The gate march reaches security: G05's four types (`threat-model`, `privacy-assessment`,
`supply-chain-plan`, `security-approval`) were declared but unenforced. Each now has a per-type rule
mapping to a G05 exit criterion. `threat-model` — every threat/abuse case carries a **mitigation** (an
uncontrolled threat is refused: *threats and abuse cases controlled*). `privacy-assessment` — every
data category carries a **lawful basis** and **handling** (*privacy obligations addressed*).
`supply-chain-plan` — **secret controls** are declared and every dependency carries a **control**
(*dependency and secret controls planned*). `security-approval` — a **human `security_authority`**
whose approval is **digest-bound to the threat-model** (a threat model edited after approval breaks
the binding) and names a **residual-risk owner** (*residual risk owned*). G05's minimum change class is
**C2**, so `examples/gate-dossier.G05.json` carries the four C2 authority roles — the first example
dossier above the C1 floor. Ships a **G04→G05** pair-acceptance (the full G00→G05 advance chain). Same
lean substrate as G01–G04.

## RSR-I06 — citation ≠ support (`BADF-WP-0061`, Issue #84 / GOV-0031)

`#84` recorded the last open research-contract design decision: a claim could be `VERIFIED` citing a
resolving, `PRIMARY`, digest-bound source whose content does not entail it, because the record had no
way to say whether semantic support was ever assessed. The resolution **freezes the boundary rather
than pretending entailment is deterministic**: RSR-I06 — `SOURCE_EXISTS != SOURCE_SUPPORTS_CLAIM`. The
gate verifies four states — a source **exists**, is **bound**, is **current** (control 6), and has been
**adjudicated** (control 21) — and stops there. Whether natural language entails a claim is
`fact-checking`'s judgment, recorded as evidence, never a policy-engine assertion.

Control 27 gives the boundary teeth without crossing it: a `VERIFIED` claim on cited support declares
`semantic_support` — `ASSESSED` (a `support_assessments` receipt with a non-empty `locator`, one per
supporting source) or `NON_COVERAGE` (the honest fallback). **Silence is refused**, and a receipt whose
own assessment does not substantiate the binding cannot back a `VERIFIED` claim. The receipt proves the
assessment *happened under contract*; it never asserts the sentence is true. `semantic_support` and
`support_assessments` are a *reading*, excluded from `evidence_digest` like findings/disposition — so
recording an assessment never invalidates the evidence digest. RSR-I06 grants no implementation
authority (RSR-I01 unchanged).

**Governance-closure defect (recorded, not hidden).** `#84` said the decision should be made *before*
`badf-research` reached `ACTIVE`; it was still open when `BADF-WP-0058` activated the family. This was
**not** a safety defect — control 21 had explicitly declared semantic entailment outside its coverage,
so no hidden control was ever claimed — but it was a governance-closure defect: the discovery was not
formally dispositioned before activation. Activation is **retained**; this WP formalizes the boundary
and closes GOV-0031. (Same doc-drift family as `#407` and the G-67 test-that-did-not-exist: the fix is
to make the document match the enforced reality. Here `acceptance.md` also stopped hard-coding a
`DESIGNED` status line that had drifted from the registry's `ACTIVE`.)

## experimental-research (`BADF-WP-0062`, Issue #113 / GOV-0032)

`R08` (`EMPIRICAL_EXPERIMENT`) was the one research type without a dedicated subskill or an integrity
control — it routed to the raw experiment mechanism and the gate never checked that an empirical run
ran an experiment. Two gaps, measured on `467406f`: an `R08` record with `experiments: []` was admitted
(measured nothing), and an experiment citing `hypothesis_ref: H-999` the record did not hold was
admitted (dangling reference). **experimental-research** is built as the 10th subskill (registered
`IMPLEMENTED`; the family `badf-research` stays `ACTIVE`), earning **control 28**: an `R08` record
carries at least one experiment, and every experiment — in any record — tests a hypothesis the record
holds. Mirror of controls 23/24 (type-specific structure, grounded in the record). The experiment
mechanism (method, result, reproduction under the composed-tree gate + mutation) is the evidence; the
gate checks the experiment is *real and bound*, not that the result is true — `D5` challenge is already
required. No new authority (RSR-I01); control 28 only refuses more, never approves more.

This is the **P1 gate lifted by operator request**, not by precedent: the deferred subskill was built
only once the operator selected the research track, and its control was earned by two failing-first
probes, not added because the P0 subskills each landed with one.

## badf-requirements — salvage over repair (`BADF-WP-0063`, Issue #115 / GOV-0033, supersedes PR #47)

PR #47 proposed a G02 requirements skill but duplicated the gate: a standalone
`scripts/badf_requirements.py` + a custom `requirements-rtm.schema.json`, re-using the already-occupied
`WP-2026-0028` / `BADF-DEM-0015` identities and a lockfile rewritten against ancient `main`. G02 was
**already solved** by `BADF-WP-0041` (PR #71), which enforces `requirements`/`nfr`/`traceability`/
`definition-of-ready` directly in the canonical gate and deliberately rejected a second validator. So
#47 is **superseded, not repaired**: closing it and rebasing would mean reconstructing it. The recovery
is **salvage over repair** — the same move `badf-prd` made with PR #44: keep the authoring layer, discard
the obsolete implementation.

`badf-requirements` is built fresh from current `main` as a top-level **authoring** skill (registered
`IMPLEMENTED`): it decomposes an approved PRD baseline into the four canonical G02 artifacts and
validates them with `badf_gate.py dossier` — **it has no validator of its own**. Its invariants run
`REQ-I01` (no gate authority) … `REQ-I06` (security provenance). The rich `OBJ→CAP→EPIC→REQ→NFR→AC→
TEST→EVDREQ` chain is preserved as the *authoring model*; the gate consumes only its lean canonical
subset (`OBJ←REQ→NFR`, `REQ↔AC`, human readiness), and `CAP`/`EPIC`/`TEST`/`EVDREQ` stay authoring
intermediates — first-class enforcement waits for a failing-first WP, not speculation. Test guards
lock the architecture: no `scripts/badf_requirements.py`, no custom RTM schema, `badf_gate.py` the sole
G02 authority. It adds **no gate code**, so there is no new control and nothing to mutate; the test
proves existence and the anti-duplication boundary. It lands `IMPLEMENTED` — `VALIDATED` is a separate
WP (cases: valid PRD → clean artifacts; orphan/qualitative → rework; a G05-born security requirement →
provenance preserved). **Separation: the skill authors, the gate verifies, an authority decides.**

## Validating an authoring skill (`BADF-WP-0064`, Issue #117 / GOV-0034)

`badf-requirements` advances `IMPLEMENTED → VALIDATED`. For a skill with no control of its own,
VALIDATED means the skill produces gate-correct outcomes on representative cases — the **canonical G02
gate is the fitness function**, run unchanged. Three cases (`tests/test_badf_requirements_validation.py`,
faithful-runner shape): **A** — a valid dossier renders `APPROVED`; **B** — the gate refuses exactly what
the skill's discipline warns against (an orphan requirement → `decomposes no objective`, REQ-I02; a
qualitative NFR → `is not quantified`, REQ-I04; an RTM orphan, REQ-I05) — "rework" is the gate refusing;
**C** — a security requirement introduced from a G05 concern passes carrying its provenance.

The honest line is drawn at Case C: the canonical G02 gate has **no** security-source (`SRC → REQ`)
field, so **REQ-I06 provenance is a skill-authoring discipline verified by inspection, not a gate
control**. Validation does not invent a control to make the case look enforced — it names the boundary
and files `SRC → REQ` as a candidate future failing-first WP. This WP adds **no gate code**: no new
control, nothing to mutate. It also stopped the SKILL.md hardcoding a status line (pointing to the
registry instead) — the same drift class fixed for the research `acceptance.md`. `SHADOWED`/`APPROVED`/
`ACTIVE` remain later admission decisions.

## Admitting badf-architecture ACTIVE (`BADF-WP-0065`, Issue #120 / GOV-0035)

`badf-architecture` advances `SHADOWED → ACTIVE`. This is an **admission decision** — the operator's, not
the loop's — recorded here and mirroring the research family's `BADF-WP-0058`: owner + security approval
given (single-collaborator repo, the owner is also the security reviewer), and the registry digest is
pinned. The shadow-calibration evidence (`references/assurance-shadow-evidence.md`, WP-ARCH-D) backs it:
ASSURE on real COMPLIANT / NONCOMPLIANT / INDETERMINATE cases — true violation detected, zero false
positives, INDETERMINATE handled without a false pass, no drift self-approved, no contract gap.

An admission advance changes **status, not the contract**: `badf_gate.py` and the G04/ASSURE schemas are
unchanged, the ARCH-I invariants hold at every status, and the capability grants **no** authority even
when `ACTIVE` (ARCH-I11 — the gate is the sole G04/ASSURE authority; there is no second validator). No
gate code, so no new control and nothing to mutate. Both capability families are now `ACTIVE`
(`badf-research`, `badf-architecture`). The WP also stopped the SKILL.md and acceptance.md hardcoding a
live status line — they point to `badf/skill-registry.json` — closing the same drift class fixed for the
research `acceptance.md` and `badf-requirements`.

## badf-git — Governed Trunk Git Model, contract freeze (`BADF-WP-0066`, Issue #123 / GOV-0045, supersedes PR #122)

The operator's *GTGM v0.1* design standardizes BADF Git on **one protected `main` ledger + short-lived
WP branches + one governed integration PR + deterministic composed-tree verification + squash
integration + immutable release evidence + explicit recovery** — an evolution of the live repo, which
already enforces squash-only, linear history, and composed-tree CI (`badf_compose.py`). An external
actor's **PR #122** attempted this exact freeze but was draft, CONFLICTING, and re-used three consumed
identities (`BADF-DEM-0052`, `WP-2026-0064`, `WP-2026-0065`). **Salvage over repair** again: `badf-git`
is built fresh from current `main` (this WP), re-homing #122's genuine authoring content onto a clean
WP with fresh ids — the collided-id examples fixed, and #122's temporary lockfile-probe scaffolding test
dropped (kept the real contract checks).

`badf-git` is a top-level **declarative** capability, registered `DESIGNED`: a router and constraint
layer, **not** a Git authority, merge bot, release authority, or second gate. Its invariants run
`GIT-I01` (no Git authority) … `GIT-I12` (no second gate/mutation engine); `SKILL.md` + eight reference
contracts freeze the GTGM cycle, the state machine, the `GIT-O0…O5` operation classes, the composition
invariant (`SOURCE_HEAD_GREEN != INTEGRATION_SAFE`), and the recovery/release contracts (repair forward
via revert/reflog; immutable tags). **No `scripts/badf_git.py`, no new schema, no Git authority** —
`badf_gate.py` and the platform rules remain the sole authorities, `badf_compose.py` the canonical
composition. No gate code, so no new control and nothing to mutate; the test guards the declarative
surface. Contract Freeze is deliberately first (WP-GIT-B…J deferred): an incorrect mutation model would
spread into every future BADF autonomous engineering loop.

## Gate 06 — implementation planning (`BADF-WP-0067`, Issue #125 / GOV-0046)

The gate march reaches planning: G06's four types (`work-breakdown`, `test-plan`, `release-plan`,
`rollback-plan`) were declared but unenforced. Each now has a per-type rule mapping to a G06 exit
criterion. `work-breakdown` — non-empty tasks, each bounded (a description), with a resolvable **and
acyclic** dependency graph (an empty, dangling-dependency, or cyclic breakdown is refused: *work
packages bounded* + *composition order defined*). `test-plan` — non-empty planned tests, each naming
what it `verifies` (*tests planned first*). `release-plan` — non-empty `environments` and concrete
`steps` (*environments and resources ready*). `rollback-plan` — an executable `method` + `steps` +
non-empty `stop_conditions` (*rollback and stop conditions executable*). G06's minimum change class is
**C1**, so `examples/gate-dossier.G06.json` carries the two base authority roles (engineering_owner +
independent_reviewer). Ships a **G05→G06** pair-acceptance (the full G00→G06 advance chain). Same lean
substrate as G01–G05 — no new module. Shipped through the operator's `/loop` self-paced gate march.

## badf-solution-design — composition contract freeze (`BADF-WP-0068` / WP-SOL-A, Issue #128 / GOV-0047)

BADF had specialist *design* surfaces (G03 UX, G04 architecture/data/API) but nothing that **composed**
their detailed contracts into one coherent solution — five individually-valid designs can compose a broken
one (UX asserts an action authorization denies; an API with no data state behind it; a failure conveyed
only by color). `badf-solution-design` is that composition/orchestration layer, registered `DESIGNED`: a
**thin router + constraint contract**, not a sixth architecture skill, a new gate, a second validator, or
a document mega-skill. `badf-architecture` (ACTIVE) stays the structural spine and G04 authority;
solution-design **details** interfaces and raises `ARCHITECTURE_CHANGE_REQUIRED` rather than inventing a
boundary (SOL-I02).

`SKILL.md` + eleven references freeze the `FRAME→…→PACKAGE` workflow, the `SOL-I01…I12` cross-artifact
invariants (requirement provenance; UX↔API; API↔authorization; **default-deny SOL-I05 `NO MATCH = DENY`**;
authorization↔audit; API↔data; UX↔error; accessibility-binds-behavior; migration safety; API compatibility;
**SOL-I12 no second gate**), the solution-composition matrix (the detailed-design RTM), the
`authorization-design` framing (principal·resource·action·scope·… with RBAC as one model), and the API
DESIGN/ASSURE split. **No `scripts/badf_solution_design.py`, no new schema, no `lifecycle.json` change** —
it composes into the **existing** G03/G04 evidence; `badf_gate.py` stays the sole gate authority. Adds no
gate code, so no new control and nothing to mutate; the test guards the declarative surface. Specialist
adapters, composition schemas and seam controls are deferred to WP-SOL-B…D. Built in an isolated
`git worktree` alongside BARCHI-2's parallel badf-git work (GIT-B/GIT-C), per GIT-I04.

## badf-solution-design → IMPLEMENTED — the composition matrix (`BADF-WP-0071` / WP-SOL-B, Issue #131 / GOV-0050)

WP-SOL-A froze the composition contract as prose; WP-SOL-B gives its central artifact — the
**solution-composition matrix** (the detailed-design equivalent of the G02 RTM) — a machine shape and a
structural validator, advancing `badf-solution-design` `DESIGNED → IMPLEMENTED`. `schemas/solution-
composition.schema.json` binds one row per requirement (`solution_id`, `requirement_ref`, and the
specialist ref arrays), and a **`solution` command in the one canonical `badf_gate.py`** validates it —
**not** a second validator script (SOL-I12 honored; it mirrors `research`/`assure` and declares no
lifecycle result). Structural controls, each earned failing-first + mutation-killed: **SOL-C01** unique
`solution_id`s; **SOL-C03** every row binds ≥1 specialist artifact (a requirement composed to nothing
satisfies nothing); plus a no-empty-matrix guard (the gate walker ignores `minItems`). **SOL-C02**
(requirement provenance) was *not* added as a code branch — the schema's `required` + `^REQ-` pattern
enforces it, so a code check would be dead; recorded as "earned by the schema, not by precedent".

The **cross-artifact SEAM controls** (SOL-I01…I12 reconciled *against* the specialist artifacts) are
deferred to **WP-SOL-C** (`VALIDATED`). No `lifecycle.json` change — the matrix is a standalone record
like research/assure, not a G03/G04 required_evidence type. Built in an isolated `git worktree` parallel
to BARCHI-2's badf-git GIT-B/GIT-C; reconcile done at land time against the current LANDED_UNRECONCILED WP.

## badf-git GIT-B — the identity contract (`BADF-WP-0070`, Issue #129 / GOV-0049)

GIT-A froze the contract and deferred branch-name enforcement "until BADF freezes one machine
WP-ID form". Measured on `8673d9a`, the identity surface was split three ways: the machine id was
*de facto* `WP-2026-NNNN` (53/53 `work/` dirs, the ledger glob, the normalizer, id allocation) but
the year was a hardcoded literal in three separate regex copies; the display label `BADF-WP-NNNN`
carried 40/40 squash subjects and 12/12 PR titles while trailers were mixed (33 display / 7 machine)
and the PR template asked for the display form in the machine trailer; merged PR heads came from
`wp/` (48), `feat/` (8), `fix/` (2), `chore/` (2), `gov/` (1), and this document prescribed
the display-label branch form (`wp/` + `BADF-WP-NNNN`) against the frozen contract's `wp/WP-2026-NNNN-<slug>`. The existing
control accepted either trailer and checked neither title nor branch — three names, one green run.

**One identity, three faces, one binding.** Machine id `WP-2026-NNNN`, where `WP-2026-` is a fixed
ledger namespace constant (the ledger's genesis namespace, *not* a calendar field — no rollover;
NNNN continues monotonically), defined **once** in `badf_gate.py` (`WP_NAMESPACE`) and imported by
`badf_compose.py` and `check_pr_traceability.py`. Display label `BADF-WP-NNNN` in the PR title /
squash subject only. Branch `wp/WP-2026-NNNN-<slug>`. The binding is the body trailer
`Work-Package: WP-2026-NNNN`; the display form there is refused with the exact line to paste.
`check_pr_traceability.py` now takes `--title` and `--head-ref` as **required** arguments (CI passes
them from the `pull_request` event) and refuses any PR whose title, branch or trailer disagree on
NNNN — absence of an argument is a usage error, never a silent skip. History is not rewritten
(GIT-I06): `ledger_landings` still resolves every historical display-form trailer; only new PRs bind
canonically. Calendar-year rollover was considered and rejected — a namespace constant is the
smallest change that removes the drift. The PR that shipped this was its own first subject on the
runner. GIT-C (the read-only baseline inspector, #127) follows in design order.

## badf-solution-design → VALIDATED — matrix-internal seams (`BADF-WP-0072` / WP-SOL-C, Issue #135 / GOV-0051)

WP-SOL-B made the composition matrix structurally sound; WP-SOL-C enforces the **cross-concern coherence**
the skill exists for, at the level the matrix alone can decide — advancing `badf-solution-design`
`IMPLEMENTED → VALIDATED`. The refund example the contract warns about (an API op with no authorization,
an authorization with no audit, a UX interaction with no accessibility) now **fails** the `solution`
command. Three matrix-internal seam controls, each earned failing-first + mutation-killed: **SOL-C04**
(SOL-I04) a row with `api_refs` carries `authorization_refs`; **SOL-C05** (SOL-I06) a row with
`authorization_refs` carries `audit_refs`; **SOL-C06** (SOL-I09) a row with `ux_refs` carries
`accessibility_refs`. Co-occurrence, not blanket — a data-only row needs no authorization.

The honest line: the **external-artifact** seams (SOL-I02 architecture baseline, SOL-I05 default-deny,
SOL-I07 API↔data, SOL-I10/I11 migration/API-compat) and the *semantic* resolution of every ref against
its specialist artifact **cannot** be enforced until the specialist adapters exist — deferred to those
WPs, not faked. Still one canonical gate (SOL-I12), no `lifecycle.json` change. Shipped through the
operator's `/loop` driving badf-solution-design toward ACTIVE; built in an isolated worktree, landing as
the second seat after BARCHI-2's badf-git GIT-B (#134) and reconciling `WP-2026-0070`.

## badf-git GIT-C — the read-only baseline inspector (`BADF-WP-0069`, Issue #127 / GOV-0048)

badf-git's BASELINE stage requires an agent to *observe before editing* and to leave the stage only
when "a reproducible baseline exists" — yet nothing produced that record deterministically:
`badf_gate.py` resolved an authority baseline and read revisions but had no working-tree, index or
worktree observation at all, BADF's own G07 dossiers bind `source_revision: HEAD` symbolically, and
this session found two agents in one working tree with no record of that state. `GIT_BASELINED`
was a sentence an agent typed.

**A baseline is measured, not typed.** `python3 scripts/badf_gate.py git-baseline [<path>]` prints
one JSON git-baseline record — repository identity; worktree path, `branch`/`detached`, linked
worktree; index and worktree status as **counts only** (never a path, never content); target ref +
SHA + tree as known locally; source ref + HEAD SHA + tree; merge base, ahead/behind, ancestry;
remote freshness stated honestly (`observed_without_fetch: true`); `policy_epoch` — and a PASS line.
It is `GIT-O0 OBSERVE`: writes nothing, fetches nothing, moves nothing (proven by a test that
snapshots status, reflog, stash, index and the file list before and after). It refuses, `BLOCKED`,
outside a git tree, when `origin/<default>` does not resolve (no fallback to HEAD — the monotonic
resolver's rule), and on an unborn HEAD. The contract's test-set epoch does not exist in BADF and is
declared as non-coverage rather than invented. The `repository-state` subskill routes to it and is
registered `IMPLEMENTED` (C1, no tools of its own); the `badf-git` root stays `DESIGNED`. A CI step
runs the inspector on the runner's own checkout — detached at `refs/pull/N/merge` on a pull request —
as the positive control on real infrastructure. Composition identity is GIT-E; branch conformance
is GIT-B's check; platform state is GIT-F.

## Discovery ≠ scope expansion

Work on `BADF-WP-A` that finds problem B opens an Issue for B (`status: DISCOVERED`,
`discovered-by: BADF-WP-A`) and does **not** fix B in A's branch. This is `AGENTS.md`'s
"no silent scope expansion", given a mechanism.

## Not adopted

No permanent `develop` branch. Trunk-oriented: `main` ← PR ← short-lived authorized branch.
