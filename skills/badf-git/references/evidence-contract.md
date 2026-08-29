# Git/GitHub Evidence Contract

Git evidence proves what repository state was observed or changed. It does not create authority.

## Remote baseline record

For GitHub-native operation capture at minimum:

```yaml
git_baseline:
  repository: bstBizEra/badf
  observed_at: <timestamp>
  target_ref: refs/heads/main
  target_sha: <sha>
  target_tree: <tree-sha>
  source_ref: refs/heads/wp/...
  source_sha: <sha-or-null>
  source_tree: <tree-or-null>
  ruleset_refs: [<stable-id>]
  pr_number: <number-or-null>
  check_state: <summary-or-null>
```

When relevant also capture merge base, ahead/behind/compare identity, policy epoch and test-set epoch.

Do not include a local worktree path, local index, stash or reflog as a required baseline field.

## Mutation evidence

Every material remote mutation should record:

```yaml
git_transition:
  transition_id: <stable-id>
  work_package: WP-2026-NNNN
  repository: bstBizEra/badf
  operation_class: GIT-O1
  operation: <create-branch|create-commit|advance-ref|update-file|...>
  actor: <principal/workload identity>
  pre_state:
    ref: refs/heads/wp/...
    expected_sha: <sha-or-null>
    expected_tree: <tree-or-null>
  intent:
    affected_paths: [<path>]
    target_ref: refs/heads/wp/...
  post_state:
    observed_sha: <sha>
    observed_tree: <tree>
  external_id: <GitHub returned id/url/sha where applicable>
  outcome: PASS|FAIL|BLOCKED|OUTCOME_UNKNOWN
  observed_at: <timestamp>
```

For object-level construction, bind created blob/tree/commit SHAs. For contents operations, bind the returned commit/content identity.

## Concurrency evidence

A source-ref update must preserve the observed pre-state. Record the prior head and resulting head. If the ref moved unexpectedly, preserve the failed transition and return to observation rather than overwrite.

```text
EXPECTED A, OBSERVED C → STALE/BLOCKED
```

A failed non-fast-forward ref advance is useful evidence of concurrent movement.

## PR evidence

Record:

- PR number/URL;
- Work-Package and demand/Issue binding;
- target ref/base SHA;
- source ref/head/tree;
- changed-file identity where material;
- required checks/run IDs;
- current review/thread state;
- PR body/message digest when it participates in the protected squash result.

## Composition evidence

For integration claims bind the fields required by BADF evidence doctrine:

```yaml
git_composition:
  target_base_sha: <sha>
  source_head_sha: <sha>
  merge_base_sha: <sha>
  merge_method: squash
  expected_result_tree: <tree-sha>
  ordered_prefix_position: <n-if-applicable>
  test_set_epoch: <epoch>
  policy_epoch: <epoch>
```

Source movement, target movement, merge-method movement, material PR-message movement or relevant policy/test movement makes affected evidence stale.

## Protected integration evidence

Before merge preserve the current:

- expected PR head SHA;
- current target/composition identity;
- required status/check identities;
- independent review/challenge evidence;
- authority decision/receipt;
- unresolved-thread/condition disposition.

After merge preserve GitHub's returned/observed protected commit and tree, then reconcile expected vs actual.

## Recovery evidence

Recovery is a new operation. Record:

- triggering failure/incident;
- last known good remote ref/commit/tree;
- current remote state;
- recovery branch/ref or revert/forward-fix candidate;
- separate authority where required;
- resulting remote identities and verification.

Never mutate an earlier evidence record to make a recovery look like the original operation succeeded.

## Release evidence

Release/tag evidence binds immutable tag/ref, commit/artifact digest, release identifier, provenance/attestation where required and release authority. A corrective release receives a new identity.
