# Git Evidence Contract

BADF Git evidence must prove exact repository state and operation outcomes without inventing a second evidence schema. Canonical evidence remains `schemas/evidence.schema.json` plus the applicable gate/release schemas. This reference defines the Git-specific bindings that must be carried in those records or their artifacts when relevant.

## Evidence principle

A Git claim must answer:

- which work package?
- which repository?
- which target/source refs?
- which exact before/source/target revisions?
- which operation and tool?
- under which policy/test/toolchain epoch?
- what outcome actually occurred?
- which composed result was tested?
- which evidence became stale because of the operation?
- which actor/authority supplied approval versus implementation?

A URL or branch name without exact revision/result identity is a pointer, not sufficient proof.

## Minimum Git operation record

For a material Git mutation, capture at minimum:

```yaml
git_operation:
  work_package_id: WP-2026-0066
  repository: bstBizEra/badf
  actor: <principal>
  tool: <tool-id/version>
  canonical_operation_class: WRITE
  git_operation_class: GIT-O3
  target: refs/heads/wp/WP-2026-0066-git-contract-freeze
  before_revision: <sha-or-null>
  after_revision: <sha-or-null-if-unknown>
  command_or_operation: <sanitized-command-or-api-operation>
  started_at: <ISO-8601>
  completed_at: <ISO-8601-or-null>
  outcome: <PASS|FAIL|BLOCKED|OUTCOME_UNKNOWN>
  returned_identifier: <remote-id-or-null>
  invalidated_evidence: []
```

The actual evidence object must use the canonical schema's allowed fields; Git-specific detail can be placed in the referenced artifact when the core schema does not have dedicated properties.

## Baseline evidence

A Git baseline artifact should record:

```yaml
baseline:
  repository: bstBizEra/badf
  observed_at: <ISO-8601>
  worktree_path: <local-operational-path-if-safe>
  branch: <branch-or-detached>
  head_sha: <sha>
  target_ref: refs/heads/main
  target_sha: <sha>
  source_ref: <ref-or-null>
  source_sha: <sha-or-null>
  merge_base_sha: <sha-or-null>
  index_state: <clean|changed|unknown>
  worktree_state: <clean|changed|unknown>
  untracked_state: <none|present|unknown>
  remote_freshness: <observation>
  policy_epoch: <epoch>
  test_set_epoch: <epoch>
```

Do not place secrets, credentials or raw sensitive content in baseline artifacts.

## Composition evidence

For protected integration, bind:

```yaml
git_composition:
  repository: bstBizEra/badf
  target_ref: refs/heads/main
  target_base_sha: <sha>
  source_ref: refs/heads/wp/...
  source_head_sha: <sha>
  merge_base_sha: <sha>
  merge_method: squash
  expected_result_tree: <tree-sha>
  ordered_prefix_position: <integer>
  test_set_epoch: <epoch>
  policy_epoch: <epoch>
  composition_tool: <canonical-tool/version>
  verification_outcome: <PASS|FAIL|BLOCKED>
```

For BADF repository changes, use the existing canonical composition mechanism (currently `scripts/badf_compose.py` in CI) rather than creating a skill-specific validator.

## Pull request evidence

A PR-bound evidence artifact should record:

```yaml
pull_request_binding:
  repository: bstBizEra/badf
  pr_number: <number>
  work_package_id: <canonical-id>
  issue_or_demand: <id/ref>
  target_ref: refs/heads/main
  source_ref: <topic-ref>
  source_head_sha: <sha>
  review_revision: <sha>
  required_checks: [<check>]
  approvals: [<receipt/ref>]
  unresolved_conditions: []
```

PR text is useful context but exact review/head identity is required when approval/evidence depends on the reviewed revision.

## History-rewrite evidence

When a permitted private rewrite occurs, record:

- old source head;
- new source head;
- rewrite type (`amend`, `rebase`, `rebase-i`, `reset-rebuild`, `cherry-pick-rebuild`, etc.);
- whether remote topic history was also updated;
- expected remote head/lease if a remote overwrite occurred;
- preserved recovery ref when applicable;
- evidence/reviews/composition invalidated;
- diagnostic comparison reference such as `range-diff` if useful.

Example:

```yaml
rewrite:
  old_source_head: <sha-a>
  new_source_head: <sha-b>
  kind: rebase
  recovery_ref: refs/heads/recovery/WP-...
  range_diff_artifact: <path-or-null>
  invalidated_evidence:
    - EVD-...
    - review:<id>
    - composition:<id>
```

`range-diff` output is explanatory evidence, not the stable identity of the rewritten change.

## Recovery evidence

A recovery artifact should distinguish:

```yaml
recovery:
  trigger: <what-went-wrong>
  scope: local|topic|protected|release
  before_state: <ref/artifact>
  authoritative_state: <ref/artifact>
  preserved_state: <recovery-ref/artifact>
  operation_class: <GIT-O*>
  recovery_action: <sanitized-operation>
  after_state: <ref/artifact>
  verification: <ref/outcome>
  residual_uncertainty: []
```

If recovery remains uncertain, keep `RECOVERY_REQUIRED`/`BLOCKED`. Do not manufacture a PASS to close the record.

## Merge evidence

Immediately before merge, evidence should be sufficient to prove:

- exact PR source head;
- current target/composition identity;
- current required checks;
- current approvals/review state;
- expected result tree;
- repository-approved merge method;
- merge authority receipt/actor;
- no unresolved blocking condition.

After merge, record:

```yaml
merge_result:
  pr_number: <number>
  expected_head_sha: <sha>
  target_ref: refs/heads/main
  merge_method: squash
  platform_outcome: <success|failure|unknown>
  landed_commit_sha: <sha-or-null>
  landed_result_tree: <tree-or-null>
  expected_result_tree: <tree>
  reconciliation: <MATCH|MISMATCH|UNKNOWN>
```

A successful platform merge response with `MISMATCH` or unknown result reconciliation cannot support a completed integration claim.

## Release evidence

When release is in scope, record the binding described in `release-versioning.md`, including version/tag, verified `main` source revision/result tree, immutable artifact digest, SBOM/provenance, change/release authority and release record.

Do not create a second release schema here. Use canonical BADF release/evidence records when they exist.

## Staleness metadata

Evidence that becomes stale is preserved and explicitly superseded.

Record:

```yaml
staleness:
  status: STALE
  reason: target_moved|source_rewritten|source_changed|policy_changed|test_epoch_changed|merge_method_changed|composition_order_changed|review_stale
  detected_at: <ISO-8601>
  superseded_by: <new-evidence-ref-or-null>
```

Never edit old evidence in place to replace its original source/target identity.

## Outcome vocabulary

For command/check reporting, use BADF's exact completion vocabulary where applicable:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_RUN`

For state-machine routing, additional hold conditions such as `STALE_EVIDENCE`, `RECOVERY_REQUIRED`, `HUMAN_REQUIRED`, and `OUTCOME_UNKNOWN` describe why progression stopped; they do not overwrite the underlying command result.

Example:

```text
command: python3 scripts/badf_gate.py repo
result: PASS
composition status: STALE_EVIDENCE (target moved after this run)
```

Both facts can be true.

## Provenance requirements

Prefer immutable/content-addressed evidence. Record:

- producer principal/type;
- tool and version;
- source revision;
- target;
- command/API operation;
- timestamps;
- exit code/platform result;
- stdout/stderr or sanitized artifact where appropriate;
- SHA-256 digest of the retained artifact;
- policy/schema/test epoch.

Do not rely on memory or chat summaries as proof when an immutable repository/CI/platform artifact is available.

## Secret and privacy handling

Git evidence must not capture:

- access tokens;
- OAuth credentials;
- SSH private keys;
- secret environment values;
- private personal data not approved for the evidence store;
- sensitive command output beyond the minimum needed to prove the claim.

Sanitize commands/logs before retention. A secret discovered in output triggers security handling; do not preserve it in ordinary evidence merely for reproducibility.

## Failed and unknown outcomes

Failures are evidence. Preserve:

- the exact attempted operation;
- before identity;
- failure/timeout message (sanitized);
- whether the remote result is known;
- observation performed before retry;
- next safe action.

For ambiguous remote writes:

```text
TIMEOUT != FAILURE
TIMEOUT != SUCCESS
```

Set `OUTCOME_UNKNOWN`, observe the authoritative remote state, then decide whether a retry is safe.

## Evidence ownership and approval separation

The implementer can produce Git/build/test evidence. The implementer cannot transform that evidence into an independent approval for the same gate/change when independence is required.

Keep distinct:

```text
IMPLEMENTATION EVIDENCE
REVIEW EVIDENCE
AUTHORITY RECEIPT
PLATFORM INTEGRATION RESULT
```

Their coexistence supports a decision; none silently substitutes for the others.
