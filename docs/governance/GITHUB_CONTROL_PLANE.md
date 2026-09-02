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

## badf-git GIT-D — staleness as a measured verdict (`BADF-WP-0075`, Issue #140 / GOV-0054)

The state machine names the events that make evidence stale — source head moved, target moved,
a rewrite, an epoch change — and says recovery is *recomputation, not waiver-by-label*; the
evidence contract defines the rewrite record. Nothing detected any of it: in this program's last
two work packages the self-dossier was twice bound to a stale base after a rebase, caught once
because compose refused a 154 KB misbinding and once by hand. GIT-C produced the record; nothing
consumed it.

**`python3 scripts/badf_gate.py git-staleness <baseline-record.json> [<path>]`** loads a git-baseline
record (tolerating the trailing PASS line a stdout redirect captures), re-observes the tree through
`git_baseline()`, and renders `CURRENT` (exit 0), `SOURCE_ADVANCED` (the recorded head is an ancestor
of the new one; HELD 3), `STALE_EVIDENCE` (the recorded head is **not** an ancestor — amend, rebase,
reset, cherry-pick — or the policy epoch changed; HELD 3, carrying `old_source_head`,
`new_source_head`, `kind: history_rewrite`, `old_head_still_reachable`, `invalidated`), or
`TARGET_MOVED` (HELD 3). Combined cases report every flag and the strictest disposition; index and
worktree count deltas are informational — a dirty tree is not a rewrite. The rewrite *type* is not
inferable from two revisions and is not guessed. It refuses, `BLOCKED`, a file that is not a complete
git-baseline record and a record taken in another checkout — a baseline binds a checkout. Read-only,
deterministic modulo `observed_at`. The `commit-integrity` subskill carries the nested loop's
discipline (`git add -p`, inspect the staged diff, atomic commits) and the rule that closes it: bind a
baseline before verification, judge it before publishing or opening a PR, recompute on a rewrite. CI
stores the runner's own baseline and checks it (`CURRENT`) every run. Composition identity is GIT-E;
approval staleness is GIT-F.
## badf-solution-design → SHADOWED — representative calibration (`BADF-WP-0074` / WP-SOL-D, Issue #141 / GOV-0053)

`SHADOWED` is the rung before `APPROVED`/`ACTIVE`, and it means *the controls were run against
cases and behaved*. `badf-research` and `badf-architecture` shadowed on **real** historical BADF
records; `badf-solution-design` has **no real project compositions yet** — BADF is a governance
framework with no UX/API/authorization surface of its own to compose. So this shadow is
**REPRESENTATIVE**, and the evidence (`references/shadow-evidence.md`) says so in its first
sentence: a real re-shadow is owed the first time a project actually uses the skill, and the
operator may hold `APPROVED`/`ACTIVE` until then.

The calibration ran the `solution` command over representative matrices: **all seven defect classes
refused** (empty matrix, duplicate id, a row binding no artifact, malformed `requirement_ref`,
api-without-authz SOL-C04, authz-without-audit SOL-C05, ux-without-a11y SOL-C06); **zero false
positives** on three clean compositions — including the reporting matrix's **data-only row**, the
false-positive check that proves the seams are *co-occurrence, not blanket* (a row with no
`api_refs` correctly needs no `authorization_refs`). And it **declares its non-coverage**: the
external-artifact seams (SOL-I02/05/07/10/11) and the *semantic* resolution of each ref against its
specialist artifact are not exercised — they need adapters that do not exist. Silence is not
coverage; the gaps are named, not implied to pass. Two committed shadow matrices
(`examples/solution-composition-shadow-refund.json`, `-reporting.json`) are validated in CI. No
`lifecycle.json` change, no new control (the controls are WP-SOL-B/C), no second validator. Registry
`VALIDATED → SHADOWED`; `APPROVED`/`ACTIVE` remains the operator's admission decision.

## badf-solution-design → ACTIVE — operator admission on a representative shadow (`BADF-WP-0077` / WP-SOL-E, Issue #146 / GOV-0056)

`SHADOWED → ACTIVE` is a **human admission gate** — self-approval is prohibited, so no agent crosses
it. The operator made the admission decision (2026-08-30): **activate now, accepting the
representative shadow**, rather than hold `ACTIVE` indefinitely for a real-project composition that
BADF — a governance framework with no product surface — may not produce soon. This WP records that
decision as a governed registry advance, mirroring `badf-research` (WP-0058) and `badf-architecture`
(WP-0065): `ACTIVE` **grants the skill no new authority** (SOL-I12 — the one canonical
`badf_gate.py solution` stays the sole composition authority; `badf_gate.py` and the platform rules
remain the authorities), and there is no `lifecycle.json` change, no new control, no second validator.

The admission does **not erase the caveat**: `references/shadow-evidence.md` still labels the shadow
representative, and the owed real-project re-shadow is filed as a tracked follow-up
(**#145**, `DISCOVERED`, trigger = the first real project composition). So the ladder stays truthful —
the capability is admitted for use, its trust is honestly bounded to a representative shadow, and the
debt to re-shadow on real data is tracked rather than lost. Registry `SHADOWED → ACTIVE`.

## badf-git GIT-E — the composition claim (`BADF-WP-0076`, Issue #144 / GOV-0055)

`SOURCE_HEAD_GREEN != INTEGRATION_SAFE` is badf-git's core invariant and its contract binds a
nine-field composition identity — yet `badf_compose.py` computed all of it on every PR (`base X +
candidate Y -> composed Z (tree T)`) and recorded none of it; three rebases across GIT-B/C/D each
silently invalidated composition. The obvious record — commit the tuple inside the PR — is
circular: the commit that adds it moves the head and the result tree. BADF had already solved that
once, in the self-dossier, by binding **content** with `work/<WP>/` and the lockfile excluded.

**`badf_compose.py --record <path>`** writes a `git-composition` record after composing; its binding
is **`expected_content_tree`** — the composed tree with `work/<WP>/` and `badf/lockfile.json` removed,
computed on a temporary index — which is what lets the record, the self-dossier and the lockfile live
inside the PR they verify. Committed as `work/<WP>/evidence/G07/composition-record.json`, it is
found by compose on the tree that would land — in CI and locally — and **refused** when the
recorded base is not the base being composed onto ("stale … recompute with `--record`": the rebase
failure mode, made a refusal), when the recomputed content tree differs (content changed after the
claim), when the method is not squash, the target is foreign, the work package differs, or the record
is malformed. No record prints `composition: no record` and passes as before — requiring one is a
later policy decision. The self-dossier indexes the record as `composition` evidence when present
(digest-bound; HUMAN_REQUIRED dossiers skip per-type rules, which is why compose is the enforcement
point). The `composition-verification` subskill carries the author's order of operations —
*commit content → `--record` → `self-dossier` → commit → push* — and the rule that a rebase or a
content change recomputes the record, never edits it. This work package's own PR carried its record
and CI verified it. Approval staleness and the expected-head merge guard are GIT-F; the landed-tree
comparison after merge is GIT-F/G.
## badf-security-design — G05 security-design contract freeze (`BADF-WP-0078` / WP-SEC-A, Issue #149 / GOV-0058)

BADF had G05 evidence types (`threat-model`, `privacy-assessment`, `supply-chain-plan`,
`security-approval`) but no capability to author them coherently. `badf-security-design` is that
capability, frozen `DESIGNED`: a thin **pre-implementation** composition/router that consumes the
architecture and solution baselines, models how the intended system can be abused, derives controls
and security requirements, and **normalizes** its specialists into the three G05 **design** artifacts.
The fourth, `security-approval`, is **never authored by the skill** — it is `security_authority`'s,
referencing exact digests (SEC-I13). SKILL.md + 14 references + `SEC-I01…SEC-I15`.

Three boundaries carry the design: **(1) design ≠ assurance** — code review / SAST / SCA / secrets /
IaC / API-review / remediation are security *assurance* and belong to a future `badf-security-assurance`
at G08/G09; absence of a design finding never establishes implementation security (SEC-I14). **(2)
consume, don't rediscover** — architecture owns boundaries (a missing one raises
`ARCHITECTURE_CHANGE_REQUIRED`, not an invented boundary, SEC-I05) and solution-design owns the
functional IAM/API/data contracts (security-design *secures and challenges* them — least privilege,
bypass resistance, isolation — it does not fork a second IAM model, SEC-I06); a derived security
requirement that changes scope raises `REQUIREMENT_CHANGE_REQUIRED` rather than silently rewriting G02
(SEC-I04). **(3) OWASP is ADAPT, not authority** — the Secure Agent Playbook and AppSec Agent are
adapted for procedural decomposition, CWE/ASVS/OWASP/OpenCRE traceability, structured findings and
agent/API taxonomies; their agent output, lifecycle and scanner results are **never** BADF gate
authority (`OWASP agent says PASS → G05 PASS` must never happen). `ai-agent-security-design` is
conditional (`NOT_APPLICABLE_WITH_REASON` for non-agentic work), first-class for BADF itself, and rests
on `CAPABILITY ≠ AUTHORITY`. No `scripts/badf_security_design.py`, no schema, no `lifecycle.json`
change, no gate-code, no specialist activated. Ladder WP-SEC-A…E mirrors solution-design; the deferred
`badf-security-assurance` is named, not built.

## badf-git GIT-F — `MERGED != VERIFIED` (`BADF-WP-0079`, Issue #151 / GOV-0059)

The cycle ends AUTHORIZE → SQUASH → RECONCILE, and the contract says to verify the actual landed
result against the expected composition — "`MERGED` is not synonymous with `VERIFIED`". Measured
after GIT-E: the expected-head guard was practised by hand (every merge in this program bound the
reviewed head SHA through the REST endpoint), and `reconcile` recorded only `landed_as` — it compared
nothing about the landed content. That left exactly one window the head guard cannot close: `main`
moving between the last CI run and the merge — hit twice in one day — in which GitHub squashes onto a
newer base and the landed tree is not the tree that was verified.

**`badf_gate.py reconcile <WP>` now verifies the landing.** It reads the composition record from the
**landed commit's tree** (never the checkout), computes the landed content tree from the object store
alone, and refuses — `BLOCKED: … main moved between verification and merge; open recovery` — when it
differs from the record's `expected_content_tree`; on a match it writes `landed_content_tree` and
`composition_verified: true` beside `landed_as`. No record → `composition_verified: false`, honest and
visible; a malformed record is refused, never downgraded. Running this check by hand on the first real
landing (GIT-E, `5aaeb62`) found a **defect in GIT-E's `content_tree`**: `git rm --cached` refuses a
path whose worktree file differs from the index and the helper silently returned the *full* tree — it
had only ever run inside compose's fresh scratch, where the worktree always matches. `content_tree`
now lives once, in `badf_gate.py`, object-store-only (`read-tree` + `update-index --force-remove` +
`write-tree` on a temporary index), guarded by a test that computes it on a checkout whose worktree
sits at a different commit; `badf_compose.py` imports it. Recomputed that way, the landed content of
`5aaeb62` equals the record: the first landing verified end to end. The `pull-request-integration`
subskill carries the AUTHORIZE checklist as a `gh`-driven procedure, the head-bound squash call, and
the rule that the next branch's reconcile is the verification. Approval-freshness enforcement and
merge queues stay outside (single collaborator; C-1 open and recorded); recovery automation is GIT-G;
releases are GIT-H.

## badf-git GIT-G — preservation and classification, measured (`BADF-WP-0080`, Issue #153 / GOV-0060)

The recovery contract opens with `PRESERVE → IDENTIFY → CLASSIFY → RECOVER → VERIFY → RECONCILE`, stops
mutation until unknown state is classified, and `GIT-O5` requires an inventory and a preservation of
unique state before any exception. Nothing produced either; GIT-F's `BLOCKED` reconcile ended at the
words "open recovery"; this program's own preservation was a hand-typed `git branch backup/…` before
every rebase, and the integrity-test residue that blocked a rebase was unclassified unique state met
with a hand-run `git checkout --`.

**`python3 scripts/badf_gate.py git-recovery [<path>]`** renders the before-state record the contract
requires: the git-baseline plus the **unique-state inventory** — uncommitted changes (a count), stash
entries, **dangling commits** (reflog entries of HEAD reachable from no ref), **unpushed commits** per
local branch, **other worktrees** of the same repository with the branch each holds — and derives the
**recovery class** (`EVIDENCE_ONLY` / `LOCAL` / `TOPIC` / `PROTECTED`) and the **disposition**
(`RECOVERABLE`, or `RECOVERY_REQUIRED` — HELD — when unique state must be preserved first), printing
the least-destructive path. Unmerged paths are `BLOCKED`: classification is impossible until conflicts
are resolved, and the tool never cleans around them. **`--preserve <label> --wp <WP>`** establishes
preservation the only way that cannot lose anything: `refs/recovery/<WP>/<label>` at HEAD and, for a
dirty tree, a `-worktree` ref at a `git stash create` snapshot — objects are written, nothing else
moves, and an existing label is never overwritten. The tool never runs `reset`, `clean`, `checkout`,
`push`, a branch/worktree deletion or a ref deletion. The revert pattern for landed work — including the
`BLOCKED`-reconcile path GIT-F introduced — stays a procedure in the `git-recovery` subskill: a **new
recovery work package** with `git revert`, composed against current `main`, head-bound squash,
post-merge reconcile; `main` is never rewritten. The runner renders its own record every run
(`EVIDENCE_ONLY` on a clean, detached checkout). Release-ref recovery is GIT-H.

## badf-git GIT-H — a release ref is a checked binding (`BADF-WP-0081`, Issue #155 / GOV-0061)

The release contract says `TAG_EXISTS != RELEASE_AUTHORIZED`, that release refs are created only
from `main` and are immutable, and that the version comes from an explicit record — never a branch
name, a PR title, a commit prefix, or a tag anyone can create. Measured after GIT-G: one release-class
ref existed, the annotated, **unsigned** `BADF-BASELINE-1.0.0` → `3f6119b`, which every G00–G02
example evidence file names as its `source_revision`; no `vX.Y.Z`, no GitHub release, no version
source of truth, no tag ruleset, and **no tag logic in the gate** — a moved baseline tag would have
silently re-governed every example.

**`badf_gate.py git-release-check <tag>`** (read-only) refuses a missing or lightweight tag, a tag off
`main`'s first-parent history, a tag with no release record (`TAG_EXISTS != RELEASE_AUTHORIZED`), a
record for a different revision (the tag *moved*), a version or result tree that differs, and a
provenance statement the tag object contradicts — else `RELEASE_BOUND`. **`git-release-record
<version>`** writes `badf/releases/<version>.json` — the contract's release binding — as a
`HUMAN_REQUIRED` request: it binds an existing tag's own commit or, absent a tag, HEAD; only
first-parent commits of `main` qualify; version reuse against different content is refused; **it
never runs `git tag`** — the release authority creates the tag, then the check proves the pair. `repo`
gains `verify_release_refs`: every recorded release ref that exists locally must still point at its
recorded revision (an absent tag is tolerated — a shallow clone is not a breach); `badf/releases/` is
lockfile-covered. The historical baseline is recorded through the tool with its provenance limitation
stated (annotated, unsigned), not rewritten. The `release-versioning` subskill carries the SemVer
decision as the release authority's checklist and the record → tag → check sequence. Whether BADF cuts
its first `vX.Y.Z` is a release-authority decision this WP enables and does not take. The runner
checks the baseline every run. Signing, tag rulesets, SBOM/attestation are the platform's and
G10–G13's.

## badf-security-design → IMPLEMENTED — the security-composition matrix (`BADF-WP-0083` / WP-SEC-B, Issue #158 / GOV-0063)

WP-SEC-A froze the contract as prose; WP-SEC-B gives its central artifact — the **security-composition
matrix**, the security-design equivalent of the RTM — a schema and structural validation in the one
canonical gate (`badf_gate.py security`), mirroring `solution`. Each `threats[]` row binds a
`security_id`, a `source` provenance object, a `disposition`
(`controlled|deferred|blocked|pending-authority`), and optional control / security-requirement /
verification refs. Four controls, each mutation-killed: a non-empty matrix; **SEC-C01** unique
`security_id`; **SEC-C02** every threat resolves to ≥1 provenance source (SEC-I02 — a threat that
resolves to nothing is not a threat); **SEC-C03** a `controlled` threat carries ≥1 `control_refs`
(SEC-I03 — controlled by nothing is not controlled). One structural check is bought by the schema
alone: `residual_risk`'s enum offers `ACCEPTED-PENDING-AUTHORITY` but **no bare `ACCEPTED`**, so
**SEC-I12 is enforced by construction** — the skill has no value with which to self-accept residual
risk. This is one record in the canonical gate, **not** a second validator (SEC-I15) and not a
lifecycle result; `lifecycle.json` is unchanged. The cross-artifact **seams** — SEC-I04 bidirectional
traceability, SEC-I01 exact-baseline binding, and the semantic resolution of every ref against the
architecture/solution artifacts — are **deferred to WP-SEC-C** (failing-first), exactly as the solution
seams were deferred from WP-SOL-B to WP-SOL-C. Registry `DESIGNED → IMPLEMENTED`.
## badf-security-design → VALIDATED — the matrix-internal seams (`BADF-WP-0084` / WP-SEC-C, Issue #162 / GOV-0065)

WP-SEC-B enforced the structural controls; WP-SEC-C enforces the **cross-artifact seams** the matrix can
decide alone, mirroring WP-SOL-C. Two controls, each mutation-killed: **SEC-C04** (SEC-I04, downstream
traceability) — a `controlled` threat carries ≥1 `verification_refs`, because a control that is asserted
but never verified is an incomplete chain; a security conclusion traces *downstream* to a verification
obligation. **SEC-C05** (SEC-I12 / SEC-I03, disposition ↔ residual-risk coherence) — `residual_risk =
ACCEPTED-PENDING-AUTHORITY` requires `disposition = pending-authority`, so a threat cannot claim its
residual risk is pending authority-acceptance unless it was actually dispositioned to authority. Both are
disposition-scoped and one-directional by design (a `deferred`/`blocked` threat needs no verification; a
`pending-authority` threat need not have declared its residual risk yet). The **external-artifact** seams
— the FULL SEC-I04 bidirectional traceability against a real sec-req registry, SEC-I01 exact-baseline
digest binding, and the semantic resolution of every ref against the architecture/solution artifacts —
stay **deferred**, honestly, until those artifacts exist. No new invariant, no `lifecycle.json` change, no
second validator (SEC-I15). Registry `IMPLEMENTED → VALIDATED`.

## badf-security-design → SHADOWED — representative calibration (`BADF-WP-0085` / WP-SEC-D, Issue #164 / GOV-0066)

`SHADOWED` means the controls were run against cases and behaved. `badf-research` and `badf-architecture`
shadowed on **real** BADF history; `badf-security-design` — like `badf-solution-design` before it — has
**no real security-composition matrices yet** (BADF has no UX/API/authorization/threat surface of its own
to model), so the shadow is **REPRESENTATIVE**, and the evidence (`references/shadow-evidence.md`) says so
in its first section: a real re-shadow is owed the first time a project actually uses the skill. The
calibration ran the `security` command over representative matrices: **all seven defect classes refused**
(empty · duplicate id · no-provenance · controlled-no-control · controlled-no-verification ·
residual-incoherence · bare-`ACCEPTED`); **zero false positives** on three clean matrices — including the
data/privacy matrix's **`deferred`** row, the false-positive check that proves SEC-C03/C04 are
disposition-scoped (a threat not yet controlled needs neither a control nor a verification) and SEC-C05 is
one-directional. And it **declares its non-coverage**: the external-artifact seams (full SEC-I04
bidirectional against a real sec-req registry, SEC-I01 exact-baseline digest binding, and the semantic
resolution of every ref) are not exercised — they need adapters that do not exist. Two committed shadow
matrices (`examples/security-composition-shadow-api.json`, `-data.json`) are validated in CI. No
`lifecycle.json` change, no new control, no second validator. Registry `VALIDATED → SHADOWED`;
`APPROVED`/`ACTIVE` remain the operator's admission decision.

## badf-security-design → ACTIVE — operator admission on a representative shadow (`BADF-WP-0086` / WP-SEC-E, Issue #167 / GOV-0067)

`SHADOWED → ACTIVE` is a **human admission gate** — self-approval is prohibited, so no agent crosses it.
The operator's standing directive — `/loop … proceed next steps until badf-security-design is active`
(2026-08-30) — is the admission decision to **activate on the representative shadow**, rather than hold
`ACTIVE` indefinitely for a real security-composition matrix that BADF — a governance framework with no
threat surface of its own — may not produce soon. This WP records that decision as a governed registry
advance, mirroring `badf-solution-design` WP-SOL-E: `ACTIVE` **grants the skill no new authority**
(SEC-I15 — `badf_gate.py` stays the sole gate authority; SEC-I13 — `security-approval` stays
`security_authority`'s), and there is no `lifecycle.json` change, no new control, no second validator.

The admission does **not erase the caveat**: `references/shadow-evidence.md` still labels the shadow
representative, and the owed real-project re-shadow is filed as a tracked follow-up (**#166**,
`DISCOVERED`, trigger = the first real security-composition matrix). So the ladder stays truthful — the
capability is admitted for use, its trust honestly bounded to a representative shadow, the debt to
re-shadow on real data tracked rather than lost. This **completes the WP-SEC-A…E ladder**
(`DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED → ACTIVE`), the second capability after
`badf-solution-design` to traverse it end to end. Registry `SHADOWED → ACTIVE`.

## badf-git GIT-I — shadow calibration on the program's own history (`BADF-WP-0082`, Issue #157 / GOV-0062)

`SHADOWED` means the controls were run against real cases and behaved. `badf-git` is unusual: **it ran
on itself** — every work package GIT-B…H was integrated through the tools it was building, rebased
under a moving `main` five times, its composition claims refused as stale and recomputed three times,
its landings verified four times by the reconcile it introduced. That history is the shadow corpus,
recorded once in `examples/git-shadow-evidence.json` and **recomputed from the object store on every
run** by `tests/test_badf_git_shadow.py` with the real tools: 4/4 record-bearing landings' content
trees equal their claims; 11/11 pre-record landings read `composition_verified: false` — honestly;
14/14 recent first-parent landings conform to GIT-B's identity rule; a baseline at the GIT-F landing
judged at the GIT-G landing renders `SOURCE_ADVANCED` through `git_staleness`; the baseline tag renders
`RELEASE_BOUND` through `git_release_check`; four CI runs are cited for the detached-runner inspectors.
A tampered record — a wrong tree, a wrong verdict, a case that cannot be recomputed offline — is refused
by the tests, so the record cannot drift from history. **Non-coverage is named, not implied:** rewrite
verdicts (`STALE_EVIDENCE`) were exercised only synthetically — the rewritten heads were force-pushed
away; the recovery inventory on real dirty state was observed, not committed; branch-name conformance
of landed heads was API-observed; no signed tag exists. **Result: no contract gap surfaced under real
conditions.** The root stays `DESIGNED` — a declarative router whose implementation is its six
`IMPLEMENTED` subskills and their suites; advancing the family is the operator's admission decision
(GIT-J), the `badf-research` precedent. No registry status change, no lifecycle change, no new
control, no new tool.

The measurement note is `skills/badf-git/evidence/shadow-evidence.md` — deliberately **outside** the
frozen `references/` contract surface (`test_contract_surface_is_declarative_only` keeps its eight
files; evidence is not contract). The calibration surfaced one harness limitation, not a contract gap:
the composed world judges a candidate with the *base's* `tests/`, so a PR that changes a guard cannot
be green inside `test_badf_git_composition` — filed as #160 (GOV-0064).

## badf-git → ACTIVE — GIT-J admission (`BADF-WP-0087`, Issue #169 / GOV-0069)

`badf-git` is admitted `DESIGNED → ACTIVE` by **registry status flip only**: `digest`
`sha256:17ea1e41…` is the freeze value and `SKILL.md` is untouched, so the contract admitted is the
contract frozen at GIT-A. The authorization is the operator's decision recorded on #169
(comment 5467417478) — rung 6 `APPROVED` of `docs/07`, owner approval proportional to a family that
holds **no tools** (`allowed_tools: []`) and grants **no authority**. Every rung below was met on `main`
before the flip: six `IMPLEMENTED` subskills (GIT-C…H, failing-first + mutation suites), deterministic
inspector tests in CI on every PR (`VALIDATED`), and the GIT-I shadow recomputed from real history at
`78eab75` (`SHADOWED`, `examples/git-shadow-evidence.json` + `skills/badf-git/evidence/shadow-evidence.md`).

**Activation changes what the family *is*, not what it *may do*.** `GIT_CAPABILITY != GIT_AUTHORITY`
holds after the flip exactly as before it: no `scripts/badf_git.py`, no `schemas/git.schema.json`, no
mutation path, `badf_gate.py` the sole gate authority, and the human still merges (BADF-MAIN-001). The
eight registry pins in the badf-git test modules (contract, baseline, staleness, composition, integration,
recovery, release, shadow) move to `ACTIVE` with the truth; the contract-surface guard is unchanged. The six subskills stay `IMPLEMENTED` — family = capability admission, subskill =
implementation status (the `badf-research` precedent, WP-0058; the registry-only flip is the
`badf-solution-design` precedent, WP-0077).

**ACTIVE does not erase the declared non-coverage.** The shadow's gaps stand as written: rewrite verdicts
(`STALE_EVIDENCE`) exercised only synthetically; the recovery inventory on real dirty state observed, not
committed; branch-name conformance of landed heads API-observed; no signed tag; the composed-world harness
limitation #160 (GOV-0064) — the composition fixtures judge a candidate with the base's `tests/`. The
shadow record is measured at `605f97f`; landings after it (WP-0082 itself, WP-0083…0086) are not in it —
a re-shadow is a later work package, not a condition of this admission.

## badf-git re-shadow — the record re-measured on the `main` that includes its admission (`BADF-WP-0090`, Issue #175 / GOV-0072)

The GIT-I record was measured at `605f97f`. The program then landed GIT-I, the #160 harness fix and
its own admission GIT-J — three more record-bearing landings. `examples/git-shadow-evidence.json` is
re-measured at `fc9e727` under the **same corpus rule** (the program's history since the GIT-A freeze
`b1e0f5a`): **7/7** record-bearing landings `MATCH` their claims, **21/21** first-parent landings since
`8673d9a` `CONFORM`, 15 landings without a record render `composition_verified: false`, the staleness
and release cases stand, the runner citations gain the #161, #173 and #174 runs. **No gap was closed:**
the non-coverage list is kept in full. The note also corrects a count that had propagated from GIT-I:
the family has **six** subskills (GIT-C…H), not seven. The generator is not a repo tool — the shadow
test recomputes every case from the object store on every run, in CI and in the composed world.

## badf-implementation-plan — G06 planning contract freeze (`BADF-WP-0091` / WP-IMP-A, Issue #177 / GOV-0073)

BADF had an enforced **G06 gate** (WP-0067: `work-breakdown`/`test-plan`/`release-plan`/`rollback-plan`
with an acyclic dependency graph) and, since WP-IMP-0, a WP template that conforms to its schema — but no
capability to turn an approved G01–G05 design into those artifacts. `badf-implementation-plan` is that
capability, frozen `DESIGNED`: a thin planning composition/router that decomposes approved design into a
**governed Work Package DAG** and normalizes it into the **existing** four G06 artifacts. SKILL.md + 16
references + `IMP-I01…IMP-I17`.

The doctrine it freezes is `Task ≠ Work Package ≠ GitHub Issue ≠ Branch` and `Implementation Plan ≠
Authority` — a Work Package is the *bounded execution contract* (scope · acceptance · authority · risk ·
dependencies · expected surfaces · tests · evidence · budget · rollback · stop conditions); a task is an
execution step inside it; an Issue is a tracking projection whose state grants no authority (IMP-I14).
Four boundaries carry it: **(1) composes G06's existing four artifacts, adds no fifth gate artifact** and
changes no `lifecycle.json`; **(2) authority is derived from `change_class` (C0–C3) and the matrix, never
a new A0/A2 system** (IMP-I07); **(3) it declares execution topology while `badf-git` realizes it**
(IMP-I15); **(4) no execution engine, no `scripts/badf_implementation_plan.py`, no schema** at freeze
(IMP-I17), and it does not duplicate G01–G05 (IMP-I02). Spec Kit, Superpowers and Matt Pocock's
`to-tickets` are adapted (plan→WP, tracer-bullet vertical slices, expand-migrate-contract, TDD, worktrees)
but never adopted as authority — external capability can shape a plan, never expand authority. The
ladder WP-IMP-A…E mirrors solution-design / security-design; per **#171** the typed planning fields
WP-IMP-B adds will be enforced by **code controls**, not by trusting the schema walker's type field.
Registry `DESIGNED`.

## badf-implementation-plan → IMPLEMENTED — the Work Package schema extension (`BADF-WP-0092` / WP-IMP-B, Issue #179 / GOV-0074)

WP-IMP-A froze the contract; WP-IMP-B gives the **Governed Work Package** its richer shape by extending
`schemas/work-package.schema.json` with the planning fields — `dependencies`, `source_baselines`,
`expected_surfaces`, `authority_requirement`, `risk_factors`, `test_obligations`, `evidence_obligations`,
`execution_budget`, `stop_conditions`, `composition` — **all optional**, so every one of the 76 existing
records still validates (`repo` PASS on the branch and in the composed world). The extension is strictly
additive: nothing enters `required`, `additionalProperties` stays absent (tightening it would reject
`note` and the ledger keys), and it **documents** the two keys `reconcile_work_package` writes on every
landing (`landed_content_tree`, `composition_verified`). The schema walker enforces what it can here —
`enum` (an unknown `stop_condition` or `test_obligation.level` is refused), `pattern` (a dependency that
is not a `WP-…` id is refused), nested `required` (an `execution_budget` without `max_attempts` is
refused) — while the **type-checking, coverage and DAG-derivation controls are WP-IMP-C code controls**,
because the walker does not type-check non-object types (#171 / GOV-0071) and `parse_composition_record`
already trusts nothing structurally. No `lifecycle.json` change, no new gate, no
`scripts/badf_implementation_plan.py`. Registry `DESIGNED → IMPLEMENTED`.

## badf-implementation-plan → VALIDATED — the G06 planning controls (`BADF-WP-0093` / WP-IMP-C, Issue #181 / GOV-0075)

WP-IMP-B gave the WP record its schema; WP-IMP-C puts the deterministic controls where the **gate actually
enforces** — the `work-breakdown` artifact (`check_work_breakdown`), the master WP DAG the gate already
validates (§11). A material finding grounds the placement: `check_schema("work-package", …)` is never
called anywhere in the gate — the WP record schema is the human-readable contract (test-validated), while
the `work-breakdown` is the machine-enforced projection. Five controls join the existing acyclic check,
each fires only when its optional per-task field is present (so a minimal `id`/`description`/`depends_on`
task is unaffected), and each is mutation-killed: **IMP-C1** (IMP-I07) a task's `authority_requirement`
cannot omit a role the authority matrix requires for its `change_class` — the plan cannot reduce
authority; **IMP-C2** (IMP-I09) every `acceptance` claim carries a `test_obligation` claiming it; **IMP-C3**
(IMP-I11) a declared `execution_budget` has a positive-integer `max_attempts` — a **code** check, because
the walker does not type-check non-object types (#171) and even rejects `True` (a Python int); **IMP-C4**
(IMP-I12) a declared `stop_conditions` names at least one; **IMP-C5** (IMP-I06) `composition_after`
resolves to real tasks and is acyclic, kept **separate** from `depends_on` (blocking ≠ landing order). The
`work-breakdown` schema gains these as **optional** task fields (`additionalProperties:false` stays), so
the existing minimal example and every record still validate. No `lifecycle.json` change, no new gate
command, no `scripts/badf_implementation_plan.py`. Registry `IMPLEMENTED → VALIDATED`.

## badf-implementation-plan → SHADOWED — representative planning calibration (`BADF-WP-0094` / WP-IMP-D, Issue #183 / GOV-0076)

`SHADOWED` means the controls were run against cases and behaved. `badf-research` and `badf-architecture`
shadowed on **real** BADF history; `badf-implementation-plan` — like solution-design and security-design
before it — has **no real G06 planning breakdowns yet** (BADF's own work packages are governance work,
not product implementation plans), so the shadow is **REPRESENTATIVE**, and the evidence
(`references/shadow-evidence.md`) says so in its first section: a real re-shadow is owed the first time a
project plans through G06. The calibration ran `check_work_breakdown` over representative breakdowns:
**all six defect classes refused** (cyclic depends_on · authority-reduced · uncovered-acceptance ·
non-positive/boolean max_attempts · empty-stop · dangling/cyclic composition_after); **zero false
positives** on three clean breakdowns — including the feature breakdown's **minimal task carrying no
planning fields**, the false-positive check that proves the controls are field-scoped (a task without the
optional fields triggers none of them). And it **declares its non-coverage**: the cross-WP execution
frontier (it spans a whole plan and a live ledger, not one artifact), the semantic resolution of every
ref against its real artifact, and the GitHub-issue projection / `badf-git` topology realization (contract
boundaries, demonstrated as doctrine not run). Two committed shadow breakdowns
(`examples/work-breakdown-shadow-migration.json` — an expand/migrate/contract sequence — and
`-feature.json` — a vertical slice) are validated in the test. No `lifecycle.json` change, no new control,
no second validator. Registry `VALIDATED → SHADOWED`; `APPROVED`/`ACTIVE` remain the operator's admission
decision.

## badf-implementation-plan → ACTIVE — operator admission on a representative shadow (`BADF-WP-0095` / WP-IMP-E, Issue #186 / GOV-0077)

`SHADOWED → ACTIVE` is a **human admission gate** — self-approval is prohibited, so no agent crosses it.
The operator's standing directive — `/loop … proceed from WP-IMP-A to WP-IMP-E` (2026-08-30), confirmed by
"proceed your tasks" — is the admission decision to **activate on the representative shadow**, rather than
hold `ACTIVE` indefinitely for a real G06 plan that BADF — whose own work packages are governance work —
may not produce soon. This WP records that decision as a governed registry advance, mirroring
`badf-solution-design` WP-SOL-E and `badf-security-design` WP-SEC-E: `ACTIVE` **grants the skill no new
authority** (IMP-I17 — `badf_gate.py` is the sole gate authority; IMP-I15 — the plan cannot execute its
own WPs; IMP-I14 — an Issue grants no authority; IMP-I07 — authority stays derived from `change_class`),
and there is no `lifecycle.json` change, no new control, no second validator. The admission does **not
erase the caveat**: `references/shadow-evidence.md` still labels the shadow representative, and the owed
real-project re-shadow is filed as a tracked follow-up (**#185**, `DISCOVERED`, trigger = the first real
G06 plan). This **completes the WP-IMP-A…E ladder** (`DESIGNED → IMPLEMENTED → VALIDATED → SHADOWED →
ACTIVE`) — the third capability, after `badf-solution-design` and `badf-security-design`, to traverse it
end to end, and the one that gives G06 (Implementation planning) its authoring capability. Registry
`SHADOWED → ACTIVE`.

## badf-build — G07 capability contract freeze (`BADF-WP-0096` / WP-BLD-A, Issue #188 / GOV-0079)

`badf-build` is frozen `DESIGNED` as the next capability after `badf-implementation-plan` reached `ACTIVE`:
the plan decides *how* authorized work is decomposed and retains IMP-I15 (it cannot execute its own Work
Packages); `badf-build` performs the **authorized mutation** of exactly one Governed Work Package inside
its exact scope, baseline, budget and stop contract; G08 verifies independently; `badf-git` governs
integration; the canonical gate evaluates the four G07 evidence types; authority permits the transition.
The freeze is a thin router (`SKILL.md`) with eighteen invariants **BLD-I01…I18** and fourteen references,
registered C1 with no tools — no runtime, no `scripts/badf_build.py` (BLD-I18: deterministic G07 semantics
stay in `badf_gate.py`), no schema, no lifecycle change.

**What it absorbs and what it refuses.** Matt Pocock's `implement`/`tdd` discipline (bounded source
contract, governed TDD at durable seams, red before green, continuous typecheck/test, full verification
at finish, review after implementation) and obra/superpowers' execution pipeline (isolation, fresh-context
units, review loops, recovery ledger, verification before completion) are adapted as REFERENCE only.
Their authority semantics are rejected: a ticket is not authority, an agent's "ruling" is not a BADF
authority decision, scope does not expand autonomously, finishing a branch is not merge permission, and
build-side review does not satisfy G08 independence. TDD is governed, not religious —
`TDD_REQUIRED` where a durable observable seam exists, `TDD_NOT_APPLICABLE_WITH_REASON` with an alternate
verification obligation where it does not; the doctrine is `NO UNVERIFIED MUTATION`. Test seams come from
the G06 `test-plan`; a `TEST_PLAN_DEFECT` routes upstream rather than moving the seam. Delegation can
only narrow authority (`delegated_authority ⊆ WP_authority ⊆ repository_policy`; a subagent task is not a
Work Package). Actual surface is compared with planned surface and `UNEXPECTED_SCOPE` is refused or
re-authorized at build time. Design drift returns upstream as `*_CHANGE_REQUIRED`.

**Ladder:** BLD-B formalizes the four G07 evidence schemas by extending the self-dossier producer and adds
the preflight/execution substrate and build ledger; BLD-C adds deterministic G07 controls to the gate;
BLD-D shadows on every G07 self-dossier BADF has produced since WP-0030; BLD-E is the operator's admission.
A successful build proves only that the authorized change was built and author-verified — never
"independently verified", "approved to merge", "approved to release" or "safe for production".

## check_schema type conformance — closing the walker's type gap (`BADF-WP-0097`, Issue #189 / GOV-0080, closes #171)

The `check_schema` walker is BADF's single structural authority for ~25 gate-validated artifacts
(work-breakdown, test-plan, release-plan, rollback-plan, solution/security-composition, architecture,
requirements, …). It enforced `required`, `enum`, `pattern`, `additionalProperties: false`, and the
object-must-be-a-mapping rule — but it did **not** refuse a value whose JSON type mismatched a declared
scalar/array `type`: an `array` given an object was silently skipped (the items loop is guarded by
`isinstance(val, list)`), and `string` / `number` / `integer` / `boolean` were never type-checked
(discovered under WP-IMP-0, tracked as **#171**). The typed planning fields the G06 ladder added
(`execution_budget`, `stop_conditions`, `dependencies`, …) were therefore declared but not
type-enforced at the schema layer.

This WP adds deterministic **type conformance** for `array` / `string` / `integer` / `number` /
`boolean`, at any depth — Option 1 from #171, closing the gap for **all governed artifacts at once**
rather than sprinkling per-field code controls. Because a Python `bool` is an `int` subclass, `integer`
and `number` **exclude bool explicitly**. The walker still deliberately ignores `minLength` / `minItems`
/ `minimum` / `format` (out of #171's scope — non-emptiness and value bounds stay code controls, e.g.
IMP-C3's positive-integer check, kept as defense-in-depth).

**Audit-first** (the safety gate, run before coding): the strict walker was applied to the tree at
`d4b8c4a` and `badf_gate.py repo` ran **PASS** — zero governed records break. One observed interaction:
a bool `max_attempts` (and a non-numeric NFR `target.value`) is now refused at the schema layer *before*
the downstream code control (IMP-C3, `check_nfr`) emits its message; the refusal is preserved, only the
layer moved (the three affected G02/G06 test needles were widened to `a number` / `integer`, matching
both layers — the code controls stay as defense-in-depth). change_class **C1** (shared control surface)
→ independent review. Patch tier. Registry unchanged (no capability advances).
## badf-build → IMPLEMENTED — typed G07 evidence, the self-dossier extended, the build ledger (`BADF-WP-0098` / WP-BLD-B, Issue #191 / GOV-0081)

Before this rung BADF's own G07 evidence was produced but not *judgeable*: `source_revision: "HEAD"`
instead of a revision, `unit-test` a `NOT_RUN` placeholder deferred to compose, no changed-path list
and no planned-vs-actual surface, a `py_compile` "build" with no environment identity. BLD-B keeps the
**one** producer — `badf_gate.py self-dossier` (BLD-I18) — and makes its four objects exact (BLD-I16):

- **Typed schemas** `schemas/{source-change,build,unit-test,documentation}.schema.json` specialize
  `evidence.schema.json` with a closed `binding` object. `source-change` binds `base_sha`, `head_sha`,
  the **content tree** (the durable identity of a squash-landed change — a branch SHA is unreachable on
  a fresh runner, as GIT-E learned), `changed_paths`, `change_digest`, the declared `expected_surfaces`
  and the **`unexpected_paths`** outside them; `build` binds command, cwd, python/platform identity,
  exit code and artifact digests; `unit-test` binds the author's run log (`Ran N tests`, OK/FAILED),
  per-module obligations with **red and green observed** (a `failing-first.txt` and the log, digest-bound)
  and names the composed-tree gate as the fresh authoritative run (BLD-I09); `documentation` answers
  what changed, whether a contract or behavior changed, and **what was not updated and why**.
- **Scope containment at packaging time (BLD-I04).** With `expected_surfaces` declared, an out-of-surface
  path is listed and the request is held with condition C-2 naming it — refused or re-authorized, never
  absorbed; without a declaration the dossier says so as non-coverage rather than staying silent.
- **A failing log refuses assembly.** The producer will not bind a `FAILED` run into a request; absent a
  log the object is honestly `NOT_RUN`.
- **Validation on both sides.** The producer runs `check_schema` before writing each typed object; a
  `HUMAN_REQUIRED` request with a malformed binding is refused on the dossier; on a passing dossier the
  G07 `EVIDENCE_RULES` open the artifact and require the binding to agree with it (paths in the diff,
  counts in the log, exit code in the build transcript). Generic objects stay admissible — additive.
- **The build ledger** `work/<WP>/build/progress.jsonl` records `START · BASELINE · VERIFY · HANDOFF`
  as hash-chained `run-ledger-event` records with `session.json` beside it; `badf_gate.py build-ledger
  <WP>` verifies the chain read-only. **No verdict reads it** — it is recovery and evidence.

The dossier's `source_revision` semantics are untouched; `lifecycle.json` and the G07 type list are
untouched. `badf-build` advances `DESIGNED → IMPLEMENTED` with its digest unchanged.

## badf-engineering-verification — G08 capability contract freeze (`BADF-WP-0100` / WP-VER-A, Issue #195 / GOV-0083)

`badf-engineering-verification` is frozen `DESIGNED` as the capability after `badf-build` reached
`IMPLEMENTED`: the build performs the authorized mutation and hands off (BLD-I17); **this skill
independently challenges what changed**; `badf-git` composes and integrates; the canonical gate evaluates
the four G08 evidence types; `quality_authority` permits the transition. The freeze is a thin router
(`SKILL.md`) with twenty invariants **VER-I01…I20** and sixteen references, registered C1 with no tools —
no runtime, no reviewer executor, no `scripts/badf_engineering_verification.py` (VER-I20: deterministic
G08 semantics stay in `badf_gate.py`), no schema, no lifecycle change, no gate change.

**Two planes, in BADF's own vocabulary.** docs/03 already defines the **Reviewer** (independent bounded
review, declares non-coverage) and the **Verifier** (executes deterministic tests independently of the
author). G08 is the seam between them: the Reviewer plane *proposes* findings through isolated,
defect-first, read-only, sealed lens passes; the Verifier plane *observes* integration, contract and
composed-tree facts through an approved runtime; schemas normalize; the gate evaluates; authority decides.
`AGENT OUTPUT = DRAFT` · `NO FINDINGS ≠ CORRECTNESS` · `SOURCE_HEAD_GREEN ≠ COMPOSED_VERIFIED` ·
`G08 ≠ G09` · `VERIFICATION ≠ APPROVAL`.

**What it reuses instead of inventing.** Target identity is the committed git-composition record's
`expected_content_tree` plus a `git-staleness` verdict of `CURRENT` — no new composed-identity field.
Reviewer verdicts are docs/03's five; contract results map onto the evidence `outcome` enum
(`INDETERMINATE → BLOCKED`, never a pass); the finding item is the architecture-assurance finding
extended with lens and reporters; the composed run is `badf_compose.py` (already the fresh run, BLD-I09);
verification run events are `run-ledger-event` records; per-artifact non-coverage extends the
dossier-level `check_non_coverage`. Three **artifact** states — `PROPOSED / OBSERVED / CANONICAL` — name the
distinction between an agent's draft, a runtime's observation and a digest-bound, lockfile-signed object;
they are not the §10 memory labels.

**What it refuses.** A security *lens* is security assurance and belongs to `badf-security-assurance`
(named, not built): every G08 review declares it as non-coverage rather than absorbing it, while a
security-*kind* finding from any lens remains a finding. Independence is an execution-level contract
(distinct run, sealed-input digest, no prior findings, no author reasoning, no cross-pass communication
before the ballot); the account-level reviewer ≠ author gap under a single collaborator stays the carried
OPEN condition — a banner never satisfies it. Codex `review-agent`, Apache Magpie and `qa-tester` are
adapted as REFERENCE only; an AI verdict as approval, all-green as coverage, an agent-reported result as an
observation, and an external tool's ruling as authority are rejected.

**Ladder:** VER-B adds the four typed G08 schemas, the finding record, the verification matrix, the run
ledger and a `badf_gate.py verify` subcommand; VER-C adds deterministic G08 controls to the gate (lean
disabled); VER-D shadows on WP-2026-0010's G08 dossier and BADF's own review history with known and
injected defects; VER-E is the operator's admission on that evidence. No findings does not mean
correctness; passing tests do not mean coverage; source-head success does not mean composed-result safety;
G08 does not replace G09.
## badf-build → VALIDATED — seven deterministic G07 controls in the canonical gate (`BADF-WP-0099` / WP-BLD-C, Issue #194 / GOV-0082)

BLD-A froze the invariants and BLD-B made them measurable; BLD-C makes the gate **refuse** their
violation. All seven live in `badf_gate.py` — in the self-dossier producer, in the G07 evidence rules
and in `validate_dossier` — typed in code (never walker-trusted), firing only on the field that
declares them, so every object already on the ledger stays valid and nothing is declared to satisfy
a control.

| Control | Invariant | Refuses |
| :--- | :--- | :--- |
| **C1** authority before mutation | BLD-I03 | a request assembled under a demand that is absent, not `AUTHORIZED`, or not authorized by a **human** |
| **C2** exact baseline | BLD-I02 | a `source-change` whose `base_sha` is not the work package's `base_revision`, or whose content tree / base disagree with the composition record |
| **C3** scope containment enforced | BLD-I04 | a **PASS** with paths outside `expected_surfaces` unless a declared `discovery_allowance` covers each (a request keeps its C-2 condition) |
| **C4** red before green, exceptions explicit | BLD-I07/I08 | declared unit obligations with no observed red and no `tdd_exception.reason` — silence; an exception is bound as `binding.tdd = {applies: false, reason}` |
| **C5** fresh verification | BLD-I09 | a unit-test `PASS` on a passing dossier with no composition record — the composed-tree run *is* the fresh run |
| **C6** budget and stop dominate | BLD-I11–I13 | a build whose ledger records `STOP`, or more `RETRY` events than `execution_budget.max_attempts` — refused at assembly and on a PASS; the ledger is read for refusal only, never to grant |
| **C7** delegation is a strict subset | BLD-I10 | a delegation in `build/session.json` with a path outside the declared surface, a missing prohibition (`push`, `merge`, `release`, `credential-use`), or an integration tool — on every disposition; declared delegations survive re-assembly |

Three optional inputs were added so the controls have something declared to judge, all additive:
`expected_surfaces.discovery_allowance` and `tdd_exception` on the work package, `binding.tdd` on the
typed unit-test evidence. No change to `check_schema`, `badf_compose.py`, the CI workflow or
`lifecycle.json`. `badf-build` advances `IMPLEMENTED → VALIDATED`; the shadow on BADF's own G07
history (BLD-D) and the operator's admission (BLD-E) remain.

## badf-engineering-verification → IMPLEMENTED — typed G08 evidence, the verification record, `verify` (`BADF-WP-0103` / WP-VER-B, Issue #200 / GOV-0086)

VER-A froze the two-plane contract; this rung makes its shapes checkable without adding an executor, a
runner or a second gate. Four typed schemas specialize `evidence.schema.json` for `independent-review`,
`integration-test`, `contract-test` and `composed-tree-test` with a **closed `binding`** — the BLD-B
pattern, additive: `check_g08_binding` (now the `EVIDENCE_RULES` entry for the four G08 types) validates a
binding only when one is present and opens the artifact to corroborate it, so a generic object stays
admissible and `work/WP-2026-0010`'s historical G08 dossier is untouched. What the rule refuses: a typed
review that is a bare PASS — no findings and no non-coverage without naming the contract that permits a
comprehensive-coverage claim (VER-I10/I11) — or whose verdict `APPROVE` contradicts its own OPEN blocking
findings; a typed observation whose `producer.type` is `agent` (VER-I08: a claimed result is not an
observation); a contract result that does not serialise onto the evidence `outcome`
(`CONFORMANT → PASS`, `NONCONFORMANT → FAIL`, `INDETERMINATE → BLOCKED`, `NOT_APPLICABLE → NOT_APPLICABLE`;
VER-I14); integration counts or exit codes that disagree with the transcript the gate reads; a composed
observation that is not `CURRENT`, did not reproduce (`equal`, recorded == recomputed content tree), or
whose tree does not appear in the artifact (VER-I01/I15). Schema-level independence: `same_execution`,
`prior_findings_visible`, `author_reasoning_visible` and `cross_pass_communication_before_ballot` admit
only `false`; `target_digest_equal` only `true`.

**The verification record.** `schemas/verification-record.schema.json` carries what a G08 review IS:
the sealed target, the lenses routed, the persisted ballots, the independence block, the findings (the
architecture-assurance finding item reused — `VF-NNN`, kind, severity, locations, expected / observed /
impact / failure scenario — plus `lens`, `reported_by`, `also_reported_by`, `requirement_refs`,
`evidence_refs`), the synthesis ledger (`withdrawn` with a reason and a `by`; `downgraded` with a
`decision_ref`), the evidence index, the verification matrix (claim → change → review → integration →
contract → composed → `VERIFIED | PARTIAL | UNVERIFIED`), non-coverage, and `authority.verification_authority:
false`. `badf_gate.py verify <path>` mirrors `assure` / `solution` / `security` and refuses: a ballot whose
sealed digest is not the council's (VER-I05); a duplicate reviewer identity or run (VER-I19); the author's
run balloting (VER-I04); a balloted finding neither carried nor withdrawn with a reason — synthesis cannot
erase (VER-I12); a finding no persisted ballot reported (VER-I06); a matrix ref that does not resolve; a
`VERIFIED` row with an OPEN MAJOR/CRITICAL finding against it or without a composed-tree observation
(VER-I15); an empty non-coverage (VER-I11). It prints "grants no verification authority" and grants none.

**Ladder.** VER-C judges these typed objects against the Work Package and the composition record at
dossier level (target and staleness binding, quorum by change class, runtime credit, per-artifact
non-coverage, finding preservation across the dossier) — lean disabled; VER-D shadows on the G08 material
BADF has; VER-E is the operator's admission on that evidence. A verification ledger writer stays declared,
not built, until a runtime exists to write it.
## badf-build → SHADOWED — the program's own builds, judged by the tools it built (`BADF-WP-0101` / WP-BLD-D, Issue #197 / GOV-0084)

`badf-build` shadows on the one corpus BADF has: **67 landed work packages carrying a G07 self-dossier**
(WP-2026-0011, WP-2026-0100), measured at `8f3d805` and recorded once in `examples/build-shadow-evidence.json`,
which `tests/test_badf_build_shadow.py` recomputes from the object store on every run — artifact digests at the
landed tree, the demand record, `content_tree` — and whose tampering it refuses. What history rendered:
**67/67** requests digest-bound (no request ever pointed at nothing), **67/67** demands `AUTHORIZED` by a
human (C1 would have admitted every one), **3/3** typed bindings recomputing `MATCH` (WP-2026-0098, WP-2026-0099, WP-2026-0100 — the last
produced by VER-A under the same producer), and fresh verification honest about the pre-BLD-B era: 55 deferred,
10 deferred with a composition record, 2 `PASS` — each behind a composed run, **0 without** (C5 replayed). One dossier
(WP-2026-0010) predates the ledger's identity window and is declared as not placeable, not counted.

**No contract gap surfaced — and the non-coverage is named, not implied.** C3 (scope containment), C4 (red
before green / explicit exception), C6 (budget and stop) and C7 (delegation subset) have **no historical
corpus**: nothing on the ledger ever declared `expected_surfaces`, `test_obligations`, a `RETRY`/`STOP` or a
delegation; they are proven on scratch fixtures only, and no build controller has yet executed a Work Package
through the workflow. That statement travels verbatim into the BLD-E admission: `ACTIVE` will mean "admitted
on the program's own builds, with four controls proven only on scratch", and not more. `badf-build` advances
`VALIDATED → SHADOWED`; no gate, schema or lifecycle change.

## badf-engineering-verification → VALIDATED — seven deterministic G08 controls in the canonical gate (`BADF-WP-0105` / WP-VER-C, Issue #204 / GOV-0088)

VER-B made typed G08 objects checkable in isolation; this rung judges them **against each other, the Work
Package and the composition record** — as one **pure** function, `check_g08_dossier(dossier, work_package,
evidence, composition_record, record)`: no reads, no writes, no git. `validate_dossier` resolves the inputs
(the indexed evidence objects, `work/<WP>/evidence/G07/composition-record.json` when present, and the
verification record when a typed review's artifact is one — validated first by `validate_verification_record`)
and calls it **only for a G08 dossier claiming `PASS` / `PASS_WITH_CONDITIONS`**; the G07 flow and every
other gate are untouched. Every control fires only on fields that are declared, so every dossier on `main`
— WP-2026-0010's generic G08 dossier included — stays valid, and `validate_dossier` stays idempotent.

**The seven controls.** **C1 exact target (VER-I01):** every typed binding binds the dossier's
`source_revision` and, when the record exists, the composition record's `expected_content_tree` and
`target_base_sha`. **C2 one composed identity (VER-I05):** all typed objects on one dossier bind the same
content tree — a review of tree X with observations of tree Y verifies nothing together. **C3 independence
and quorum (VER-I04/I19):** the author's execution or identity cannot be the reviewer unless the
single-collaborator deviation is carried as an OPEN condition (never hidden, never satisfied by a banner);
C2/C3 change classes require a verification record with ≥2 / ≥3 distinct reviewers *and* runs and the
mandatory lenses (`correctness` + `quality/test`, + `data/integration` at C3). **C4 runtime credit
(VER-I08):** a Work Package may declare `verification_obligations.runtime_required`; then an untyped
observation on a passing dossier earns no credit. **C5 per-artifact non-coverage (VER-I11):** a typed
observation with empty `non_coverage` is refused unless the Work Package names that type in
`verification_obligations.comprehensive_coverage_permitted_for`. **C6 review blockers resolved
(VER-I12):** an OPEN MAJOR/CRITICAL finding refuses `PASS`; on `PASS_WITH_CONDITIONS` each maps to a
dossier condition naming it; the review's findings are carried or withdrawn by the record — synthesis
cannot erase. **C7 composed-result authority (VER-I15):** `composed-tree-test` is never `NOT_APPLICABLE`
— a G08 dossier without a composed observation cannot pass; `contract-test` may still be declared.

`schemas/work-package.schema.json` gains the optional, closed `verification_obligations` object beside
BLD-C's `tdd_exception` and `discovery_allowance` — additive, as every planning field has been. Lean mode
disabled: these are HARD INVARIANTS. **Ladder:** VER-D shadows the controls on the G08 material BADF has
(WP-2026-0010's dossier and the seats' review history, with known and injected defects); VER-E is the
operator's admission on that evidence.
## badf-build → ACTIVE — BLD-E admission (`BADF-WP-0104`, Issue #203 / GOV-0087)

`badf-build` is admitted `SHADOWED → ACTIVE` by **registry status flip only**: `digest` is the GIT-A-style
freeze value (`SKILL.md` untouched since BLD-A), `allowed_tools: []`, `risk_class` C1. The authorization is the
operator's decision — pre-authorized for the whole ladder on #188 (comment 5469168780, "proceed on your
call to build the badf-build from WP-BLD-A - WP-BLD-E as ACTIVE") and bound to the evidence on #203. Every
rung below was met on `main` before the flip: BLD-A `cf431fa` (contract, BLD-I01…I18), BLD-B `6814a24`
(typed G07 evidence, build ledger), BLD-C `8f3d805` (seven deterministic controls, mutation-killed,
independently reviewed), BLD-D `07c23f7` (shadow on every landed self-dossier: requests digest-bound,
demands human-authorized, typed bindings exact, no `PASS` without a composed run).

**Activation changes what the family *is*, not what it *may do*.** `BUILD ≠ INTEGRATION` holds after the
flip exactly as before it: no `scripts/badf_build.py`, no mutation path, no push/merge/release tool; the
seven controls and the typed producer are byte-untouched; the human still merges (BADF-MAIN-001).

**`ACTIVE` does not erase the shadow's non-coverage.** It is carried here verbatim: **C3** scope
containment, **C4** red before green / explicit exception, **C6** budget and stop, **C7** delegation subset
have **no historical corpus** — nothing on the ledger ever declared `expected_surfaces`, `test_obligations`,
a `RETRY`/`STOP` or a delegation — and are proven on scratch fixtures only; **no build controller** has yet
executed a Work Package through the workflow. `ACTIVE` therefore means "admitted on the program's own
builds, with four controls proven only on scratch", and not more; the first real project — or the first
build executed under the contract — is the deferred re-shadow's trigger.

## badf-engineering-verification → SHADOWED — the G08 controls on the material BADF has (`BADF-WP-0106` / WP-VER-D, Issue #207 / GOV-0089)

Three case classes, one record (`examples/verification-shadow-evidence.json`), every case recomputed from
the repository on every run by `tests/test_badf_verification_shadow.py` — and the honest first sentence
states what is real, what is reconstructed and what is representative. **`historical-generic-dossier`:**
WP-2026-0010 — the only real G08 dossier, four binding-less agent-produced objects — replays UNTOUCHED
through `check_g08_binding` and `check_g08_dossier` (the additive proof, now measured, not just asserted).
**`real-review-encoded` (5):** BARCHI-1's real verdict arc — #196 **Request Changes** (the synthetic-id
collision, a genuine OPEN `MAJOR` finding) → **Approved** on the fix head with the finding `RESOLVED` and
the `WP-2026-9999` sentinel as resolution evidence, then #201 / #202 / #205 — encoded under the encoded
reviewer's own honesty conditions: one ballot per record, the real comment id as `reviewer_run_id`, sealed
digest labeled RECONSTRUCTED, no council claimed, non-coverage carried verbatim, matrix rows `PARTIAL`
(no composed observation can be reconstructed from prose). `badf_gate.py verify` accepts all five and
refuses tampering — the digest changed, the #196 finding erased (VER-I12), `VERIFIED` without a composed
ref (VER-I15). **`representative-typed-dossier` (12):** ten injected defects each refused by the control
that owns it — every control C1–C7 owns at least one refusal — and two clean dossiers admitted (0 false
refusals). Metrics measured and named; **reviewer correlation is NOT MEASURABLE with one reviewer seat**
— a non-coverage the future BADF-QA / BADF-REV seats exist to close.

**COI, disclosed:** the encoded reviewer is also the seat's usual reviewer; BARCHI-2 (not encoded)
co-reviews the encoding class for fidelity. Registry `VALIDATED → SHADOWED` (digest unchanged); no gate,
schema or lifecycle change (ladder-internal). **Admission (`VER-E`) is the operator's decision on this
evidence, asked on its own issue — never pre-granted**; the real typed re-shadow trigger (first project
G08 with typed objects) is filed as a deferred issue at close-out, mirroring #185 / #166.

## badf-engineering-verification → ACTIVE — the operator's admission on the shadow evidence (`BADF-WP-0108` / WP-VER-E, Issue #214 / GOV-0092)

The G08 verification capability is admitted `ACTIVE`. **The flip grants nothing**: registry status only,
digest unchanged, `allowed_tools: []`, `risk_class: C1`, no `scripts/badf_engineering_verification.py`
(VER-I20), no gate, schema or lifecycle change — `VERIFICATION ≠ APPROVAL` (VER-I18) is as true after the
admission as before it. C1–C7 have been enforcing on every G08 dossier since `5b428f7` independently of any
label; what changes is that the contract, the typed schemas, the seven controls and the shadow evidence are
now the **admitted** G08 verification doctrine for BADF-governed work.

**What the operator admitted over — carried into the admission, not around it.** The decision was put on
#214 with the alternative (`HOLD AT SHADOWED`) stated beside it, and these four gaps named in the issue body
rather than only in linked evidence:

- **No typed real G08 dossier exists** — the typed-object shadow is representative fixtures. A real
  re-shadow is owed the first time a project passes G08 with typed objects; it is filed as **#217
  (GOV-0093)**, deferred and trigger-gated (the #212 / #185 / #166 pattern). That issue is the
  admission's discharge path: a re-shadow discharges a caveat, it does not re-grant a status.
- **One reviewer seat at encoding time** — reviewer correlation `NOT_MEASURABLE`. The BADF-QA and BADF-REV
  seats change this going forward.
- **The real-review class is RECONSTRUCTED** from public prose verdicts with ids cited — honest, but not
  observed records.
- **The per-fixture scratch-clone `validate_dossier` path** is declared, not shipped — end-to-end
  `validate_dossier` is exercised by the historical WP-2026-0010 case and CI's composed run.

**The ladder that earned it:** VER-A froze the two-plane contract and VER-I01…I20 (#198); VER-B added the
four typed G08 schemas, the verification record and `badf_gate.py verify`, additive so WP-2026-0010's
historical dossier stayed untouched (#201); VER-C added the seven pure dossier-level controls (#205); VER-D
measured them — WP-2026-0010 `UNTOUCHED`, five RECONSTRUCTED single-reviewer records of a real verdict arc
verified and tamper-refused, 12/12 injected defects refused with every control and VER-I10/VER-I14
load-bearing, 0 false refusals (#208). Every rung was failing-first and mutation-killed; the VER-D rung was
independently reviewed by BADF-QA and BADF-REV, both of whom issued Request Changes that found real defects
— two dead assertions and an anachronistic binding — before approving the fixed heads.

**Doctrine, unchanged by the admission:** no findings does not mean correctness; passing tests do not mean
coverage; source-head success does not mean composed-result safety; G08 does not replace G09. The gate
evaluates the evidence and `quality_authority` decides whether G08 advances.
## badf-build's Boundary named a family that does not exist — and the first controller run (`BADF-WP-0109`, Issue #219 / GOV-0095)

`skills/badf-build/SKILL.md`'s frozen **Boundary** block named `badf-verification (G08)` as the family
that independently verifies a build. No such family is in `badf/skill-registry.json`; the one that
verifies at G08 is `badf-engineering-verification`. Every other family the surface names resolved. In a
block a build controller reads to learn **who checks its work**, that is a dangling authority reference —
found by BARCHI-3 at their VER-A freeze and left for this surface's owner rather than edited across the
seat boundary. The fix is one name (the block re-aligns by whitespace; no description changes), the
registry digest re-pinned in the same change, and the activation test's pinned literal moved with it —
its meaning preserved, since it still ties the pin to `sha256(SKILL.md)`. The **guard** is what keeps the
class out: every `badf-*` token appearing anywhere under `skills/badf-build/**` must resolve in the
registry, red before this fix and green after.

**This work package is also the first ever executed *through* `badf-build`'s own workflow** — the family
went `ACTIVE` at `bbec762` having never governed a build. It declared `expected_surfaces` (7 files),
one unit `test_obligation` with a red phase required, an `execution_budget` of 3 attempts and six
`stop_conditions`, and it **delegated one slice** — the guard test — to a subagent whose contract was a
strict subset: `allowed_paths: ["tests/test_badf_build_contract.py"]`, the integration verbs prohibited,
2 attempts. The delegate stayed inside it (verified by the controller, not taken on report) and did not
touch the defect it was writing a guard against, so the red phase was real.

So the controls the BLD-D shadow could only prove on scratch fixtures met real conditions here: **C3**
compared a really-declared surface against the actual diff, **C4** required and got an observed red,
**C6** recorded a genuine `RETRY` (the first attempt at moving the pinned digest silently matched
nothing — there is no `FREEZE_DIGEST` constant, the literal is inline — and the activation test caught
it; 2 attempts of 3), and **C7** judged a real delegation. The build ledger records
`START · BASELINE · RED · RETRY · GREEN · VERIFY · HANDOFF`. #212 (the deferred real-conditions
re-shadow) now has its first real case; discharging #212 remains its own work package.

## badf-release-validation — G09 independent pre-release validation router freeze (`BADF-WP-0107` / WP-VAL-A, Issue #209 / GOV-0090)

`badf-release-validation` is frozen (DESIGNED) as the **G09 independent pre-release validation
orchestrator** — a risk-routed evidence federation that takes the exact G08-verified candidate and
attempts to disqualify it across four **independent** validation classes (quality · security ·
performance · resilience), normalizing the observed evidence into the four G09 evidence types the
lifecycle already names (`quality-validation` · `security-validation` · `performance-test` ·
`resilience-test`). It **composes** those existing types — it adds **no fifth `release-validation`
type, no `scripts/badf_release_validation.py`, no schema, no `lifecycle.json` change** (VAL-I20: the
deterministic G09 semantics arrive inside the canonical `badf_gate.py` at WP-VAL-C, never a competing
validator).

The boundary it defends: G09 is `quality_authority`-owned and establishes **pre-release validation
evidence only** — it does **not** issue UAT, release readiness, go/no-go, deployment or production
claims; **G10** (`release_authority`) owns release readiness and stays untouched. Frozen invariants
**VAL-I01…VAL-I20**: exact-candidate binding (I01, `MIXED_CANDIDATE_EVIDENCE → REFUSE`), risk-derived
routing not "run all QA" (I02), class independence (I03) and no class substitution (I13, one runtime
result cannot fill several evidence slots), runtime observation with an oracle **outside** the agent
(I04) with agent output draft-until-bound (I05), thresholds pre-existing outcomes (I06,
`measurement ≠ PASS`), environment provenance + declared deviation (I07/I08, `staging PASS ≠ production
proven`), security-validation ≠ risk acceptance (I09), resilience hypothesis-driven with observed
recovery (I11/I12), a **conjunctive** G09 dossier where a security blocker cannot be outvoted (I14),
mandatory non-coverage (I15), explicit flake policy (I16), and the gate separations G08≠G09 (I17),
G09≠G10 (I18), G09≠G12 (I19). External sources are **adapt-not-authority**: `petrkindlmann/qa-skills`
(taxonomy/adapters; its `release-readiness` is G10, not G09), Grafana `k6` (performance methodology),
OWASP Secure Agent Playbook (primary security methodology); scanners/runtimes are observation
producers, never authority. Ladder-internal at this rung (SKILL + 17 references, no gate/schema);
WP-VAL-B (typed G09 evidence contracts) and WP-VAL-C (canonical deterministic controls) are
shared-surface and go to BADF-QA + BADF-REV. Authored by BARCHI-1 as Senior ARCH & ENGIN. Registry
`badf-release-validation: DESIGNED`.
## A guard that could not pass — the build shadow's authority case (`BADF-WP-0111`, Issue #225 / GOV-0097)

`tests/test_badf_build_shadow.py`'s `authority-replayed` case compared the record's stored demand
`status` — a **snapshot of a mutable field**, taken at the record's `measured_on` — against the **live**
demand file. So it measured *"is this demand currently `AUTHORIZED`"* while the record claims *"was this
demand human-authorized as measured"*. The consequence was sharper than a loose comparison: the
`CLOSED_DEMAND` branch was **unreachable**. Element 0 is frozen at `AUTHORIZED`, so a legitimately
discharged demand could never satisfy the tuple the branch existed to accommodate — the mirror image of
an assertion that can never fail, and the only one of the evening's instances that CI caught rather than
a seat. One case reddened when `BADF-DEM-0087` was discharged (#224); **all 67 would have** when #220's
derived terminality lands, which was a hard sequencing dependency now removed.

The fix recomputes the demand **at the record's `measured_on`**, exactly what the generator read: the
comparison stays *exact* rather than being loosened to "`AUTHORIZED` or any terminal state", which would
have kept the light green by proving less — a demand that reached terminal *wrongly* would have passed.
It also restores the module's own convention: the sibling case classes all recompute at a pinned
revision via `show(c["landed_as"], …)`; this one had skipped it. One durable live assertion remains,
chosen because no legitimate lifecycle transition can break it: a demand recorded as human-authorized
must still record a human principal.

**The record was not re-measured.** `examples/build-shadow-evidence.json` is byte-identical. Editing a
frozen measurement so that today's tests pass would falsify the measurement — the standing rule when a
shadow and the present disagree is that the *test* is wrong, or the present is, and never that the past
should be rewritten. #220's derived-terminality work must not reach for that green either.
## A guard that went quiet when its subject disappeared (`BADF-WP-0112`, Issue #229 / GOV-0099)

The family-name guard shipped two work packages earlier (`WP-2026-0109`) scanned `skills/badf-build/**`
by glob and asserted no `badf-*` token was unresolved. Move that directory aside and it reported
`Ran 1 test … OK` **in 0.000s** — absence of the surface was indistinguishable from a clean surface, and
the very defect it existed to catch would have vanished under a rename. It went quiet exactly when the
thing it protects stopped existing.

This is the tenth instance of the evening's class and the **second introduced while remediating** — it
was written to close a naming defect. The remedy is the idiom this repository **already carried**: `tests/test_badf_schema_drift.py:31` asserts non-emptiness of its glob-derived sets at module scope, with a comment naming this exact failure mode — found by BADF-REV while sweeping, and it reframes the fix from a design question into a consistency one. Copied rather than reinvented, and fired at import so it cannot be forgotten by whoever adds the next test. The scan must now prove it read
the router, the fourteen frozen references, and the family naming itself before anything is concluded
from an empty result. Verified by moving the surface aside — the probe that used to pass now fails with
`the surface's router is absent; the scan below would conclude nothing, quietly` — and by two further
vectors measured rather than assumed.

Two notes for whoever generalizes this. First, the class is **"an assertion over a collection derived
from a glob"**, not "an assertion inside a glob loop": BADF-REV's sweep for the in-loop shape missed
this instance precisely because it asserts on a derived dict, so a repo-wide detector must catch both or
it inherits the blind spot it is hunting. Second, the checklist that found it — *ask what a guard reports
when its input is missing; if the answer is "passes", it is not a guard* — now has a **clear as well as a
hit**: applied to the `badf-engineering-verification` modules it correctly found nothing, because those
already assert counts before iterating. A detection rule that has only ever fired is as suspect as a
guard that never does.

## badf-release-validation → IMPLEMENTED — the four G09 evidence contracts, typed (`BADF-WP-0113` / WP-VAL-B, Issue #233 / GOV-0103)

G09 named four evidence types and none of them had a schema, so a G09 dossier could carry any object
shape and the gate could not refuse a validation claim on its content. WP-VAL-A froze what those claims
**mean** (VAL-I01…VAL-I20) and shipped no enforcement, saying so in its own non-coverage: *"the contract
is frozen text plus a contract test — nothing at this rung proves a validation class can actually be
routed, observed or refused."* This rung closes that gap.

Four typed schemas specialize evidence for `quality-validation`, `security-validation`,
`performance-test` and `resilience-test` with a **closed** `binding`, and `check_g09_binding` — registered
over exactly those four types in `EVIDENCE_RULES`, mirroring VER-B's `check_g08_binding` — enforces the
invariants decidable on a single evidence object: one immutable candidate (**VAL-I01**); no agent as
producer, and no agent adjudicating its own success (**VAL-I04/I05** — an agent may *attempt* a journey,
the oracle sits outside it); no PASS on an unapproved runtime (**VAL-I04**); mandatory non-coverage
(**VAL-I15**); a non-production environment that declares its material deviations, so `staging PASS ≠
production proven` becomes recorded rather than forgotten (**VAL-I08**); a flake policy that retains
failed observations (**VAL-I16**); blocking findings preserved against a PASS (**VAL-I14**); thresholds
bound **before** the run began, because a bound fitted to the result is not conformance (**VAL-I06/I10**);
and resilience PASS only on observed recovery with verified integrity, never mere survival during
injection (**VAL-I11/I12**). Two refusals are structural rather than code: `residual_risk.acceptance.state`
has no bare `ACCEPTED` member, so a validator accepting its own risk is **unrepresentable** (**VAL-I09**,
the SEC-I12 pattern); and one class's payload cannot fill another's slot — measured as **two** structural floors, not one:
a wholesale swap is refused by `required` (the walker checks it *before* `additionalProperties`, so the
foreign keys are never reached), while `additionalProperties: false` is what refuses a single foreign key
smuggled into an otherwise-complete binding. Both are the floor under **VAL-I13**; an earlier draft named
only the second and was wrong about which one fires.

**Strictly additive.** A G09 evidence object with no `binding` passes through for all four types, exactly
as WP-2026-0010's historical dossier survived the G08 rung. Nothing was added to any existing schema's
`required`, no `additionalProperties` was tightened, and `repo` is green across the whole ledger.
**No `scripts/badf_release_validation.py`** — VAL-I20 holds at every rung, not only at A — and no
`lifecycle.json` change: G09 already named these four types; this rung types them and moves no ownership.
G09 stays `quality_authority`; G10 stays `release_authority`. The frozen contract is untouched: SKILL.md's
only edit is the frontmatter `status:` field, which had to move because the registry did — the skill file
and the registry must not disagree about the rung. That SKILL.md carries a hardcoded status at all is a
defect of its own class, the one `badf-engineering-verification`'s SKILL.md forbids in writing; it is filed
rather than fixed here.

**Nineteen control endpoints, each demonstrated load-bearing by mutation** (neuter the `raise`, the suite
notices; 19/19 killed, no survivors). The first mutation pass, run in a throwaway worktree *before this
branch existed*, found one survivor: VAL-I12's "PASS with an **empty** `integrity_checks` list" had no
test — `observed: false` and a `FAIL` check were covered, the empty array was not, and it is structurally
valid because the walker ignores `minItems`. That control could have been deleted under a green suite.
The missing test was added before the branch was cut. **A green suite is not evidence that a control is
load-bearing**; only mutation is.

**Declared non-coverage, carried into review rather than left to be found:** the fixtures are
author-written, so *"the control fires"* and *"the control fires on anything real"* are separable claims
and only the first is within an author's reach — the same shape as VER-D's representative-shadow
non-coverage. There is no real G09 dossier in this repo to test against. BADF-QA attacks the second with
fixtures built from landed evidence and near-miss mutations an author would not write; BADF-REV checks
that no refusal is unreachable by construction. Dossier-level controls — cross-class candidate identity
and class substitution beyond the structural floor — are **WP-VAL-C**.

## Scope containment made two-sided — a declared surface that matches nothing is named and refused (`BADF-WP-0116`, Issue #232 / GOV-0102)

C3 computed containment in one direction only: for each **changed** path, is it declared. No pass asked
the inverse — did each declared pattern match anything the work changed. That asymmetry was not cosmetic,
because `expected_surfaces.files` is simultaneously the surface C3 checks and the **ceiling C7 enforces
on delegations** (BLD-I10): a declaration could be arbitrarily wide, both controls stayed green, and every
extra pattern handed a delegate real authority over paths the work never needed. The gap had a live
instance before the fix landed: `WP-2026-0111`'s landed record declares
`work/WP-2026-0109/work-package.json`, which the landed diff `66c92f8` never touched — the reconcile
target moved across a night of rebases and nothing flagged the stale declaration (measured on #232).

The fix is the mirror of the existing loop, at the two sites that already own the one-sided halves.
Assembly computes the declared `files` patterns that matched no changed path and, when any exist, adds an
OPEN Major condition and a `held_because` line naming them. `check_g07_binding` refuses a **PASS**
source-change whose record declares a pattern matching nothing in `binding.changed_paths` — recomputed at
check time from the record and the equality-bound binding, never stored, so there is nothing for a forged
binding to omit and no schema change (the binding stays `additionalProperties: false`).

The design question the issue deferred resolves through the schema that already existed: **`files` is
must-touch** (it is the C7 ceiling, so an entry is authority, and unexercised authority is pruned);
**`discovery_allowance` is may-touch** and exempt from the mirror by construction — a pattern that is
*supposed* to match nothing in the ordinary case belongs there, and it never widens C7 (C7 reads `files`
only). Corollary: never declare the work package's own `work/<WP>/` directory or the lockfile in `files`
— both are excluded from the governed diff, so the pattern can never match.

**Not covered, stated:** C7 grants a delegation mid-flight against the declared ceiling, before `actual`
exists — an over-broad grant can live transiently inside a work package that never reaches PASS. Binding
that would need delegation-time knowledge of the future; it becomes design work if delegations ever carry
it. **Not done, deliberately:** `WP-2026-0111`'s landed record was not amended — it is historical, carries
no delegations, and rewriting a landed record to satisfy today's control is the same falsification the
`BADF-WP-0111` section above refuses. The instance is reported on #232; the control binds from here
forward. Red-first: the two positive controls failed against the one-sided gate before the fix (5 ran,
2 failures); mutation: each new branch neutered turns its test red (2/2 killed).

## badf-uat — G10 business-acceptance router freeze (`BADF-WP-0115` / WP-UAT-A, Issue #239 / GOV-0107)

`badf-uat` is frozen (DESIGNED) as the **G10 business-acceptance capability**, and its whole reason to
exist is one distinction: technical E2E verification proves the system did not crash; UAT proves the
observed behavior satisfies the business outcome a PRD's acceptance criteria approved. It produces
**exactly one** of G10's four evidence types — `uat` — never `release-packet` or
`operational-readiness` (`badf-production-readiness`, Issue #237 / GOV-0105) and never `go-no-go`
(`release_authority`'s own act, human-reserved in `badf/authority-matrix.json`). Discovered as a real
gap independently of this freeze (Issue #238 / GOV-0106: `uat` was a required G10 evidence type with no
producing capability) and filed separately rather than folded silently into either freeze.

The chain it walks: `schemas/prd.schema.json` → `schemas/acceptance-criteria.schema.json` →
`schemas/requirements.schema.json`, resolved through `schemas/traceability.schema.json`'s existing
`requirement_to_objective` and `criterion_to_requirement` link maps — this skill **resolves that chain,
it does not rebuild it**, the same "resolve, don't reperform" discipline `badf-release-validation` holds
at G09. The one leaf it adds is the UAT Scenario: business-readable, adapter-independent (UAT-I02), with
execution adapters (browser/API/manual/hybrid) as pure observers — **none registered as a subskill at
this rung**, the over-engineering risk this WP explicitly refused per its own Stage-Gate note. An
eight-stage workflow (`RESOLVE ACCEPTANCE BASIS → DERIVE SCENARIOS → SELECT ADAPTER → EXECUTE →
CLASSIFY DEFECTS → COMPUTE COVERAGE → PACKAGE RECOMMENDATION → HANDOFF TO HUMAN ACCEPTANCE`) and
fourteen references carry twenty frozen invariants, UAT-I01…UAT-I20: business/exact-candidate/exact-basis
provenance (I01/I04/I05), scenario ≠ procedure and technical-E2E ≠ UAT (I02/I03), business-readable
oracle with diagnostics as supplement not substitute (I06/I10), representative actor and context
(I07/I08), tool output as observation only (I09), a ten-way explicit defect taxonomy where
`ACCEPTANCE_CRITERION_DEFECT` routes upstream rather than being silently absorbed as an implementation
bug (I11), mandatory non-coverage and criticality-aware completion — a critical FAIL cannot hide inside
an aggregate pass percentage (I12/I13), the two-layer artifact separating this skill's *recommendation*
from a separate human's *acceptance* (I14/I15/I16, the same "the evidence-producer cannot also be the
decider" principle SEC-I13 and VER-I18 already hold), candidate-change staleness with extend-only
superseded records (I17), and UAT ≠ go-no-go ≠ deployment (I18/I19). No competing
`scripts/badf_uat.py`, no typed schema, no `lifecycle.json` change at this rung (I20). External source
`webapp-uat` (Playwright-based) is confirmed absent from this repository; its execution mechanics are
adapt-candidate material for a later adapter WP, its definition of "done" is explicitly rejected as this
skill's definition of "accepted". Ladder-internal at this rung (SKILL + 14 references, registry
`badf-uat: DESIGNED`, no gate/schema/lifecycle change); WP-UAT-B (typed schemas) and WP-UAT-C
(deterministic controls, lean disabled — these are HARD INVARIANTS) are shared-surface and go to
BADF-QA + BADF-REV. Authored by BARCHI-3 as Senior ARCH & ENGIN, on the operator's explicit directive to
proceed `badf-uat` then `badf-production-readiness`.

## badf-production-readiness — G10 readiness aggregator freeze (`BADF-WP-0114` / WP-PRDY-A, Issue #237 / GOV-0105)

`badf-production-readiness` is frozen (DESIGNED) as the **G10 readiness aggregator**, and the governance
correction that shaped it is the whole design: it **produces the evidence basis for production
authorization; it does not issue `PRODUCTION_AUTHORIZED`.** It owns two of G10's four evidence types —
`release-packet` and `operational-readiness` — never `uat` (`badf-uat`, Issue #239 / GOV-0107) and never
`go-no-go` (`release_authority`'s own act, human-reserved in `badf/authority-matrix.json`). With
`badf-uat` landing alongside it, G10's four types now split three ways by construction rather than by
convention.

Three fundamental rules carry the capability. **AGGREGATION NOT RE-EXECUTION** (PRDY-I01): readiness
*resolves and evaluates* upstream evidence and never re-performs the owning discipline — a readiness
skill that re-runs G09's validation has become a second validator with none of G09's independence,
oracles or execution identity, and its result would then need validating by something else. The
reference carries an explicit MAY / MUST NOT list. **READINESS ≠ AUTHORIZATION** (PRDY-I19): the
strongest positive conclusion the skill can reach is `READY_FOR_AUTHORITY`, a recommendation and an
input to a decision. **PRODUCTION_AUTHORIZED IS DERIVED, NEVER WRITTEN**: it is a predicate over valid
evidence *plus* valid authority bound to exact candidate, environment, rollout scope, conditions and
validity window (PRDY-I20) — never a hand-written field, because a hand-written boolean can be `true`
while any conjunct is false and nothing downstream can tell.

Twenty-four invariants **PRDY-I01…I24**, frozen verbatim from the operator's design: exact-candidate
binding across source/composed-tree/artifact/SBOM/provenance/config/migration digests (I02/I18/I23),
previous-release delta with *no diff ≠ ready* (I03), evidence provenance (I04), freshness earning **no
credit rather than reduced credit** (I05), contradiction yielding `NOT_READY` or `INDETERMINATE` with
synthesis forbidden from choosing the favorable claim (I06), product acceptance irreplaceable by
technical validation (I07), security validation irreplaceable by a green suite and residual risk never
self-accepted (I08/I09), performance bound to predeclared budgets (I10), backup ≠ restore and recovery
observed not planned (I11/I12), rollback `DEFINED/VALIDATED/REHEARSED` reconciled with migration
compatibility in one reference because the two constrain each other (I13/I14), observability binding the
full `signal → query → threshold → alert → owner → action` chain (I15), operations and support ownership
(I16/I17), the same-artifact rule against per-environment rebuild (I18), and the three gate separations
G10 ≠ G11 ≠ G12 (I21/I22). The authority boundary cites **SEC-I13**, **VER-I18** and **UAT-I14/I15** as
precedent rather than novelty, and states the generalization across all four: *the capability that
produces the evidence is never the capability that decides progression.* The narrow wording is
load-bearing — an earlier draft said "never the capability that makes it", which is false of every
capability in the list, since each makes real routing, classification or evaluation judgments. The
boundary is who owns the act that **advances the lifecycle**, not who makes any decision at all.

Sixteen references; no `scripts/badf_production_readiness.py`, no schema, no `lifecycle.json` change, no
`badf_gate.py` change (PRDY-I24). External sources are **ADAPT / EXTEND / REJECT** with the honest
caveat declared in the reference itself: `final-release-review`'s delta matrix is adapted and its local
`GREEN LIGHT TO SHIP` authority rejected; the reviewed readiness skill's dimension decomposition is
adapted, extended with owning-gate binding and with the `STALE`/`INDETERMINATE` states it lacks, and its
own approval decision rejected — and **both sources were characterized from the operator's directive
rather than independently fetched**, stated in `external-methodology.md` rather than implied. Ladder-
internal at this rung; WP-PRDY-B (typed schemas) and WP-PRDY-C (deterministic controls, **lean disabled
— HARD INVARIANTS**) are shared-surface and go to BADF-QA + BADF-REV. Registry
`badf-production-readiness: DESIGNED`. Authored by BARCHI-3 as Senior ARCH & ENGIN.

## The id-allocation protocol — six surfaces, one binding mechanism (`BADF-WP-0118`, Issue #227 / GOV-0098)

Five id incidents in 48 hours — three live collisions (the third-actor `WP-2026-0073` poisoning; the
`WP-2026-0110`/`BADF-DEM-0097` double-claim bound only in an unlanded PR tree; the `WP-2026-0113`/
`BADF-DEM-0100` claim published only in an issue body) and two seat-sweep defects (a title-blind sweep;
a `DEM-00xx` regex structurally unable to match ids ≥ 0100) — established that the sweep convention,
scattered across issue threads, does not survive contact with concurrent seats. This section replaces it.

**The surfaces are six.** ① the landed ledgers (`work/`, `badf/demands/`) · ② remote branch heads ·
③ open-PR file lists · ④ issue/PR **bodies** · ⑤ the shared clone’s `git worktree list` · ⑥ the negative
one: an **independent clone is invisible to all of the above** — no seventh sweep closes it. The
conclusion runs the other way: **the published issue claim is the binding mechanism.** Sweeps bound the
risk; publishing binds. Measure, ask the seats (the only instrument that sees unpushed work), publish
the claim on an issue, and only then bind ids into any artifact.

**`scripts/badf_id_sweep.py` mechanizes the remote-visible half.** Deterministic and offline (CI has no
network; a sweep that silently degrades when `gh` fails reports clean scans it never ran), it reads four
dump files from `--from-dir` and encodes four properties as structure: claims are only what claim-shaped
surfaces show (ledger paths, branch refs, PR file lists), each **named with its source**; body strings
are **MENTIONS**, surfaced for reading and never folded into next-free — prose may *carry* a binding
claim, which is exactly why a human reads it rather than a regex trusting it; the sentinel exclusions
(`0997`–`0999` fixtures, `9999` sanctioned; `0900` deliberately absent — cited once, retracted as
unverified) are printed, never silent; and the run **refuses to report unless it can see the
known-present anchors** — an empty scan and a clean scan are otherwise identical output. Every report
ends with the non-coverage trailer naming surfaces ⑤ and ⑥. Producing the dumps:

```bash
D=$(mktemp -d)
{ ls work/; ls badf/demands/; } > $D/ledger.txt
git ls-remote --heads origin > $D/branches.txt
for pr in $(gh pr list --state open --json number --jq '.[].number'); do
  gh api repos/bstBizEra/badf/pulls/$pr/files --jq '.[].filename'; done > $D/pr_files.txt
gh api -X GET search/issues -f q='repo:bstBizEra/badf "WP-2026"' --jq '.items[].body' > $D/bodies.txt
for n in $(gh issue list --state open --json number --jq '.[].number'); do
  gh api repos/bstBizEra/badf/issues/$n/comments --jq '.[].body'; done > $D/comments.txt
python3 scripts/badf_id_sweep.py --from-dir $D
```

**The comment surface is where the binding claims actually live** (#282, after four allocation
incidents in one session): provide `comments.txt` and the sweep warns by name on any comment id at or
above the computed next-free — never folding it into the count (#199 stands) and never dropping it.
When the dump is not provided, the run says so in its SURFACES header: an unread surface stated is a
caution; omitted, a false clean.

**GitHub search is a tokenizer, not a grepper**: it returns fuzzy hits, so any body-search result is
verified by literal grep before it is believed (four false positives in one allocation tonight).
GOV ids have no file-backed claim surface at all — the tool reports them as prose-derived observations,
labelled as such, and GOV allocation always requires reading.

## An identifier that resolved to another seat's work (`BADF-WP-0119`, Issue #235 / GOV-0104)

The section above documenting the build shadow's authority case was filed under **`BADF-WP-0110`**. That work
shipped as **`WP-2026-0111`** (#228); `WP-2026-0110` is BARCHI-3's G08 close-out (#224). Residue from a
renumber: when the id moved after an id collision, the machine-readable surfaces were corrected — the work
package record, the demand, the issue body, the PR title — and the **prose heading was not**, because prose
reads as commentary rather than as the durable record it is.

**Dangling is the benign half.** While `WP-2026-0110` did not exist, the reference merely resolved to nothing.
Once #224 landed under that id, it began resolving to **real but unrelated work** — a strictly worse failure,
because a wrong answer is indistinguishable from a right one at the point of reading.

**It propagated before it was fixed.** `WP-2026-0116` (#249) read the mislabelled heading and wrote a fresh
cross-reference to *"the `BADF-WP-0110` section above"* at line 1754 — new doctrine inheriting the wrong id
from old doctrine. This is what "the cost grows with time" means concretely: not that the error becomes
harder to fix, but that it **reproduces into surfaces written after it**, each copy carrying the same
authority as the original.

**What was deliberately not corrected**, and the reasoning matters more than the edit: `BADF-DEM-0098.json`
contains the same stale id inside its `problem` field, and it stays. That field is a frozen export whose
`source.body_digest` is `sha256(problem)` — verified, not assumed. The snapshot is *correct*: issue #225
really did say `WP-2026-0110` at export time. Editing a record of the past so that it agrees with the present
destroys the binding that makes it evidence, to make a cosmetic id consistent. The same refusal the
`BADF-WP-0111` section above records for `examples/build-shadow-evidence.json`.

Anyone sweeping for the stale id will hit that demand and be tempted. **The temptation is the trap.**

## The AET runtime contract frozen — doctrine gets guards, and authority stays where it lives (`BADF-WP-0122` / AET-A, Issue #236)

The Agentic Engineer Team program opened the way this repository opens everything: freeze the contract
before building the runtime. `docs/14-agentic-engineer-team.md` now declares the four planes, six
persistent seats, routing rules, invariants `AET-I01`–`AET-I13`, the durable-effect contract with its
five outcome classes, budgets/stop codes, the `badf init` subset invariant, and rungs `AET-B`–`AET-E`
**defined and gated, not built** — `AET-B` behind P1-before-P3 and the #246 ratchet, `AET-E` behind a
human-reserved authorization in the operator's own channel. The contract grants no authority and holds
no copies: the reserved-role list stays in `badf/authority-matrix.json`, pointed at, never restated —
on the one document where a drifted copy would *become* authority.

Two structural choices worth naming. The AET is deliberately **not** a skill-registry entry — it is
operating doctrine for seats, not a routed capability, and staying off the most-contended shared
surface is the D4 lesson practiced. And the doctrine ships with **content-anchor guards**
(`tests/test_badf_aet_contract.py`, red-observed before the document existed, gut-tested by mutation):
after #216/#230/#235, a normative document without guards is a claim nobody re-measures.

`AET-I13` (channel-bound authorization) was earned during this WP's own drafting: a ratification
relayed from one session cannot release a hold committed in another — a seat correctly refused exactly
that, the D3 record on #236 was corrected, and the invariant now freezes what the episode proved. In
the same hours, the id claim for this WP survived a crossed-ids misread (caught at ask-time by the
print-the-ceiling rule) — the allocation protocol landing in `BADF-WP-0118` doing its job on the very
next WP to allocate.

## badf-uat → IMPLEMENTED — the typed `uat` binding, and an enum that cannot say yes (`BADF-WP-0124` / WP-UAT-B, Issue #263 / GOV-0116)

Rung A froze `badf-uat`'s contract and shipped **no runtime**, which left `uat` — a required G10
evidence type — checkable by nothing. This rung types the artifact and extends the canonical gate:
`schemas/uat.schema.json` specializing `evidence.schema.json`, and `check_g10_uat_binding` registered
`EVIDENCE_RULES["uat"]`. **Strictly additive**, exactly as VER-B and VAL-B before it — an untyped
`uat` binding stays admissible, so nothing already landed breaks.

**The load-bearing decision is a closed enum.** UAT-I14 says the capability that produced the evidence
does not issue the decision. Rung A stated that in prose across fourteen references; a schema admitting
`recommendation: "ACCEPTED"` would have defeated it with a permissive vocabulary rather than an
argument — a producer would not need to disobey the rule, only decline to read it. So
`recommendation` is exactly four `RECOMMEND_*` values, the acceptance verdicts exist **only** inside
the optional Layer 2 `acceptance` object, and that object pins `accepted_by.principal_type` to
`const: "human"`. **An agent cannot issue product acceptance by any encoding this schema admits.**
The rule stopped being a norm and became a shape.

Five code controls carry the cross-field constraints the schema walker cannot express: an observation
naming a scenario absent from the binding is unanchored (U2, UAT-I01); a `FAIL`/`BLOCKED` observation
with no classified defect is noise the disposition cannot act on (U3, UAT-I11); `RECOMMEND_ACCEPT`
with a critical scenario not passing is refused, so an aggregate cannot bury a mandatory criterion
(U4, UAT-I13); and a Layer 2 acceptance must bind this binding's own candidate digest and carry a
human principal (U5, UAT-I15/I16). All five **observed red** against a neutered gate.

**A sixth control was written and removed, and the removal is the instructive part.** `U1` checked
that `acceptance_basis` carries a `prd_digest` — but the schema already makes that field `required`,
so `check_schema` refuses first and `U1` could never fire. Its test passed **on the wrong raise**,
because both messages contain the string `prd_digest`. The mutation battery caught it: neutering `U1`
left the suite green. **A control the schema makes unreachable is not a control; it is the shape of
one** — #250's class, found by this rung's own battery in this rung's own code, and recorded in a
comment where it stood so nobody re-adds it.

Shared-surface (`schemas/` + `badf_gate.py`) → QA + REV, unlike rung A. Next: **WP-UAT-C**,
deterministic G10/UAT controls with lean **disabled** — acceptance-basis binding across a dossier,
freshness, and staleness on candidate change are HARD INVARIANTS.

## A verdict that contradicted the findings it cited (`BADF-WP-0123`, Issue #211 / GOV)

`validate_verification_record` checked coherence at the **matrix** layer — a `VERIFIED` row over an OPEN
blocking finding is refused — and `check_g08_binding` checked it on an independent-review **evidence
binding** (`badf_gate.py:1742`). The record's own **ballot** layer was unchecked, so flipping the PR-196
record's verdict `REJECT → APPROVE` while it cited an OPEN `MAJOR` it had raised itself rendered
`BADF VERIFY PASS`. Two layers guarded the property and the one in between did not.

**The blast radius was already bounded and that is why this was deferred, not urgent:** the record grants
no verification authority, a `VERIFIED` matrix row over an OPEN MAJOR is refused, and C6 refuses an OPEN
MAJOR passed over at dossier level. The defect was never that an incoherent ballot could become authority.
It was that **the artifact future tooling reads could carry a self-contradiction**, and a downstream reader
has no way to know the verdict and the findings disagree.

**Strict `APPROVE` only — and the codebase settled that, not judgement.** The instinct was to refuse
`APPROVE_WITH_CONDITIONS` over an open finding too, treating every one as unmapped-by-construction since
the schema has no condition structure. `tests/test_badf_verification_evidence.py`'s baseline fixture is
*exactly that shape* — `APPROVE_WITH_CONDITIONS` citing an OPEN `MAJOR` — and an existing test asserts it
**passes**. A conditional approval over an open finding is the designed arc; refusing it would have broken
a test that encodes the intent and called the breakage a fix. It also matches the sibling control, which
tests `verdict == "APPROVE"` and nothing else. **Both layers now refuse the same shape and no more.**

**A filed acceptance criterion was found unbuildable and the deviation was published before review.** The
issue asked for `APPROVE_WITH_CONDITIONS` to be permitted "only with the finding condition-mapped,
mirroring C6". Measured: the record schema carries **no** condition key, and **0 of 5** encoded records use
that verdict. Mirroring C6 would require inventing a schema field — which the issue's own scope forbids
("additive refusal only") and which would be a schema change on zero instances. Stating that on the issue
*before* the review round is the difference between a plan defect and a review finding.

**The control is watched.** Neutering the new `raise` turns the owning module red. That is asserted because
**#250 exists precisely because `check_g07_binding` accumulated correct controls nothing was watching** —
adding an unwatched control while claiming to fix that class would have grown the pile.

## A declared future family, not an apologetic typo (`BADF-WP-0120`, Issue #223)

`badf-solution-design`'s routing table sent the security threat / risk decision row to
**`badf-security`** — a family that has never been in the registry — while **`badf-security-design` is
`ACTIVE`** and owns exactly that concern. A reader following the table deferred a decision that was
routable today. The row now names the family that owns it, and the stale *future* is gone.

The interesting part is the guard. `BADF-WP-0109` added a family-name guard over `skills/badf-build/**`;
generalizing it across every family surface surfaced two unresolved tokens, only one of which is a
defect. The other — `badf-security-assurance` — is a deliberate forward reference, named before it is
built so that `badf-security-design` can route assurance concerns *away* from itself rather than absorb
them (SEC-I14).

**#223 originally proposed permitting an unresolved token when the same surface labels it "named, not
built" at that use. That criterion is backwards on this repository's data, measured before it was
built:**

| token | uses | labelled at the use | bare |
| :--- | ---: | ---: | ---: |
| `badf-security-assurance` — legitimate | 17 | 14 | **3** |
| `badf-security` — **the defect** | 1 | **1** | 0 |

The defect reads `future **badf-security**`, so it *satisfies* the label check; three legitimate uses are
bare on their line. A guard built to that criterion would admit the one thing the issue exists to catch
and refuse three things it must not. **"Carries a declared-future label" is a proxy for "is a
deliberately declared future family", and a typo satisfies the proxy simply by being written
apologetically** — the same proxy-for-property shape as the vacuity findings, one layer up.

So the exception surface is **governed rather than inferred**: a top-level `declared_future_families`
list in `badf/skill-registry.json`, already the authoritative surface for family names, digest-pinned and
lockfile-covered. The guard reads a governed artifact and asserts nothing of its own. **Controls narrow
the list-becomes-a-hole risk without closing it**: an entry must carry `declared_by` (resolvable in the
tree, not merely present), `gate` and a non-empty `reason`, and a declared name that **no surface
references** is refused as dead permission. What they cannot catch — measured, not conceded — is a typo
introduced *together with* its listing in the same edit: that shape satisfies every property, and no
mechanism closes it without a worse proxy (a similarity threshold would be calibrated on a list with one
legitimate member, and no threshold separates the legitimate forward reference at 0.744 from the original
defect at 0.788). **The same-edit case is caught by review of the digest-pinned registry edit — review
does that work, not the guard** — which is still the real improvement: the bar moved from a word in prose
to a governed edit under review. Adding the key is
schema-additive — there is no registry schema, and `verify_registry_digests` iterates only
`registry["skills"]`, so no per-family digest moves.

**What this rung does not do:** it establishes one declaration surface with one member. The general
question — what a gate should do when an *optional* enforcement input is absent, of which an undeclared
future family is the fourth instance beside C3's `expected_surfaces`, C7's delegation ceiling and GIT-F's
composition record — is deferred to that class's single answer, because answering them one at a time
would produce inconsistent answers.

**The guard proved itself mid-build.** `badf-uat` landed while this WP was open, and the generalized scan
immediately found a third unresolved token on the new surface — `badf-production-readiness`, three uses in
`skills/badf-uat/SKILL.md`, routing `release-packet` and `operational-readiness` away from `badf-uat`
rather than claiming them. A legitimate forward reference, and now the list's second member (UAT-I14 /
#237). That also produced the list's first **discharge**: PR #245 registers that family, and a name may
not be both registered and declared-future — so whichever lands second deletes the entry, enforced by a
test rather than remembered, with the instruction written into the entry's own `reason` field because a
condition living in chat does not outlive the session holding it.

**And the first discharge happened before this rung even landed.** `badf-production-readiness` was added as a
second member when `badf-uat` landed mid-build; then PR #245 registered that family, and a name may not be
both registered and declared-future — so the entry was removed here. The list is back to one member, and it
shrank because a family got *built*, which is exactly the property that keeps it from decaying into a
permanent allowlist. The instruction that made that happen lived in the entry's own `reason` field rather
than in a message, and was read in place.

**Known and uncovered:** `GOV-0102`'s own doctrine says *"unexercised authority is pruned"*, which is the right
remedy when a declaration is over-broad and the **wrong** one when the declaration is correct and the content
went missing — both emit a byte-identical condition. That gap is filed as **#257 / GOV-0113** and is not fixed
here: this rung's subject is family names, and editing the same file is not sharing the subject.

<<<<<<< HEAD
## badf-uat → deterministic G10 controls — a defence that names a field must require the field (`BADF-WP-0125` / WP-UAT-C, Issue #273 / GOV-0120)

**Lean mode DISABLED.** These are HARD INVARIANTS, the same tier as the G08 controls at VER-C.

At rung B, `U4` refuses a critical scenario failure only under `RECOMMEND_ACCEPT`. That boundary
was defended — by its own author, in the PR — on the grounds that *conditions are exactly where a
known critical failure gets named.* BADF-QA agreed the **rationale** and demonstrated it was
**enforced by nothing**: `conditions`, `known_defects_acknowledged` and
`declared_non_coverage_acknowledged` are all optional, so a disposition whose **name asserts
conditions exist** required none — and UAT-I13's aggregate-burying was reachable **one enum value
over** from a control that read as complete.

**The repair enforces the precondition rather than withdrawing the judgement**, and that is the
transferable part: *a defence that names a field is a defence that the field must be non-empty.*
An argument for why a gap is acceptable is only as good as the thing it points at.

```
C7   RECOMMEND_ACCEPT_WITH_CONDITIONS + a not-passing critical named in no condition
     and no acknowledged defect                                    -> refused   (UAT-I13)
C8   disposition ACCEPTED_WITH_CONDITIONS with no conditions       -> refused   (UAT-I16)
C9   unconditional ACCEPTED over an unacknowledged not-passing
     critical                                                      -> refused   (UAT-I16)
C10  acceptance.scenario_set_digest != a digest recomputed over the
     scenarios actually carried                                    -> refused   (UAT-I17)
C11  a criterion not_covered with neither a reason nor a declared
     non_coverage entry                                            -> refused   (UAT-I12)
```

**C9 draws the line where it belongs:** a human **may** accept a known critical failure — that is
their authority, and BADF does not second-guess it. Acknowledging it is what makes it *known*.

**C10 converts an invariant into a mechanism.** UAT-I17 says a material change invalidates an
acceptance; until this rung that was prose in a reference. Recomputing the scenario-set digest
means a scenario added or removed after an acceptance was issued **cannot carry that acceptance
forward silently**. The prose stayed the same; what changed is that something now checks it.

Additive as B established — an untyped binding is still admissible, asserted. **Provenance stated
per control**, because the rung is deliberately wider than the issue that prompted it: C7–C9 are
#266's three criteria and close it fully; C10 and C11 come from the A-rung ladder's own C-rung text
and BADF-QA's routed coverage-exactness note.

**Every control mutation-checked individually — 0 survivors, 0 without an in-process liveness
witness.** Worth recording that the battery's *first* run parsed **3 of 24 tests** and reported a
clean-looking `survivors: 5`: `unittest -v` splits a docstringed test's verdict onto a second line,
and the parser required both on one. Read as evidence it would have filed a false
unwatched-controls finding against correct code. **The negative control's own printed count caught
it**, which is why the battery now asserts that its parsed count equals the module-declared count
and exits before measuring on a mismatch — *every stage of a measurement chain needs its own
liveness witness, including the stage that reads the others.*
=======
## badf-uat → SHADOWED — representative calibration, and the gaps it declares (`BADF-WP-0131` / WP-UAT-D, Issue #277 / GOV-0124)

`SHADOWED` means the controls were run against cases and behaved. `badf-uat` has **no real G10 evidence
at all** — measured on `main`: **0** G10 dossiers ever assembled, **0** landed `uat` evidence, against 91
`gate-dossier.G07`. BADF builds itself and has no product-acceptance event, exactly as
`badf-security-design` had no threat surface (#166) and `badf-solution-design` no solution matrices
(#145). So the shadow is **REPRESENTATIVE** (`PRD-SHADOW-CHECKOUT`) and `references/shadow-evidence.md`
says so in its first section; the real re-shadow is owed and filed as **#291**, whose trigger is
**mechanical** rather than prose — a live scan asserting no G10 dossier exists, red the day one lands.

**Two shapes were refused before this one**, and the distinction is the reusable part: an **empty-corpus**
shadow is *vacuous* (zero cases exercised is zero discrimination — a broken control and a correct one go
identically green), and shadowing `uat` over the 91 G07 dossiers is the *proxy* class (different gate,
different semantics). What separates them from this one is **vacuity gap vs realism gap**: a run that
*cannot* fail is disqualifying; a run that drives every control and *can* fail, but only on encodings
someone imagined, is what a declared caveat plus a live trigger exists for. The empty-corpus option was
this author's own filed plan, and was the weaker instrument wearing the honest label.

The calibration drives **all eleven** `check_g10_uat_binding` controls — each observed **red against its
own message fragment**, never a bare exit code, because passing on the wrong raise is how a control
acquires a test that does not test it. The case count is asserted equal to the `ValidationError` sites
read from the live gate **by AST**, so a control added later without a shadow case fails rather than going
quietly unshadowed. **All ten `defect_class` values are injected**, the class set read from the schema
enum rather than written down. A **rejecting** run (critical `FAIL`, classified defect,
`RECOMMEND_REJECT`, no acceptance object) is **admitted** — the gate refuses malformed evidence, never an
unfavourable result, a property a shadow of only-accepted runs could not show.

**And it declares four defect shapes no control catches** — `coverage-contradicts-observation` (a
criterion marked `covered_pass` while its own scenario's observation is `FAIL`), `scenario-dropped-entirely`,
`critical-not-executed-unclassified`, `defect-statement-empty` — each asserted **admitted** and asserted
**declared in the non-coverage section**, the check scoped to that section rather than to the document,
because a substring found anywhere is not a declaration. SARCHI's #270 addition asked for **one** such
case; the search found four, and declaring only the one asked for would have reproduced the very defect
the requirement exists to prevent.

Registry **`IMPLEMENTED` → `SHADOWED`** in one edit declaring **both** earned steps: `VALIDATED` was
earned at rung C and **the advance was omitted** — C's own pin comment set the status to the unadvanced
value and nothing flagged it, the co-edit-obligation-silently-unmet shape (#268's class), named here
rather than repaired silently. The standing fix is one line in the ladder — *each rung's PR advances the
registry status in the same change; a rung PR that does not is refused at review* — put in REV's path
rather than in a new checker. `acceptance.md` is amended **extend-only**: the frozen rung-A D text is
untouched, and the amendment records what D delivers and what defers to #291 (detection quality — a
property of a judgment a thin router with `allowed_tools: []` has no runtime to make).
`APPROVED`/`ACTIVE` remain the operator's admission decision at **WP-UAT-E**.

## badf-uat → ACTIVE — operator admission on a representative shadow, with two defects named (`BADF-WP-0136` / WP-UAT-E, Issue #310 / GOV-0136)

`ACTIVE` means the operator accepted WP-UAT-D's evidence. It does **not** mean the control path is
clean, and this section exists so a later reader cannot infer that it does.

**The evidence**: eleven G10 controls each observed **red against its own message fragment** — never a
bare exit code, because passing on the wrong raise is how a control acquires a test that does not test
it; ten `defect_class` values injected with the enum **read from the schema** rather than written down;
a **rejecting** run (critical `FAIL`, classified defect, `RECOMMEND_REJECT`) **admitted**, since the gate
refuses malformed evidence and never an unfavourable result; and two tripwires **verified able to fire**
rather than merely present. Precedent is `badf-solution-design` (#145) and `badf-security-design` (#166),
both admitted `ACTIVE` on representative corpora with the caveat stated and the real re-shadow deferred.

**Admitted with two OPEN defects in its own controls** — bugs, not declared coverage gaps, and the
distinction is the point: **#289** (C7/C9 match a scenario id by substring, so a critical failure named
only by a longer id passes as acknowledged) and **#293** (C8 admits `[""]`, a shape hole a matcher fix
does not touch). The operator was offered admission after #289 lands and chose admission with the
defects on the record; that choice is recorded rather than smoothed.

**Four adversarial cases no control catches** remain declared in `shadow-evidence.md`, led by
`coverage-contradicts-observation` — a criterion marked `covered_pass` while its own scenario's
observation is `FAIL` **is admitted today and nothing in eleven controls notices**. The
detection-quality half of the frozen D is deferred to **#291**, whose trigger is a live scan rather
than prose.

**What `ACTIVE` does not grant.** `UAT-I14`/`UAT-I15` hold at every rung including this one, and the
three facts that make that true — `allowed_tools == []`, a recommendation vocabulary that cannot
express an acceptance, and a Layer-2 acceptance pinned to `principal_type: human` — are now asserted
**together, as a property of the admitted state**, in
`test_active_grants_no_acceptance_authority`. Verified red-first in both directions: adding an
acceptance verb to the enum fails it, and granting a tool fails it. Registry status flip only;
**digest unchanged**, asserted.

## The enforcement-input ratchet — an optional input becomes loud, then mandatory (`BADF-WP-0126`, Issue #246 / GOV-0108)

The class, in BARCHI-3's sentence this WP exists to falsify: *a control whose input is optional is a
control that is off by default, and nothing says so.* `expected_surfaces` fed both C3 containment and
the C7 delegation ceiling, and 2 of 95 work packages had ever supplied it. Now: **every `repo` run
counts the coverage out loud** (`BADF SURFACE RATCHET: declared N/M; grandfathered undeclared G…`),
and **from `WP-2026-0126` forward the declaration is mandatory** — refused at self-dossier assembly
and RED in `validate_repo`, both naming the record, with the threshold being the very record that
shipped the ratchet. History below the threshold is grandfathered: counted at the point of judgment,
never edited. Sentinel ids (#199 / GOV-0085) are exempt by declaration, not by silence. A declaration
naming the record's own `work/` directory or the lockfile — both excluded from the governed diff by
construction — is refused as unmatchable: C7 authority attached to nothing (the VAL-B near-miss).

**The may-touch semantic, one sentence (#272 / GOV-0119, folded here by dependency):** `files` is
must-touch — the C7 ceiling, mirror-required; `discovery_allowance` is may-touch — never `unexpected`
at assembly, never refused at binding, never mirror-required, never widens C7. Before this WP the two
containment sites disagreed (assembly never consulted the allowance; binding exempted by it), so no
declaration was correct in both directions for a may-touch path. Assembly now consults the allowance
exactly as binding does; binding keeps its own filter because pre-unification bindings still carry
allowance-covered paths in `unexpected_paths`. Over-reach (changed-but-undeclared) and
over-declaration (declared-but-unmatched) remain **distinct** conditions with distinct counts — no
emitted number means two things (#257). `services`, `interfaces` and `data` remain schema-declared
with **zero consumers**: reserved, unconsumed, stated here so nobody discovers it — their enforcement
or removal is #240-lane work under the replay-first doctrine, not this WP's.

Five control branches, each red-observed by mutation; the sub-key × consumer matrix (measured on
#272 pre-build) re-verified post-change: no pair of consumers disagrees about any key.
>>>>>>> 1150843 (feat(gate): the enforcement-input ratchet -- expected_surfaces mandatory from WP-2026-0126, coverage counted, unmatchable refused, may-touch unified (WP-2026-0126))

## An optional governed route is not a route

`GOV-0118` (#271, `WP-2026-0127`). The verification record defines a justified path for each
way a finding can be weakened, and required none of them:

| Weakening | Governed path | The free route |
| :--- | :--- | :--- |
| withdraw a finding | `synthesis.withdrawn[]` — `finding_id`, `reason`, `by` | set `status: WITHDRAWN` directly |
| downgrade severity | `synthesis.downgraded[]` — `finding_id`, `from`, `to`, `decision_ref` | edit `severity` in place |

`VER-I12` — *synthesis cannot erase a finding* — is exactly what `withdrawn[]` protects, and it
was protecting nothing, because **the unjustified route was free while the justified one was
optional.** A route you may skip is not a route; it is a suggestion with a schema.

This is the *authority* form of the vacuity class this repo has been cataloguing: not a guard
that passes because its input is missing by accident, but a guard whose input is missing **by
permission**. It is the same shape as `GOV-0108`'s optional `expected_surfaces` — a control an
author can switch off by silence.

### Why it had to be closed with #267, not instead of it

#267 refused `APPROVE` over an OPEN blocking finding. That control is correct and it made this
gap **worse**: with the verdict side closed, editing the *finding* side became the path of least
resistance. A control that displaces a defect rather than removing it looks like progress on
the surface it guards and is invisible everywhere else. Closing the cheaper path is what turns
#267 from a redirection into a removal.

### The three refusals

1. **`status: WITHDRAWN` with no `synthesis.withdrawn` entry** — erasure without justification.
2. **A `synthesis.withdrawn` entry whose finding is still carried with another status** —
   justification without effect. `withdrawn[]` is the escape hatch for findings *not carried*;
   a record that both carries a finding open and claims it withdrawn contradicts itself.
3. **A `synthesis.downgraded` entry whose `to` differs from the finding's real severity** — the
   id-existence check alone let an entry name any `from`/`to` while the finding carried a third
   value. An entry that does not describe its finding justifies nothing.

Note that (1) and (2) are inverses, and only (1) was on the issue's list.

### Two gaps declared, not half-closed

The issue's own test list permits declaration as a disposition, and that is deliberate — a work
package that treated all four probes alike would either over-reach or stall.

- **`ACCEPTED_BY_AUTHORITY`** is a valid `status` with **no corroborating structure anywhere**:
  `authority` carries only `verification_authority`, so a finding may claim an authority accepted
  it while the record names no such authority. *Design needed:* an authority principal that must
  appear in `authority`, plus a `decision_ref` of the kind `downgraded` already carries. That is
  an architecture call — it decides what evidence *constitutes* acceptance — not an engineering one.

  > **Re-tested under GOV-0130 and it holds** — `authority` has exactly one property and one required
  > field, `verification_authority`; there is no `accepted_by`, `approver` or `principal` anywhere in
  > the schema. Recorded because the sibling declaration below it did *not* hold, and a correction
  > that fixes one claim while leaving its neighbour untested is the failure this repository keeps
  > paying for.
  >
  > **One caution on the suggested remedy:** `synthesis.downgraded[].decision_ref` is *required and
  > read by nothing* (#292). Modelling authority corroboration on it would copy a field whose
  > presence is enforced and whose referent is never resolved — compliance rather than evidence.
  > Whatever closes this needs the reference to **resolve**, not merely to exist.
- **A silent in-place severity edit** is undetectable today because nothing records the severity a
  finding was *first* reported at — "edited in place" and "reported at this severity" are
  byte-identical. Refusal 3 narrows this: an in-place edit **accompanied** by a `downgraded` entry
  is now caught. The residue is the edit that covers its tracks by writing nothing.

  *Design needed:* **which existing anchor carries prior severity, or whether a new field does.**

  > **Corrected (GOV-0130, measured on `9fad369`).** This said the edit was *"undetectable without a
  > baseline the record does not carry"*, needing *"the sealed input digest or an equivalent
  > anchor"*. **The record carries both candidates**, and the sentence sent a reader to build a
  > mechanism that already exists:
  >
  > - `target.sealed_input_digest` is **required** and cross-checked against `independence` and every
  >   ballot — but the gate **never computes it**, only compares it, and no `hashlib` site feeds it.
  >   **The checks seal the record against itself:** target, `independence` and every ballot may carry
  >   the same *wrong* value and all comparisons pass. It enforces internal consistency, not
  >   correspondence to anything outside the record — so it seals nothing against reality and
  >   **cannot** close this route. *(BADF-REV's statement of the mechanism, on #295.)*
  > - `findings[].baseline_ref` is **required** and referenced **zero** times by
  >   `validate_verification_record`. The only `baseline_ref` control belongs to
  >   `validate_architecture_assurance` — attributed by AST, because two record types carry the field
  >   and `grep` cannot separate them (the homonym trap, #292).
  >
  > Neither is missing. One is enforced but scoped to the review input rather than to severity; the
  > other is scoped correctly and unenforced. That is a much narrower question than *"invent a
  > baseline"*, and getting it wrong would have cost a builder the whole design.

> **One surface carrying the corrected claim is deliberately left uncorrected.**
> `badf/demands/BADF-DEM-0113.json` is a provenance export of issue #271's body at export time and
> is digest-sealed (`source.body_digest` recomputes over the stored `problem` text). Its function is
> to record **what was believed when it was exported**, wrong or not. Correcting it would break the
> digest and falsify the one artifact that exists to preserve the original. A sweep that corrects
> everything it finds is wrong on exactly one class of artifact — the class that exists to hold
> errors. Left as-is, deliberately, so the next sweep does not "fix" it.

### The route this change makes cheapest, found in review

**Found by BADF-REV on the PR that closed the routes above, by walking the whole `status` enum.** Recorded here because the section immediately above argues that #267 displaced weakeners onto the finding side — and this change displaces them again, one enum value over.

`findings[].status` has four values. #271 enumerated two of the three non-`OPEN` ones. The third:

```
APPROVE over the finding as-is (OPEN/MAJOR)   refused   #267's ballot control
APPROVE + flip OPEN -> WITHDRAWN              refused   refusal 1, above
APPROVE + flip OPEN -> RESOLVED               ADMITTED
```

`RESOLVED` buys exactly what `WITHDRAWN` used to: the finding leaves `OPEN`, the ballot control stops seeing a blocking finding, and a refused `APPROVE` becomes admissible. It has **no governed path, no corroboration, and no synthesis structure at all** — and after this change it is the *cheapest* of the three, because `WITHDRAWN` now requires an entry and `ACCEPTED_BY_AUTHORITY` is at least named as open.

That is the honest cost of closing a route without closing its class: **each closure promotes the next-cheapest bypass**, and only walking the enum finds it. Closing `RESOLVED` is a schema-gap decision like `ACCEPTED_BY_AUTHORITY` — resolution is the *normal, correct* outcome for a finding, so a refusal cannot simply forbid it; it needs a decision about what corroborates a resolution. Left open and declared, on #271's remainder.

**A related route, stated at its true reachability:** deleting a finding from `findings[]` outright is **refused** — an existing control catches a ballot that reported an id the record no longer carries. It is admitted only when the deletion is accompanied by a matching scrub of the ballot's `finding_ids`. Worth stating precisely, because "deletion is admitted" would imply a one-line bypass where the existing control in fact forces a coordinated two-place edit. Same class as the in-place edit, and equally unclosable without a baseline.

### Testing a control that another control masks

Every fixture here is **non-`APPROVE`**, on purpose. #267's ballot control refuses `APPROVE` over
an OPEN blocking finding *before* synthesis is examined, so an `APPROVE`-shaped probe would go red
whether or not this control existed — it would prove the masking, not the fix. When two controls
guard overlapping ground, **a test must fail for the reason it names**, which means fixtures that
the outer control lets through.

### Where the third refusal came from

QA observed, while probing #267, that all four of their own acceptance criteria for it had been
**confirm-shaped** — each asked *"does the thing I thought of work?"*, none asked *"what else
reaches the same proposition?"* — and that this is why the class survived into a control built to
their spec. Item 5 of #271's test list encodes that lesson as a requirement: *at least one probe
not derived from 1–4.*

This work package's first draft closed exactly the two gaps the issue listed, and stopped. Turning
QA's question back on it — *what else reaches "a finding weakened without the governed path"?* —
produced refusal 2, the inverse of the one probe that was listed. **The open-ended clause earned
its place on the first package that was made to answer it**, which is the argument for keeping it
on the next one.

## The seat roster — the runtime's first substrate artifact holds identity and nothing else (`BADF-WP-0130` / AET-B-1, Issue #287)

AET-B opened with a plan, a named adversarial challenge, and a rung that came out **smaller** than
planned — which is the challenge working. `badf/seats.json` now binds the operating seats to the
docs/14 §3 contract roles with charter provenance, the librarian vacancy stated out loud rather than
implied. **The roster holds identity and NOTHING else**, and the guard enumerates *both*
doctrine-declared shapes that must never land in it: a permission-shaped key forks
`badf/authority-matrix.json`; a time-shaped key pre-empts the #261-round decision docs/03's
time-window component requires. Both refusals run before the schema so the doctrine-declared shape
gets the doctrine-declared message — `AUTHORITY_CONFLICT`, and where the undecided half lives.

Delegations gain the **seat-field ratchet** (mandatory from `WP-2026-0130` forward, sentinels
exempt, the one grandfathered delegation counted at the point of judgment) and
**declaration-consistency**: a declared seat must exist in the roster — labeled as consistency of
what a session says about itself, NOT identity verification, which lands only when #261 gives seats
a structural referent. The full docs/03 authority tuple, each component with its home artifact:
**actor/role** → the roster (identity) and, post-#261, the structural actor field; **action +
target** → `badf/authority-matrix.json`; **environment** → the runbook/CI identity in evidence
bindings; **time window** → UNDECIDED, the #261-round question, deliberately homeless until ruled;
**work package** → `work/<WP>/`; **conditions** → the dossier. None lands in the roster silently —
the enumeration is the frame-check #270 demands, applied to the plan's own falsification line after
the challenge proved the original confirm-shaped.

Standing design law inherited by whoever eventually builds expiry (F3): the clock is an injected
input — the check compares stored-against-stored, never `datetime.now()` at the point of judgment,
so verdicts stay a function of the tree alone.

## Terminal is not established (AET-B-2, #294)

A durable effect's outcome vocabulary answers two different questions, and until
`WP-2026-0132` the gate had a name for only one of them.

**Terminal** means *this attempt concluded* — the run stops waiting on it.
**Established** means *the world changed* — the external side effect happened.

`TERMINAL_OUTCOMES` holds both kinds, and the difference is load-bearing:
`PROVEN_ABSENT` is terminal and **not** established, because proving an effect did not
happen is precisely the proof that retrying it is safe. The ledger's own tests already
encoded this (`test_proven_absent_effect_may_be_prepared_again`); nothing named it.

So `EFFECT_ESTABLISHED` = `{COMMITTED, SKIPPED_ALREADY_COMMITTED}` seals re-execution,
and `AFTER_ESTABLISHED_ALLOWED` = `{COMPENSATED, MANUAL_REMEDIATION}` keeps a real
effect compensable — an effect that happened must remain undoable and escalable, and a
rule that sealed it outright would be worse than the hole it closed.

**The general form, for whoever writes the next transition rule:** a criterion that says
"assert successors from the declared table" must name where that table IS. When it does
not exist, the criterion's true content is *invent one*, and the nearest constant whose
NAME resembles the property will be substituted for it. That is the adjacency class at
the level of a named set rather than a matcher, and the existing passing tests are
usually the table you are looking for.

**And the instrument:** a test that derives its cases from the constant under test can be
silenced by a mutation that empties that constant — the loop passes over nothing exactly
as it passes over everything. Pin the members the behavior requires, then walk the set,
then re-run the mutation to prove the guard bites.

## The authority check leaves a trace (AET-B-2, #294)

`AET-I05`'s phases are `PREPARE → AUTHORITY CHECK → COMMIT → RECONCILE`, but no outcome
recorded that the check ran, and `REJECTED` is ambiguous about which phase rejected on
whose authority. A phase that leaves no trace cannot be shown to have happened — and it
is invisible to any test that walks only the vocabulary that exists, which is why the
adversarial clause was pointed here first rather than spread evenly.

`AUTHORITY_CHECKED` is mandatory before `COMMITTED`, per effect, from `WP-2026-0132`
forward; earlier ledgers are grandfathered and sentinels exempt — the surface and seat
ratchet shape reused rather than a third mechanism invented. A check recorded for one
effect does not authorize another.

`badf init` was the first caller to meet it, and the disclosure matters: it recorded
`COMMITTED` for its intake with **no authority basis in the ledger at all**. It now
records what that basis actually is — the operator's invocation of the command — rather
than a check it never performed. Recording a real weak basis beats recording a
strong-sounding absent one; it grants nothing, and the G00 dossier stays
`HUMAN_REQUIRED`.

## The executor statement (interim, until the identity split lands)

The executor of any merge posts a comment at merge time naming its seat and the delegation it
acted under. **Observed convention, codified here rather than proposed** — every landing since
adoption carries one (`#290`, `#297`, `#298`, one each, measured by first-line declaration).

**Its limits travel with it, and are the reason it is safe to record:**

- **Self-asserted** — text under the same shared account as every other comment.
- **Unverifiable from outside** — no reader can confirm the delegation existed.
- **Falsifiable in one direction only** — its *absence* is checkable; its *presence* proves nothing.

It converts "no artifact" into "a claim a reader can challenge", which is what the banner
regime already provides for comments, and no more. **Whoever cites an executor statement as
evidence that a delegation existed has been misled by the record rather than by the seat**, so
the limits are stated here rather than left to be rediscovered.

Every landing's `merged_by` currently reads the same shared account, so a compliant
configuration and a non-compliant one produce byte-identical artifacts. The structural remedy,
the operator runbook that provisions it, and an enumeration of what stays unverifiable
afterwards are in [`IDENTITY_ATTRIBUTION.md`](IDENTITY_ATTRIBUTION.md).

## Discovery ≠ scope expansion

Work on `BADF-WP-A` that finds problem B opens an Issue for B (`status: DISCOVERED`,
`discovered-by: BADF-WP-A`) and does **not** fix B in A's branch. This is `AGENTS.md`'s
"no silent scope expansion", given a mechanism.

## Not adopted

No permanent `develop` branch. Trunk-oriented: `main` ← PR ← short-lived authorized branch.
