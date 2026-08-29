---
name: repository-state
description: Observe and record the Git baseline of a working tree before any material Git operation -- repository identity, worktree/branch/index state as counts, target and source revisions and trees, merge base, ahead/behind, remote freshness and policy epoch -- by running the read-only `badf_gate.py git-baseline` inspector. Use at badf-git's BASELINE stage and whenever a claim about "where the checkout is" must be measured rather than typed. Do not use to fetch, check out, stash, clean, reset or otherwise change Git state, and never as a source of authority.
---

# repository-state

A subskill of `badf-git` (`../../SKILL.md`). It produces the **git-baseline record** that
badf-git's BASELINE stage (`../../references/git-cycle.md` section 2) and the
`GIT_BASELINED` state (`../../references/git-state-machine.md`) require before editing. Its
admission status is recorded in `badf/skill-registry.json`; this file defines behaviour and
hardcodes no lifecycle status.

**The invariant: a baseline is measured, not typed.** Until this subskill existed,
`GIT_BASELINED` was a sentence an agent wrote. The record is produced by one deterministic
command in the canonical control (GIT-I12: no second validator):

```text
python3 scripts/badf_gate.py git-baseline [<path>]      # default: this repository
```

It is `GIT-O0 OBSERVE` (`../../references/operation-authority-matrix.md`): it writes nothing,
fetches nothing, and never moves a ref, the index, the worktree, the stash or the reflog. It
grants nothing (GIT-I01) -- a green baseline is a fact about the checkout, not permission to
change it.

## What the record carries

- repository identity (the `SELF` registry name when the tree is a BADF repository, and the root path);
- worktree path, `head_kind` (`branch` | `detached`), branch, whether it is a linked worktree;
- index and worktree status as **counts only** -- staged, unstaged, untracked, unmerged, stash entries --
  never a path and never a byte of content;
- `target_ref` (`refs/heads/<default>`), `target_sha`, `target_tree` -- the target as known locally;
- `source_ref` (null when detached), `source_head_sha`, `source_tree`;
- `merge_base_sha`, `ahead`, `behind`, `head_is_ancestor_of_target`;
- `remote_freshness` stated honestly: the tracking ref's SHA with `observed_without_fetch: true`;
- `policy_epoch` from `badf/lifecycle.json`; `observed_at`; `disposition: GIT_BASELINED`;
- `non_coverage`: the contract's test-set/toolchain epoch does not exist in BADF and is declared, not invented.

## Dispositions

- `GIT_BASELINED` (exit 0) -- a reproducible baseline exists; the record is the evidence.
- `BLOCKED` (exit 1) -- outside a git working tree; `origin/<default>` does not resolve (the inspector
  never falls back to HEAD, the same rule the monotonic authority resolver follows); HEAD is unborn.

## Boundaries

- Composition identity (`expected_result_tree`, `merge_method`, epochs) is GIT-E, not this subskill.
- Branch-name conformance is judged by `check_pr_traceability.py` (GIT-B); this record only *reports* the branch.
- Platform state (pull requests, rulesets, checks) is GIT-F; nothing here talks to GitHub.
