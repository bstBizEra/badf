# Git/GitHub Recovery Contract

BADF recovery preserves remote history and restores a known, authorized repository state without hiding what happened.

## Principles

1. **Observe before recovery.** Read authoritative GitHub refs/commits/PR state before choosing an action.
2. **Unknown outcome is not failure.** If a remote mutation timed out or returned ambiguously, query GitHub before retry.
3. **Protected history is additive.** Repair `main` by governed revert or forward fix, not reset/rebase/force rewrite.
4. **Recovery is new work.** Bind recovery to a Work Package/incident and produce new evidence.
5. **Known Git objects are recovery anchors.** Existing commit/tree identities remain usable even if a topic ref is damaged or deleted, subject to retention/reachability and authority.
6. **Release identities are immutable.** Correct with a new release/tag; never move a published tag.

## Remote topic-workspace recovery

### Source ref moved unexpectedly

Disposition: `STALE_EVIDENCE` or `BLOCKED`.

1. Observe current source head/tree.
2. Compare it with the expected prior head.
3. Determine whether movement is authorized and within the same WP.
4. Reconcile or create a new additive commit from the current head.
5. Reverify the new source identity.

Do not force the ref back merely because an earlier actor expected a different SHA.

### Source ref damaged but a good commit is known

Preferred recovery is non-destructive:

- preserve the damaged ref/state as evidence;
- create a `recovery/<WP>-<slug>` or replacement authorized source ref from the known-good commit;
- apply a forward correction on that recovery ref;
- open/update the governed PR and rerun checks.

### Source ref deleted

If the required commit SHA is known and still reachable through GitHub objects/history/evidence, recreate a scoped recovery/topic ref from that commit. Record who authorized recreation and the old/new ref identities.

Local `git reflog` is not a required BADF recovery mechanism because the canonical workspace is remote GitHub state.

## Bad change landed on main

Use a new recovery Work Package/incident:

```text
OBSERVE current main
→ identify offending landed commit
→ prepare inverse/forward repair
→ verify candidate
→ PR
→ compose against current main
→ challenge/authorize
→ protected merge
→ reconcile
```

The conceptual public-history operation is `git revert`: create an additive inverse change rather than rewriting shared history. Implementation may be produced through GitHub APIs/automation as long as the resulting commit/PR semantics are equivalent and evidence is preserved.

## Merge outcome unknown

When a merge API call or network session has uncertain outcome:

1. query the PR state;
2. query current protected branch head;
3. inspect merge/landed commit identity returned by GitHub if present;
4. compare against the expected PR head/result;
5. only retry if the authoritative state proves the intended mutation did not occur and authority is still current.

Never double-submit a protected action blindly.

## Conflict recovery

Conflict resolution is new code. Resolve in a controlled candidate branch/ref, preserve rationale for non-trivial choices, recompute composition and rerun affected verification. BADF does not depend on local rerere caches.

## Release recovery

If a release/tag points to the wrong content:

- preserve the published tag/history;
- mark/supersede the bad release through the release system;
- produce a new corrected version/tag under separate release authority;
- bind the new artifact/commit provenance.

Moving/deleting the existing tag to rewrite history is not normal recovery.

## Recovery stop conditions

Stop with `HUMAN_REQUIRED`, `BLOCKED` or `RECOVERY_REQUIRED` when:

- required commit/object identity cannot be established;
- protected/admin mutation would be needed outside delegated authority;
- recovery would overwrite another actor's current source-ref work;
- evidence/authority has expired or conflicts;
- the actual protected result differs from the authorized expected result and cause is unresolved.

## Explicit non-goals

This contract does not implement local linked worktrees, local worktree cleanup, local index/stash restoration, local reflog-based governance, or destructive local reset procedures. Those Git techniques may be useful outside BADF, but they are not the canonical recovery substrate for GitHub Remote Workspace.
