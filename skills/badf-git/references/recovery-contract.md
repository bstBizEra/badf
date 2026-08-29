# Git Recovery Contract

Recovery begins with preservation and diagnosis. A command that makes the checkout look clean is not automatically a safe recovery.

## Fundamental rule

```text
PRESERVE → IDENTIFY → CLASSIFY → RECOVER → VERIFY → RECONCILE
```

Never start with `reset --hard`, destructive `clean`, forced protected-ref movement, or deletion of unknown branches/worktrees merely because the repository is inconvenient.

## Recovery classes

### Local working-state recovery

Examples:

- uncommitted edits appear lost;
- wrong branch/worktree was used;
- an amend/rebase/reset obscured a prior commit;
- staged/unstaged state is confusing;
- a branch was moved locally.

Preferred discovery/recovery tools:

- `git status`
- `git diff` / `git diff --cached`
- `git reflog`
- `git show`
- `git fsck` only when appropriate to investigate unreachable objects
- create a **recovery branch/ref** pointing at the known good commit before cleanup.

`git reflog` is local recovery evidence, not a shared audit log. Reflog retention is not permanent, so valuable recovered state should be promoted to a named ref/commit/evidence artifact promptly.

### Topic-branch recovery

Examples:

- private rebase went wrong;
- an authorized force-with-lease update needs correction;
- branch diverged from intended source;
- conflict resolution was incorrect.

Rules:

- observe local and remote branch heads;
- preserve the pre-recovery head in a recovery ref when useful;
- decide whether the corrected branch will be a new commit or a private-history rewrite;
- if history is rewritten, invalidate affected evidence/reviews/composition;
- if remote topic state must be overwritten, require explicit remote-topic mutation authority and verify the expected remote head.

Do not repair a shared topic branch by silently replacing collaborators' commits.

### Protected/shared-history recovery

Once a change lands on `main`, normal recovery is a **new forward change**, usually `git revert` (or an equivalent platform-governed revert workflow).

Why:

- protected history remains auditable;
- the correction has its own work package/evidence/review;
- downstream clones and references do not lose history;
- the faulty state and remediation remain attributable.

Do not rewrite `main` to erase a bad merge under normal BADF operation.

A revert itself is not automatically safe: it can conflict with later changes, break migrations/contracts, or fail current tests. Treat it as a new change and compose/verify it against current `main`.

### Release-ref recovery

Published release/baseline tags are governance artifacts. Do not move/delete/reuse an immutable release tag to make history look correct.

If a release is bad:

- preserve the original release record/tag;
- issue rollback/revert/new release through release authority;
- create a new version/tag where required;
- record supersession/revocation status rather than rewriting historical identity.

Historical unsigned tags are not retroactively rewritten merely to satisfy a newer signing policy.

## Unknown state

If state is unknown, recovery stops mutation until it is classified.

Questions to answer:

1. Which repository/worktree are we in?
2. Which branch/ref is checked out?
3. What is HEAD?
4. What is staged, unstaged and untracked?
5. Which commits/refs exist locally and remotely?
6. Which state is authoritative?
7. Is any content the only copy of work/evidence?
8. Is another agent/user relying on the branch/worktree?
9. What work-package authority covers the proposed recovery?
10. Which evidence becomes stale if state changes?

## Reset posture

### `reset --soft` / `reset --mixed`

These can be legitimate private-history tools under `GIT-O2` when the branch is unmerged/unprotected and state is preserved/understood. They still change source identity and invalidate affected evidence.

### `reset --hard`

Classify as `GIT-O5 DESTRUCTIVE` whenever it could discard unique tracked/index/worktree state.

Default: deny.

Only consider when:

- exact target is verified;
- the discarded state is known and preserved or intentionally disposable;
- destructive authority is explicit;
- no safer route exists;
- before-state evidence exists;
- rollback/recovery is understood.

A convenience cleanup is not sufficient justification.

## Clean posture

Commands equivalent to `git clean -f`, `-d`, or `-x` can destroy untracked/generated/ignored state.

Before any destructive clean:

- preview scope;
- distinguish reproducible generated files from unique local artifacts;
- preserve anything potentially valuable;
- verify the work package permits destructive cleanup.

Do not delete ignored files blindly: credentials, local databases, build caches, evidence exports or user artifacts may be ignored by Git but still important or sensitive.

## Restore/checkout posture

Restoring a path from another revision can overwrite local work. Before doing so:

- inspect the path diff;
- preserve unknown content;
- verify source revision/path;
- confirm the overwrite is within work-package scope.

A path-level restore can be `GIT-O1` when reversible/preserved, but becomes destructive if unique state is discarded.

## Reflog recovery pattern

Conceptual sequence:

```text
OBSERVE reflog
  → identify candidate prior commit
  → inspect candidate
  → create recovery branch/ref
  → verify recovered content
  → decide how to reconcile with current branch
```

Do not immediately move the primary branch pointer before the candidate is inspected and preserved.

## Revert pattern for landed work

Conceptual sequence:

```text
new recovery WP
  → baseline current main
  → identify landed change to reverse
  → create revert as a new change
  → resolve conflicts explicitly
  → verify source
  → compose against current main
  → independent challenge / authorize
  → protected integration
  → post-merge reconciliation
```

The revert's source is the current target, not necessarily the historical parent of the bad commit.

## `rerere` contract

`rerere` can remember conflict resolutions. Recommended design posture:

```text
rerere.enabled = true
rerere.autoUpdate = false
```

Rules:

- recalled content is a **candidate**, not a decision;
- inspect the resolved diff;
- confirm requirements/semantics still match the new conflict context;
- stage intentionally;
- rerun affected tests;
- record non-obvious reused-resolution provenance when material.

Do not interpret `rerere` reuse as proof that a previous resolution remains correct.

## Stash contract

`git stash` may temporarily park local changes, but:

- it is local and easy to forget;
- it is not a durable work-package handoff;
- it is not immutable evidence;
- it is not an authorization record;
- it is not a substitute for a recovery branch/commit when state matters.

If stashed state becomes material to a decision or handoff, promote it to a named, reviewable form.

## Cherry-pick posture

Cherry-pick can be useful to reconstruct a private topic branch or deliver a bounded correction, but it creates new commit identity and can change context.

Consequences:

- source SHA/evidence binding changes;
- conflict resolutions are new edits;
- composition must be recomputed;
- do not use cherry-pick to bypass the authorized branch/PR path.

## Recovery evidence

Record:

- recovery trigger;
- repository/worktree/ref identities;
- before-state SHAs and local state summary;
- authoritative state/source used for recovery;
- preservation step (recovery branch/artifact/etc.);
- operation class and commands/API calls;
- after-state SHAs;
- evidence/reviews invalidated;
- verification outcome;
- residual uncertainty.

Failed recovery attempts are evidence. Do not erase them when they affect the next decision.

## Recovery stop conditions

Stop and emit `RECOVERY_REQUIRED`, `BLOCKED` or `HUMAN_REQUIRED` when:

- unique state cannot be classified;
- the only known remedy rewrites protected history;
- destructive scope is broader than the work package;
- another actor's branch/worktree may be overwritten;
- remote mutation outcome is unknown;
- release/tag identity would need rewriting;
- required recovery authority is absent;
- preservation cannot be established.
