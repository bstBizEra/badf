# Shadow evidence (`BADF-WP-0082`, Issue #157 / GOV-0062)

**What is real and what is only synthetic — first sentence, as the contract requires.** Every case
below is real BADF history, recomputed from the object store by `tests/test_badf_git_shadow.py` with
the real tools; the one verdict class history cannot replay — `STALE_EVIDENCE` on a rewrite — was
exercised only against synthetic scratch clones, and is listed under non-coverage, not implied to pass.

`badf-git` is unusual among BADF's capability families: **it ran on itself.** Every work package
GIT-B…H was integrated through the tools it was building — rebased under a moving `main` five times,
its composition claims refused as stale and recomputed, its landings verified by the reconcile it
introduced. That history is the shadow corpus. It is recorded once, in
`examples/git-shadow-evidence.json`, and re-derived on every CI run and inside every composed tree.

## Measurement

| Case class | Real history | What the contract had to represent | Outcome |
| :--- | :--- | :--- | :--- |
| `landing-verified` (4) | WP-2026-0076, 0079, 0080, 0081 — the landings that carry a composition record | GIT-E's claim (`expected_content_tree`, bound with `work/<WP>/` and the lockfile excluded) equals what GitHub's squash actually produced; GIT-F's `MERGED != VERIFIED` | **4/4 MATCH.** Each landed content tree equals the record read from the landed tree. |
| `landing-without-record` (11) | WP-2026-0066…0075, 0077, 0078 — landings that predate GIT-E or belong to other families | A landing with no claim must read `composition_verified: false` — visibly, never a silent pass | **11/11 honest.** No record in any of those landed trees; reconcile writes `false`. |
| `identity-conform` (14) | the last 14 first-parent landings on `main` | GIT-B: one NNNN across the `BADF-WP-NNNN:` label and the canonical `Work-Package: WP-2026-NNNN` trailer | **14/14 CONFORM** — the 10 after GIT-B landed had to; the 4 before happened to. |
| `staleness-source-advanced` (1) | a baseline at the GIT-F landing (`928fc6b`) judged at the GIT-G landing (`74282a4`) | GIT-D: forward progress is `SOURCE_ADVANCED` (the recorded head is an ancestor), not a rewrite | **`SOURCE_ADVANCED`**, `source_rewritten: false`, through `git_staleness` in a scratch clone. |
| `release-bound` (1) | `BADF-BASELINE-1.0.0 → 3f6119b`, the `source_revision` of every G00–G02 example | GIT-H: annotated, on `main`'s first parent, record-bound, unmoved; provenance stated (unsigned) | **`RELEASE_BOUND`** through `git_release_check`. |
| runner citations (4 runs) | CI runs 33274353040, 33276346140, 33277666507, 33279337817 (PRs #148, #152, #154, #156) | GIT-C/D/G/H on real infrastructure: a *detached* checkout (`refs/pull/N/merge`) must render `detached`, `CURRENT`, `EVIDENCE_ONLY`, `RELEASE_BOUND` | Rendered as claimed on every run; cited by run id (observed on the platform, not recomputable offline). |

**Result: no contract gap surfaced under real conditions.** The tools said what the contract says
they must, on the history that actually happened — including the three times during the program that
compose *refused* a stale composition record (base moved under #148 twice; content changed after the
claim) and the four times reconcile verified a landing.

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

## Why the root stays `DESIGNED` here

`badf-git` is a declarative router. Its implementation *is* its seven `IMPLEMENTED` subskills
(`repository-state`, `commit-integrity`, `composition-verification`, `pull-request-integration`,
`git-recovery`, `release-versioning`, and the identity contract enforced by `check_pr_traceability`)
and their failing-first and mutation suites; its shadow is this record. Advancing the family up the
ladder is the **operator's admission decision** — the `badf-research` precedent (shadow at WP-0055,
`ACTIVE` by admission at WP-0058) — and is GIT-J, never an agent's act. Nothing in this shadow affects
a gate: no registry status change, no lifecycle change, no new control.
