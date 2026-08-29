# Git Operation and Authority Matrix

This reference classifies Git operations for routing and risk discussion. It does **not** assign authority. Canonical capability governance remains `docs/08-mcp-and-tools.md` (`READ`, `WRITE`, `DESTRUCTIVE`, `ADMIN`), the active work package, `badf/tool-registry.json`, `badf/authority-matrix.json`, repository policy and platform controls.

## Two-layer classification

BADF uses:

1. **Canonical tool operation class** — `READ`, `WRITE`, `DESTRUCTIVE`, `ADMIN`.
2. **Git-local operation class** — `GIT-O0` through `GIT-O5`, which describes Git-specific risk and evidence expectations.

The Git-local class may only **narrow** behavior. It cannot downgrade a canonical tool/platform classification.

## Classes

### `GIT-O0 — OBSERVE`

Purpose: establish repository facts without changing Git state.

Examples:

- `git status`
- `git log`
- `git diff`
- `git show`
- `git rev-parse`
- `git merge-base`
- `git cat-file`
- `git branch --show-current`
- read-only remote/ref/PR/status observation

Canonical mapping: normally `READ`.

Controls:

- record repository/ref identity when evidence depends on it;
- avoid commands whose apparent inspection also mutates state/config;
- sanitize output before storing evidence;
- a read result can be stale immediately after upstream movement.

### `GIT-O1 — LOCAL_REVERSIBLE`

Purpose: create bounded local source state whose effect is normally recoverable without protected history mutation.

Examples, when separately authorized:

- fetch remote objects/refs;
- create/switch a work-package branch;
- add a dedicated worktree;
- intentionally stage/unstage content;
- create local commits;
- restore a known path from a verified source when this does not destroy unknown work;
- create a recovery branch/ref before repair.

Canonical mapping: usually `WRITE` to local repository state; a fetch can also update remote-tracking refs and is therefore state-changing even though it does not change the remote repository.

Controls:

- baseline before mutation;
- preserve unrelated work;
- exact target/source binding;
- do not infer remote/push/merge permission from local write permission.

### `GIT-O2 — HISTORY_REWRITE_PRIVATE`

Purpose: rewrite the history of an **unmerged, unprotected private/work-package topic** when explicitly permitted and coordinated.

Examples:

- `git commit --amend`
- `git rebase`
- interactive rebase (`pick/reword/edit/squash/fixup/drop`)
- `git reset --soft` / `--mixed` on a private branch
- cherry-pick used to reconstruct/reorder topic history

Canonical mapping: at least `WRITE`; can become `DESTRUCTIVE` when it would discard unique/unpreserved state or overwrite shared remote history.

Hard boundaries:

- never treat this class as permission to rewrite `main` or another protected/shared ref;
- do not rewrite a branch another actor relies on without explicit coordination;
- source SHA changes invalidate affected evidence, reviews and composition;
- preserve dropped/lost commits through reflog/recovery refs when risk exists;
- remote publication of rewritten history is a separate `GIT-O3` action.

Evidence consequence:

```text
HISTORY_REWRITE_PRIVATE → SOURCE_IDENTITY_CHANGED → AFFECTED_EVIDENCE_STALE
```

`git range-diff` may help explain how the old/new patch series differ, but the stable binding remains SHA/tree/evidence identity.

### `GIT-O3 — REMOTE_TOPIC_MUTATION`

Purpose: create/update/delete **non-protected topic refs** on an approved remote.

Examples, when permitted:

- push a new WP branch;
- fast-forward/update a WP branch;
- update a rewritten WP branch with a guarded lease;
- delete a merged/abandoned topic branch after reconciliation.

Canonical mapping: `WRITE`; deletion or overwrite can be `DESTRUCTIVE` under canonical tool/platform semantics.

Controls:

- exact repository/remote/ref verification;
- current remote observation before overwrite/delete;
- push only work-package-authorized content;
- no secrets/prohibited data;
- observe final remote state after timeout/ambiguous response;
- `--force-with-lease` is the maximum normal force boundary for a permitted rewritten topic branch; bare `--force` is not a normal BADF workflow;
- lease safety is not authority and does not make overwriting another actor's work acceptable.

### `GIT-O4 — PROTECTED_INTEGRATION`

Purpose: change protected integration/release refs through an approved platform workflow.

Examples:

- squash merge a PR to protected `main`;
- create an authorized protected release tag/ref;
- publish a release record that binds verified `main`.

Canonical mapping: `WRITE` and possibly `ADMIN`/reserved-action semantics depending on repository/platform policy. The higher classification always wins.

Controls:

- separately granted integration/release authority;
- exact expected source head;
- current target/base and composition evidence;
- required checks/reviews/conditions current;
- repository-approved merge method;
- no bypass of rulesets/branch protection;
- post-operation reconciliation.

The ability of a connected GitHub tool or token to perform the operation is **capability**, not authorization.

### `GIT-O5 — DESTRUCTIVE`

Purpose: actions that can irreversibly or materially discard/overwrite state, or alter protected history/policy.

Examples:

- `git reset --hard` where unique state may be lost;
- `git clean -f/-d/-x` over unknown/unverified scope;
- forced movement of `main` or another protected/shared ref;
- rewriting/deleting release tags or immutable baseline refs;
- deleting branches/worktrees that contain unique uncommitted evidence/work;
- bypassing protected integration controls;
- changing GitHub rulesets/branch protection to make a merge possible.

Canonical mapping: `DESTRUCTIVE` and/or `ADMIN`.

Default: **deny**.

Requirements before any exception:

- explicit work-package scope for the exact target;
- separately granted destructive/admin authority;
- authoritative target identity;
- inventory/preservation of unique state;
- recovery/rollback procedure;
- evidence of the before state;
- no safer authorized alternative.

`badf-git` cannot authorize an exception.

## Common command posture

| Operation | Git class | Notes |
| --- | --- | --- |
| `status`, `log`, `diff`, `show`, `rev-parse`, `merge-base` | O0 | read-only observation |
| `fetch` | O1 | local ref/object mutation; remote read |
| create/switch WP branch | O1 | local reversible write |
| `worktree add` | O1 | isolate parallel work |
| stage/unstage | O1 | inspect staged diff before commit |
| commit | O1 | source identity changes; evidence binds after commit |
| amend/rebase/rebase-i | O2 | private only; evidence becomes stale |
| `reset --soft/--mixed` private | O2 | preserve/check state; evidence stale |
| push new topic | O3 | remote write |
| guarded rewrite of topic (`--force-with-lease`) | O3 + O2 consequence | only when explicitly permitted and remote expected state is verified |
| squash merge protected PR | O4 | exact head/current composition + separate authority |
| create protected release tag | O4 | release authority + verified main |
| `revert` landed change | O1 locally then O3/O4 to deliver | repairs forward; still a new governed change |
| reflog inspection | O0 | local recovery discovery |
| create recovery branch from reflog | O1 | preserve before cleanup |
| `rerere` recall | O1 candidate | recalled resolution must be reviewed/tested |
| `reset --hard`, destructive clean | O5 | deny by default |
| forced protected ref/tag rewrite | O5 | deny by default / reserved admin action |
| ruleset/branch-protection change | O5 / ADMIN | outside this skill's authority |

## `rerere` posture

Recommended design posture:

```text
rerere.enabled = true
rerere.autoUpdate = false
```

Reason:

- remembered resolutions can reduce repeated manual conflict work;
- automatic staging can blur the boundary between **recalled** and **reviewed** resolution;
- with auto-update disabled, the recalled resolution remains a candidate requiring inspection, staging and verification.

Repository/user configuration is a separate authorized operation; this contract does not change config automatically.

## Stash posture

`git stash` may be a temporary local convenience, but it is not:

- a durable handoff;
- an evidence store;
- a work-package record;
- an authority record;
- a safe substitute for committing/recovery-branch preservation when state matters.

If state must survive session/agent handoff, preserve it through a named branch/commit/artifact/session record as appropriate.

## Operation evidence

For every material `WRITE`, `DESTRUCTIVE` or `ADMIN` Git action, record at least:

- work-package ID;
- actor/tool;
- repository;
- Git-local and canonical operation class;
- target ref/path/worktree;
- before revision/state;
- after revision/state when known;
- command/API operation with secrets removed;
- started/completed time;
- outcome;
- returned remote identifier when applicable;
- evidence invalidated by the operation;
- next required reconciliation.

See `evidence-contract.md` for the full binding.
