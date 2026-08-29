# GitHub Remote Workspace, Branch and Pull Request Contract

BADF isolates delivery work on GitHub. A **GitHub Remote Workspace** is a BADF abstraction over remote refs and immutable Git objects; it is not native `git worktree`.

## Canonical workspace identity

```yaml
github_remote_workspace:
  repository: bstBizEra/badf
  target_ref: refs/heads/main
  target_base_sha: <commit-sha>
  target_base_tree: <tree-sha>
  source_ref: refs/heads/wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>
  source_head_sha: <commit-sha>
  source_head_tree: <tree-sha>
  pr_number: null
  observed_at: <timestamp>
```

A filesystem checkout path is never part of the canonical identity.

## Topic branch contract

The proposed canonical branch form is:

```text
wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>
```

The Work-Package identity contract is being hardened separately; **branch-name enforcement is deferred** until that contract lands. A branch name is traceability, not authority.

### Creation

1. Observe the current authorized target ref and exact target-base SHA from GitHub.
2. Confirm no conflicting source ref already represents another active workspace.
3. Create the source ref directly on GitHub from that exact SHA.
4. Record source head/tree identity immediately after creation.

Do not create a local filesystem checkout as the BADF isolation primitive.

## Remote mutation protocol

Normal source-ref mutation is optimistic and additive:

```text
OBSERVE source_head=A
READ exact remote content/object
PREPARE candidate change
BUILD tree T2
CREATE commit B(parent=A, tree=T2)
ADVANCE source_ref A → B without force
OBSERVE source_ref
```

If the source ref is no longer `A`, do not overwrite it. Return `STALE_EVIDENCE`/`BLOCKED`, read the new state and reconcile.

GitHub contents APIs may create commits directly; lower-level Git data APIs may create blobs, trees and commits. Either path must preserve the same pre-state/post-state evidence and Work-Package scope.

## Parallel agents

- one active Work Package normally owns one source ref;
- independent agents use different refs/workspaces;
- overlapping-file edits require a designated integrator or explicit serialization;
- two agents must not race by force-updating the same source ref;
- remote ref movement is a concurrency signal, not a reason to overwrite.

## Commit contract

Each material commit must be attributable to the active Work Package through the surrounding GitHub workspace/PR evidence. Keep commits coherent and reviewable. The final protected squash message remains governed by the repository PR traceability contract.

BADF does not require a local staging area to establish commit correctness. Review is based on GitHub object/diff identity and the candidate revision that CI verifies.

## Synchronization

GitHub `main` movement never silently changes a workspace. Re-observe target state before composition. When a target move matters:

1. mark target-bound composition evidence stale;
2. compare the current source with the new target;
3. update the source ref through an authorized additive commit/reconstruction strategy if needed;
4. rerun affected source and composed verification.

Local rebase is not a BADF requirement. A remote history rewrite of a published topic ref is exceptional because it changes source identity and invalidates evidence.

If a separately authorized topic-ref rewrite is unavoidable, it must bind an exact expected prior remote SHA. The safety concept is equivalent to `--force-with-lease`; **Bare `--force` is not a normal BADF workflow**. Diagnostic `git range-diff` may help humans compare reconstructed patch series, but it is not machine identity.

## Pull request contract

A PR binds at minimum:

```yaml
pull_request:
  work_package: WP-2026-NNNN
  issue_or_demand: <id>
  target_ref: refs/heads/main
  target_base_sha: <sha used by current composition>
  source_ref: refs/heads/wp/...
  source_head_sha: <exact reviewed head>
  source_head_tree: <tree>
  merge_method: squash
  expected_result_tree: <tree after composition>
```

The PR body carries the repository-required `## What`, `## Verification`, `Work-Package:` and `Closes #N` surfaces. A PR is evidence and collaboration state, not merge authority.

## Movement and staleness

Any of these invalidate affected evidence:

- source-head movement;
- target-base movement;
- material PR-message change when the message affects the squash result/ledger;
- merge-method change;
- policy/ruleset change;
- material test/toolchain epoch change.

Recompose/reverify after movement.

## Merge contract

Before protected integration confirm:

- PR head equals reviewed/evidenced source head;
- current target is compatible with the composition claim;
- required checks are current;
- required independent challenge is current;
- no blocking thread/condition remains;
- merge authority is valid;
- merge method matches the active ruleset.

Where GitHub accepts an expected head SHA, use it so a moved PR head is rejected rather than merged accidentally.

## Cleanup

After merge and post-merge reconciliation, the remote topic ref may be deleted when policy permits. Preserve commit/PR/evidence identities. BADF has no requirement to remove a local filesystem checkout because none is created by this contract.

## Explicit non-goal

GitHub does not provide a persistent native `git worktree` object. BADF therefore must not implement local worktree path conventions, local worktree registries, or local-worktree cleanup as governance requirements.
