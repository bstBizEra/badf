# Shadow evidence (`BADF-WP-0082`, Issue #157 / GOV-0062 — re-measured at `fc9e727` by `BADF-WP-0090`, Issue #175 / GOV-0072)

**What is real and what is only synthetic — first sentence, as the contract requires.** Every case
below is real BADF history, recomputed from the object store by `tests/test_badf_git_shadow.py` with
the real tools; the one verdict class history cannot replay — `STALE_EVIDENCE` on a rewrite — was
exercised only against synthetic scratch clones, and is listed under non-coverage, not implied to pass.

`badf-git` is unusual among BADF's capability families: **it ran on itself.** Every work package
GIT-B…J — the admission included — was integrated through the tools it was building, rebased under a moving `main` seven times,
its composition claims refused as stale and recomputed, its landings verified by the reconcile it
introduced. That history — since the GIT-A freeze `b1e0f5a` — is the shadow corpus. It is recorded in
`examples/git-shadow-evidence.json` (first measured at `605f97f`, re-measured at `fc9e727` under the same
corpus rule), and re-derived on every CI run and inside every composed tree.

## Measurement

| Case class | Real history | What the contract had to represent | Outcome |
| :--- | :--- | :--- | :--- |
| `landing-verified` (7) | WP-2026-0076, 0079, 0080, 0081, 0082, 0087, 0088 — every landing that carries a composition record, the admission's own included | GIT-E's claim (`expected_content_tree`, bound with `work/<WP>/` and the lockfile excluded) equals what GitHub's squash actually produced; GIT-F's `MERGED != VERIFIED` | **4/4 MATCH.** Each landed content tree equals the record read from the landed tree. |
| `landing-without-record` (15) | WP-2026-0066…0075, 0077, 0078, 0083…0086 — landings that predate GIT-E or belong to other families | A landing with no claim must read `composition_verified: false` — visibly, never a silent pass | **11/11 honest.** No record in any of those landed trees; reconcile writes `false`. |
| `identity-conform` (21) | every first-parent landing on `main` since `8673d9a` (21) | GIT-B: one NNNN across the `BADF-WP-NNNN:` label and the canonical `Work-Package: WP-2026-NNNN` trailer | **14/14 CONFORM** — the 10 after GIT-B landed had to; the 4 before happened to. |
| `staleness-source-advanced` (1) | a baseline at the GIT-F landing (`928fc6b`) judged at the GIT-G landing (`74282a4`) | GIT-D: forward progress is `SOURCE_ADVANCED` (the recorded head is an ancestor), not a rewrite | **`SOURCE_ADVANCED`**, `source_rewritten: false`, through `git_staleness` in a scratch clone. |
| `release-bound` (1) | `BADF-BASELINE-1.0.0 → 3f6119b`, the `source_revision` of every G00–G02 example | GIT-H: annotated, on `main`'s first parent, record-bound, unmoved; provenance stated (unsigned) | **`RELEASE_BOUND`** through `git_release_check`. |
| runner citations (7 runs) | CI runs 33274353040, 33276346140, 33277666507, 33279337817, 33284842460, 33301153596, 33302765046 (PRs #148, #152, #154, #156, #161, #173, #174) | GIT-C/D/G/H on real infrastructure: a *detached* checkout (`refs/pull/N/merge`) must render `detached`, `CURRENT`, `EVIDENCE_ONLY`, `RELEASE_BOUND` | Rendered as claimed on every run; cited by run id (observed on the platform, not recomputable offline). |

**Result: no contract gap surfaced under real conditions.** The tools said what the contract says
they must, on the history that actually happened — including the three times during the program that
compose *refused* a stale composition record (base moved under #148 twice; content changed after the
claim) and the seven record-bearing landings reconcile verified — the last of them the admission itself.

## Non-coverage (named, not implied)

- **`STALE_EVIDENCE` on rewrites** — the program's rewritten heads (e.g. `7a755d9`, `c10a22e` under
  #148) were force-pushed away and are not on `origin`; the rewrite verdicts stand on the synthetic
  proofs in `tests/test_badf_git_staleness.py` (amend, reset, rebase onto a moved target) only.
- **Recovery inventory on real dirty state** — observed locally during the program (`TOPIC
  RECOVERY_REQUIRED` before a push; `LOCAL` on a mid-rebase residue) but not committed; the committed
  runner records are `EVIDENCE_ONLY` on clean checkouts.
- **Branch-name conformance of landed PR heads** — observed through the GitHub API at merge time;
  branches are deleted on merge, so it is not recomputable offline (the label/trailer half is).
- **Tag signing** — no signed release ref exists; `provenance.signed` is recorded, never verified.

## The root is `ACTIVE` — GIT-J (`BADF-WP-0087`, Issue #169)

`badf-git` is a declarative router. Its implementation *is* its **six subskills** (`repository-state`,
`commit-integrity`, `composition-verification`, `pull-request-integration`, `git-recovery`,
`release-versioning` — all `IMPLEMENTED`) plus the identity contract enforced by `check_pr_traceability`,
with their failing-first and mutation suites; its shadow is this record. When this note was first
written the root was `DESIGNED`, and the earlier text counted seven subskills — there are six; the
count is corrected here and in the GIT-I doctrine section. Advancing the family was the **operator's
admission decision** — the `badf-research` precedent (shadow at WP-0055, `ACTIVE` by admission at
WP-0058) — taken on #169 and landed as GIT-J at `fc9e727`: a registry status flip only, digest unchanged,
`allowed_tools` still `[]`. **Activation granted no authority**, and the re-measure closed no gap: the
non-coverage list above stands exactly as first written. Nothing in this shadow affects a gate: no
registry status change here, no lifecycle change, no new control.
