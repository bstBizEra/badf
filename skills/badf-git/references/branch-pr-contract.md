# GitHub Remote Workspace, Branch and Pull Request Contract

This reference defines how a BADF Git change is isolated and bound to its Work Package on GitHub. GIT-A (WP-2026-0066) proposed the canonical branch form; GIT-B (**WP-2026-0070**) froze the machine Work-Package ID and made the form live on every pull request. GIT-A2 (WP-2026-0073) replaces local-worktree isolation with a GitHub Remote Workspace without weakening GIT-B identity enforcement.

A **GitHub Remote Workspace** is a BADF abstraction over remote refs and immutable Git objects; it is not native `git worktree`.

## Identity hierarchy

Use identity in this order:

1. **Canonical Work-Package record** — machine identity and bounded authority.
2. **Issue/demand/decision bindings** — why the work exists and what authorized it.
3. **Repository + target/source refs + SHAs/trees** — exact Git identity.
4. **Pull request ID** — review/integration vehicle.
5. **Branch name / PR title / commit message** — human-readable labels that must satisfy the live consistency contract.

A label cannot override a contradictory Work-Package record. If `WP-2026-NNNN`, `BADF-WP-NNNN`, issue metadata and branch/PR text do not map one-to-one, stop and reconcile rather than guessing.

## Canonical branch form — enforced

BADF branch naming is frozen as:

```text
wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>
```

The canonical machine ID is `WP-2026-NNNN` (`WP-2026-` is a fixed ledger namespace constant, not a calendar field), so the enforced form is:

```text
wp/WP-2026-NNNN-<slug>
```

Rules:

- `wp/` declares a bounded Work-Package topic branch, not authority level.
- `<CANONICAL-WORK-PACKAGE-ID>` must match the Work-Package artifact and body trailer exactly.
- `<short-slug>` is descriptive/disposable lowercase kebab and never an identity key.
- enforcement is live from **WP-2026-0070**: `scripts/check_pr_traceability.py` refuses a PR whose head ref/title/trailer disagree.
- historical branches are never renamed merely to conform (GIT-I06).
- no permanent `develop`, `integration`, `staging`, `alpha`, or `beta` branch represents BADF lifecycle state.

Identity consistency proves binding, never permission.

## Canonical GitHub Remote Workspace identity

```yaml
github_remote_workspace:
  work_package_id: WP-2026-NNNN
  repository: bstBizEra/badf
  target_ref: refs/heads/main
  target_base_sha: <commit-sha>
  target_base_tree: <tree-sha>
  source_ref: refs/heads/wp/WP-2026-NNNN-<slug>
  source_head_sha: <commit-sha>
  source_head_tree: <tree-sha>
  pr_number: <number-or-null>
  observed_at: <timestamp>
```

A filesystem checkout path, local index, stash or reflog is never part of canonical workspace identity.

## Remote branch creation contract

Before creating a source branch:

1. observe the intended GitHub target ref and exact target-base SHA/tree;
2. confirm the Work Package permits the repository write;
3. confirm the canonical branch name does not collide with another active Work Package/ref;
4. create the source ref directly on GitHub from that exact base SHA;
5. re-observe and record source ref/head/tree.

Branch creation is not approval to push, merge or release.

No local filesystem checkout is required to establish isolation.

## Remote mutation protocol

Normal source-ref mutation is optimistic and additive:

```text
OBSERVE source_head=A
READ exact remote content/object
PREPARE candidate change
BUILD tree T2
CREATE commit B(parent=A, tree=T2)
ADVANCE source_ref A → B without force
OBSERVE source_ref=B
```

The implementation may use registered GitHub contents operations or lower-level blob/tree/commit/ref operations. Either path must preserve expected pre-state, intended paths/content, resulting commit/tree and observed post-state.

If the source ref is no longer at the expected prior SHA, stop with `STALE_EVIDENCE`/`BLOCKED`, re-observe and reconcile. Do not convert a concurrency failure into permission to force.

## Parallel agents and overlap

- one active Work Package normally owns one source ref/workspace;
- independent agents use different refs/workspaces;
- overlapping-file edits require an explicit integrator/composition plan;
- two agents must not race by force-updating the same source ref;
- unexpected ref movement is a concurrency signal and evidence event.

If overlap appears unexpectedly, stop independent mutation and reconcile rather than racing to land first.

## Commit contract

Topic commits are working engineering history; protected `main` remains the authoritative integration ledger.

Requirements:

- mutate only intended Work-Package scope;
- bind remote pre-state and resulting commit/tree;
- preserve Work-Package traceability through workspace/PR/evidence even when internal commit messages are concise;
- do not encode secrets, tokens, personal data or transient credentials;
- do not infer authority, SemVer, risk or gate status from Conventional Commit prefixes;
- keep current protected integration squash-only unless higher repository policy changes it.

BADF does not require a local staging area to establish commit correctness. Review and verification bind the GitHub object/diff identity and exact candidate revision.

## Synchronization and target movement

`main` movement does not silently update a GitHub Remote Workspace. When the target advances:

1. mark target-bound composition evidence stale;
2. observe the new target SHA/tree and compare against the source;
3. choose an authorized synchronization strategy that preserves collaborator state;
4. recompute merge base/expected result tree and rerun affected checks/review.

A source ref need not be cosmetically rebased if current composed-result verification is valid. When source ancestry must be synchronized without rewriting its published history, an additive integration/synchronization commit may be used if authorized and independently verified. BADF cares about the current exact result, not a pretty topic graph.

## Rewriting a published topic ref

Remote-first BADF prefers additive commits. A published topic rewrite changes source identity and invalidates checks/reviews/composition.

If a rewrite is separately authorized, bind the exact expected prior remote SHA. The safety intent is equivalent to `--force-with-lease`; **Bare `--force` is not a normal BADF workflow**. `git range-diff` or equivalent can help reviewers understand a reconstructed series, but textual diagnostics never replace SHA/tree evidence.

## Publication contract

Before a remote topic mutation:

1. verify repository identity and canonical source ref;
2. observe exact current source head;
3. verify Work-Package/tool authority for the operation;
4. verify no prohibited data/secrets are introduced;
5. bind expected pre-state;
6. execute the mutation;
7. observe the authoritative remote outcome.

If the result is ambiguous or times out, query GitHub state before retrying.

## Pull request contract

A BADF PR body carries the canonical binding:

```text
Work-Package: WP-2026-NNNN
Closes #<issue-number>
```

The PR title carries the display label with the same NNNN:

```text
BADF-WP-NNNN: <concise outcome>
```

The head branch is `wp/WP-2026-NNNN-<slug>`. GIT-B enforcement is live from WP-2026-0070 and refuses mismatch among title, branch and trailer.

The PR also makes clear:

- objective/outcome, scope and non-goals;
- target ref/current composition base;
- source ref and exact reviewed head/tree;
- demand/Issue binding;
- acceptance criteria and affected controls/contracts;
- verification performed and unrun surfaces;
- composed-result identity/status;
- risk/change class;
- required independent review;
- rollback/recovery path;
- residual risks/unknowns;
- what the PR does **not** authorize.

A PR is an integration proposal/evidence surface, never merge authority.

## PR/source movement contract

Any source movement after verification/review can invalidate:

- source verification;
- review findings/approvals;
- composition evidence/expected result tree;
- merge authorization.

After movement capture the new head/tree, classify stale evidence, recompute composition against current target and rerun required verification/challenge.

## Merge contract

The PR author and this skill do not self-authorize protected integration.

At merge time require:

- exact expected PR head;
- current target/base observation;
- current composition evidence;
- current required checks;
- current independent approvals/challenge;
- no blocking thread/condition;
- repository-approved merge method;
- authorized integration actor.

Where GitHub supports an expected head SHA, use it so moved source state is rejected rather than accidentally merged.

Under the current BADF repository contract protected integration is squash-only.

## Cleanup

Retire/delete a remote topic ref only after:

- merge/abandon outcome is authoritative and known;
- no recovery/evidence need remains;
- required reconciliation is complete.

Cleanup never erases PRs, commits, evidence or Work-Package audit records. BADF has no local-worktree cleanup requirement.

## Explicit non-goal

GitHub does not provide a persistent native Git worktree object. BADF therefore must not implement local worktree path conventions, local worktree registries, local-worktree cleanup automation or local checkout state as GitHub Remote Workspace governance.
