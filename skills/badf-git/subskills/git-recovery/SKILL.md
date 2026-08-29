---
name: git-recovery
description: Recover Git state the way badf-git's recovery contract requires -- PRESERVE, IDENTIFY and CLASSIFY before anything destructive -- by rendering the unique-state inventory with the read-only `badf_gate.py git-recovery` inspector, establishing preservation with `--preserve` (recovery refs only), and then following the least-destructive path for the class: reflog recovery for local loss, a preserved topic for unpushed work, and a forward `git revert` under a new work package for anything that landed on the protected branch. Use whenever state is unknown, a reconcile is BLOCKED, or a reset/clean/force is being considered. Do not use to perform destructive operations, to rewrite the protected branch, or to grant recovery authority.
---

# git-recovery

A subskill of `badf-git` (`../../SKILL.md`) for the recovery contract
(`../../references/recovery-contract.md`) and the `RECOVERY_REQUIRED` transitions of the state
machine. Its admission status is recorded in `badf/skill-registry.json`; this file defines
behaviour and hardcodes no lifecycle status.

**The invariant: `PRESERVE → IDENTIFY → CLASSIFY → RECOVER → VERIFY → RECONCILE`.** Never start
with `reset --hard`, a destructive `clean`, a forced protected-ref movement or the deletion of an
unknown branch or worktree because the repository is inconvenient. Unknown state stops mutation
until it is classified — and classification is measured, not guessed.

## IDENTIFY + CLASSIFY (read-only, `GIT-O0`)

```text
python3 scripts/badf_gate.py git-recovery [<path>]
```

renders the **git-recovery record**: the git-baseline, the **unique-state inventory** —
uncommitted changes (a count), stash entries, **dangling commits** (reflog entries of HEAD reachable
from no ref: the only copy of a commit), **unpushed commits** per local branch, **other worktrees** of
the same repository and the branch each holds (another actor may be relying on it) — the
**recovery class** and the **disposition**:

| Class | Meaning | Least-destructive path |
| --- | --- | --- |
| `EVIDENCE_ONLY` | nothing unique; only records may be stale | recompute (`git-staleness`, `--record`) |
| `LOCAL` | uncommitted, stashed or dangling state exists only here | preserve; recover from the reflog into a recovery ref; verify; then decide |
| `TOPIC` | commits exist only on a local branch | preserve; publish or keep a recovery ref before deleting/rewriting; `--force-with-lease` only after preservation |
| `PROTECTED` | HEAD is the protected branch | repair **forward** with `git revert` under a **new work package**, composed against current `main`; never rewrite `main` |

`RECOVERABLE` (exit 0) means nothing unique needs preserving; `RECOVERY_REQUIRED` (HELD, exit 3)
means unique state exists and must be preserved before any destructive step. Unmerged paths are
`BLOCKED` (exit 1): resolve or abort first, never clean around a conflict.

## PRESERVE (`GIT-O1`, opt-in, additive only)

```text
python3 scripts/badf_gate.py git-recovery --preserve <label> --wp <WP> [<path>]
```

creates `refs/recovery/<WP>/<label>` at HEAD and, when the tree is dirty,
`refs/recovery/<WP>/<label>-worktree` at a `git stash create` snapshot — which writes objects and
touches neither the worktree, the index nor the stash list. An existing label is never overwritten.
This is the contract's "preservation step" and its "evidence of the before state", in one record.

## RECOVER → VERIFY → RECONCILE (procedure)

- **Local loss:** `git reflog` → inspect the candidate → it is already a recovery ref if preserved,
  otherwise `git update-ref refs/recovery/<WP>/<label> <sha>` → verify the content → decide how to
  reconcile with the current branch. Do not move the primary branch pointer before the candidate is
  preserved and inspected.
- **Unpushed topic:** preserve, then publish (`git push -u`) or keep the recovery ref; a rewrite of a
  private topic is `GIT-O2` and invalidates its evidence (`commit-integrity`).
- **Landed on `main` (incl. a `BLOCKED` reconcile — landed content ≠ the composition record):**
  open a **recovery work package**; `git revert <landed sha>` as a new change on a `wp/` branch;
  compose it against current `main` (`--record`); independent challenge; head-bound squash;
  post-merge `reconcile`. The bad landing and its remediation stay attributable; `main` is never
  rewritten.
- **Release refs:** never rewritten — GIT-H.

Record the recovery evidence (trigger, identities, before-state SHAs, preservation refs, operation
class, after-state, invalidated evidence, verification outcome, residual uncertainty). Failed
recovery attempts are evidence; keep them.

## Boundaries

- The tool never runs `reset`, `clean`, `checkout`, `push`, `branch -D`, `worktree remove` or any
  ref deletion; it makes those decisions safe to *take*, and records what they would cost.
- Another actor's reliance on a branch/worktree is reported, not decided; remote-topic and
  release-ref recovery are procedures, not this record.
