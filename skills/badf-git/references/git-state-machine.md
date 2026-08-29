# Git State Machine

This state machine makes Git progression explicit without creating a new BADF lifecycle gate. A state is an observed/controlled Git delivery condition, not a permission grant.

## Primary states

| State | Meaning | Minimum evidence to enter |
| --- | --- | --- |
| `GIT_AUTHORITY_BOUND` | Git activity is bound to one active work package and target | work-package ID, repository, target, permitted operation scope |
| `GIT_BASELINED` | current repository/source/target state has been observed and recorded | target SHA, source SHA/ref if present, worktree/index status, remote freshness |
| `GIT_ISOLATED` | the change has a bounded source branch/worktree | source ref, branch/worktree identity, no unresolved ownership collision |
| `GIT_CHANGE_ACTIVE` | edits/commits are in progress | current source revision plus nested-loop state |
| `GIT_LOCALLY_VERIFIED` | required source-level checks passed on a named revision | source-head-bound test evidence |
| `GIT_PUBLISHED` | the topic ref exists on the approved remote when publication is authorized | remote source ref + source head observation |
| `GIT_PR_BOUND` | a PR/review unit is traceably bound to the work package and source | PR ID/URL, work-package binding, target, source head |
| `GIT_COMPOSED` | an expected protected result has been computed for the current identities | target base, source head, merge base, method, expected result tree |
| `GIT_VERIFIED` | required checks support the current composed result | composition-bound test evidence and current epochs |
| `GIT_MERGE_AUTHORIZED` | the required authority has authorized integration of the exact current change | current approvals + exact head/base/method/evidence identity |
| `GIT_MERGED` | the platform reports the change landed on the protected target | merged PR/integration result and landed commit identity |
| `GIT_RECONCILED` | actual landed state has been checked against the expected result and acceptance claim | actual protected revision/result + reconciliation evidence |
| `GIT_RELEASED` | optional release/tag record binds an authorized verified main revision | release authority + release evidence |
| `GIT_CLEANED` | disposable local/topic state has been intentionally reconciled | proof state is no longer needed and no unknown work is destroyed |
| `GIT_LEARNED` | validated reusable lessons have been captured through governed learning | learning record/proposal with provenance |

`GIT_RELEASED` is optional. A non-release work package can progress from `GIT_RECONCILED` to `GIT_CLEANED`.

## Hold and failure states

| State | Trigger | Allowed next behavior |
| --- | --- | --- |
| `STALE_EVIDENCE` | source, target, merge method, policy epoch, test epoch, conflict resolution, or expected result changed after evidence | observe/recompute/retest/re-review; never reuse stale authorization silently |
| `BLOCKED` | required identity, dependency, check, evidence, tool permission, or authority cannot be established | diagnose, preserve state, escalate or amend work package |
| `HUMAN_REQUIRED` | the next decision/action is reserved or exceeds delegated authority | prepare evidence and request the authorized human decision; no self-approval |
| `RECOVERY_REQUIRED` | state is inconsistent, unknown, lost, conflicted, or restoration would require risky/destructive action | enter the recovery contract; preserve evidence before mutation |
| `OUTCOME_UNKNOWN` | a remote mutation returned timeout/ambiguous result and final remote state is not established | observe authoritative remote state before any retry |
| `REWORK_REQUIRED` | verification/challenge proves the current change does not meet the contract | return to `GIT_CHANGE_ACTIVE` with a changed hypothesis/implementation |

## Normal transitions

```text
GIT_AUTHORITY_BOUND
  → GIT_BASELINED
  → GIT_ISOLATED
  → GIT_CHANGE_ACTIVE
  → GIT_LOCALLY_VERIFIED
  → GIT_PUBLISHED
  → GIT_PR_BOUND
  → GIT_COMPOSED
  → GIT_VERIFIED
  → GIT_MERGE_AUTHORIZED
  → GIT_MERGED
  → GIT_RECONCILED
  → [GIT_RELEASED]
  → GIT_CLEANED
  → GIT_LEARNED
```

The sequence can pause, return, or skip a non-applicable publication/release step, but it must not jump across evidence or authority boundaries.

## Transition guards

### `GIT_AUTHORITY_BOUND → GIT_BASELINED`

Required:

- canonical work-package identity exists;
- repository and target are unambiguous;
- read access is permitted;
- the proposed mutation class is within work-package scope.

Failure → `BLOCKED` / `HUMAN_REQUIRED`.

### `GIT_BASELINED → GIT_ISOLATED`

Required:

- baseline captures unknown/unrelated state rather than destroying it;
- branch/worktree target is derived from the intended base;
- no conflicting ownership of the same worktree/files without an integration plan.

Failure → `BLOCKED` or `RECOVERY_REQUIRED`.

### `GIT_CHANGE_ACTIVE → GIT_LOCALLY_VERIFIED`

Required:

- current source revision is fixed for the evidence run;
- required source-level checks are run and recorded;
- failures are not suppressed or relabelled.

Any source rewrite/edit after the checks returns to `GIT_CHANGE_ACTIVE` and invalidates affected evidence.

### `GIT_LOCALLY_VERIFIED → GIT_PUBLISHED`

Required only when remote publication is in scope:

- remote topic mutation is authorized;
- target remote/repository/ref is exact;
- no secrets or prohibited data are included;
- push outcome is observed.

A timeout does not imply failure or success; it produces `OUTCOME_UNKNOWN` until the remote ref is observed.

### `GIT_PUBLISHED → GIT_PR_BOUND`

Required:

- PR target and source refs are correct;
- PR carries the canonical work-package binding and issue/demand traceability;
- exact current source head is known;
- scope and non-goals are reviewable.

### `GIT_PR_BOUND → GIT_COMPOSED`

Required:

- current target base is observed;
- merge base is recomputed;
- expected result tree is computed with the intended merge method;
- ordered-prefix position is known when multiple changes are composed.

Any upstream movement before/during composition restarts this transition from the new target base.

### `GIT_COMPOSED → GIT_VERIFIED`

Required:

- checks run on the expected composed result or an equivalent canonical composition representation;
- evidence binds to current target/source/result/test/policy identity;
- no required check is missing or unknown.

### `GIT_VERIFIED → GIT_MERGE_AUTHORIZED`

Required:

- required independent reviews/approvals are present and current;
- no open blocker/expired exception exists;
- exact source head/target/method/result identity is unchanged;
- the actor who will merge has separate integration authority.

This skill cannot create this state by itself.

### `GIT_MERGE_AUTHORIZED → GIT_MERGED`

Required:

- protected integration occurs through the platform-approved method;
- expected head protection is used when available;
- platform/ruleset checks are not bypassed;
- final outcome is observed from the authoritative platform.

If the target or source changed first → `STALE_EVIDENCE`, not merge.

### `GIT_MERGED → GIT_RECONCILED`

Required:

- actual landed commit/ref is observed;
- actual result tree is reconciled to expected composition;
- issue/PR/work-package evidence is reconciled;
- post-merge checks/holds are recorded.

Unexpected mismatch → `RECOVERY_REQUIRED` or `BLOCKED`.

### `GIT_RECONCILED → GIT_RELEASED`

Only when release is in scope and separately authorized. Release authority, immutable artifact identity and release evidence are required.

### `GIT_RECONCILED/GIT_RELEASED → GIT_CLEANED`

Required:

- branch/worktree/local state is known disposable;
- no sole copy of evidence or recovery information will be lost;
- no open review/incident depends on the state.

### `GIT_CLEANED → GIT_LEARNED`

Learning is not automatic policy mutation. Reusable conclusions require provenance and separate governed adoption.

## Staleness transitions

The following events send affected downstream states to `STALE_EVIDENCE`:

- source head changes after verification/review/composition;
- target base changes after composition;
- rebase, amend, reset, cherry-pick or conflict-resolution rewrite changes source history/content;
- merge method changes;
- expected result tree changes;
- policy/ruleset/authority epoch materially changes;
- test-set/toolchain epoch changes where the prior evidence depended on it;
- ordered composition prefix changes;
- required reviewer approval becomes stale under repository policy.

Recovery from `STALE_EVIDENCE` is **recomputation**, not waiver-by-label.

## Recovery transitions

`RECOVERY_REQUIRED` does not authorize destructive commands. The recovery contract first establishes:

1. what state exists;
2. what state is authoritative;
3. what must be preserved;
4. whether the error is local, remote-topic, protected-target, or evidence-only;
5. the least-destructive authorized recovery path.

Shared/protected history normally repairs forward. Local lost state is recovered into a separate branch/ref before cleanup.

## State ownership

- Git observations can establish Git facts.
- CI can establish check outcomes.
- repository/platform controls can establish protected integration facts.
- authorized reviewers/authorities establish approvals.
- this skill can route evidence among these facts but cannot collapse them into a self-approved decision.
