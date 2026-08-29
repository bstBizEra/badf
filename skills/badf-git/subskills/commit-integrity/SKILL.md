---
name: commit-integrity
description: Run badf-git's nested Git loop with intentional staging, inspected diffs and atomic commits, and keep the evidence honest across it -- bind a git-baseline record before verification and judge it with the read-only `badf_gate.py git-staleness` inspector before publishing or opening a pull request, so a rewrite (amend, rebase, reset, cherry-pick) or a moved target is recomputed, never relabelled. Use inside the BUILD stage and before PUBLISH/PR. Do not use to rewrite, stage, commit or push anything on the agent's behalf, and never as a source of authority.
---

# commit-integrity

A subskill of `badf-git` (`../../SKILL.md`) for the BUILD stage's nested loop
(`../../references/git-cycle.md` section 4) and the staleness transitions of the state
machine (`../../references/git-state-machine.md`). Its admission status is recorded in
`badf/skill-registry.json`; this file defines behaviour and hardcodes no lifecycle status.

**The invariant: a history rewrite changes the evidence subject (GIT-I05).** Evidence is
bound to a source head; amend, rebase, reset or cherry-pick produce a *different* head, and
anything measured on the old one is stale until recomputed. Recovery from `STALE_EVIDENCE`
is recomputation, not waiver-by-label. Before this subskill existed, recognising staleness
was an act of memory; twice in this program a self-dossier was bound to a stale base.

## The loop

```text
SYNC → INSPECT → EDIT → STAGE → DIFF → COMMIT → VERIFY → RECONCILE → ↺
```

- **STAGE** intentionally: `git add -p` (or an equivalent hunk review) for mixed changes; never
  `git add .` over unknown state. `git stash` is not durable handoff or evidence (GIT-I07).
- **DIFF**: inspect the staged diff before committing; the commit should be coherent enough
  to review, bisect locally and recover.
- **COMMIT** atomically; the message is working history, not identity -- identity is the
  `Work-Package:` trailer and the branch (GIT-B).
- **VERIFY**: before running the checks that produce evidence, **bind the baseline**:

  ```text
  python3 scripts/badf_gate.py git-baseline > work/<WP>/evidence/git-baseline.json
  ```

- **RECONCILE / before PUBLISH or PR**: judge that baseline against the tree now:

  ```text
  python3 scripts/badf_gate.py git-staleness work/<WP>/evidence/git-baseline.json
  ```

## Dispositions

| Verdict | Exit | Meaning | Do |
| --- | --- | --- | --- |
| `CURRENT` | 0 | same source head, target and policy epoch | proceed |
| `SOURCE_ADVANCED` | 3 | new commits on top; the recorded head is an ancestor | recompute composition; head-bound evidence stays valid *for that head* |
| `STALE_EVIDENCE` | 3 | the recorded head is not an ancestor (a rewrite), or the policy epoch changed | recompute source-bound evidence (the self-dossier), composition and review -- never relabel |
| `TARGET_MOVED` | 3 | `origin/<default>` moved, source unchanged | recompute composition |
| `BLOCKED` | 1 | not a git-baseline record, or a record from another checkout | take a fresh baseline here |

The verdict carries the contract's rewrite record (`old_source_head`, `new_source_head`,
`kind: history_rewrite`, `old_head_still_reachable`, `invalidated`). The rewrite *type* is
not inferable from two revisions and is not guessed. Index and worktree count deltas are
reported informationally; a dirty tree is not a rewrite.

## Boundaries

- Read-only (`GIT-O0`): it judges the loop's result; it never stages, commits, rebases,
  fetches or cleans on the agent's behalf. Private rewrites remain `GIT-O2`, permitted only
  on an unmerged topic branch and only with the recomputation this subskill demands.
- Composition identity (`expected_result_tree`, `merge_method`) and composition-prefix
  staleness are GIT-E; reviewer-approval staleness is GIT-F.
