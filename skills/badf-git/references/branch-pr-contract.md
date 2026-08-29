# Branch, Worktree and Pull Request Contract

This reference defines how a BADF Git change is isolated and bound to its work package. GIT-A (WP-2026-0066) proposed the canonical branch form and deferred enforcement; GIT-B (**WP-2026-0070**) froze the machine work-package id and made the form live on every pull request.

## Identity hierarchy

Use identity in this order:

1. **Canonical work-package record** — machine identity and bounded authority.
2. **Issue/demand/decision bindings** — why the work exists and what authorized it.
3. **Repository + target/source refs + SHAs** — exact Git identity.
4. **Pull request ID** — review/integration vehicle.
5. **Branch name / PR title / commit message** — human-readable labels only.

A label cannot override a contradictory work-package record. If `WP-2026-NNNN`, `BADF-WP-NNNN`, issue metadata and branch/PR text do not map one-to-one, stop and reconcile the identity rather than guessing.

## Proposed canonical branch form

BADF branch naming is frozen as:

```text
wp/<CANONICAL-WORK-PACKAGE-ID>-<short-slug>
```

The canonical machine ID is `WP-2026-NNNN` (`WP-2026-` is a fixed ledger namespace constant, not a calendar field), so the enforced form is `wp/WP-2026-NNNN-<slug>` — for example:

```text
wp/WP-2026-0066-git-contract-freeze
```

Rules:

- `wp/` declares a bounded work-package topic branch, not authority level.
- `<CANONICAL-WORK-PACKAGE-ID>` must match the work-package artifact exactly.
- `<short-slug>` is descriptive and disposable; it is never an identity key. It is lowercase kebab (`[a-z0-9]+(-[a-z0-9]+)*`).
- enforcement is live from WP-2026-0070: `scripts/check_pr_traceability.py` refuses a pull request whose head ref is not `wp/WP-2026-NNNN-<slug>`, or whose NNNN differs from the body trailer's. Historical branches are never renamed (GIT-I06).
- no permanent `develop`, `integration`, `staging`, `alpha`, or `beta` branch is introduced to represent lifecycle state.

Identity is frozen, but a branch name is still a label: tooling reads the canonical work-package artifact/body binding and **must not infer authority from branch regex alone** — the regex proves consistency, never permission.

## Branch creation contract

Before creating a branch:

- observe the intended target/base SHA;
- confirm the work package permits a local/repository write;
- confirm the branch name does not collide with another active work package;
- preserve existing worktree/index state;
- create from the intended authorized baseline, not from an arbitrary local tip.

Record:

```yaml
branch_binding:
  work_package_id: WP-2026-0066
  repository: bstBizEra/badf
  target_ref: refs/heads/main
  target_base_sha: <sha>
  source_ref: refs/heads/wp/WP-2026-0066-git-contract-freeze
  created_from_sha: <sha>
```

Branch creation is not approval to push or merge.

## Worktree contract

For parallel work, prefer a dedicated `git worktree` per independent branch/work package.

### Why

A worktree gives each agent/change:

- a distinct filesystem root;
- an explicit checked-out branch;
- less accidental overlap than sharing one checkout and repeatedly switching branches;
- easier preservation of uncommitted state;
- a clearer evidence target.

### Rules

- one agent/work package owns one active worktree unless an explicit integrator plan says otherwise;
- do not point two worktrees at overlapping mutable output directories without coordination;
- do not use worktree removal as cleanup while uncommitted/unknown work remains;
- worktree path is operational metadata, not a durable identity; branch/SHA/work-package bindings are durable;
- if a worktree appears stale, inspect before pruning; pruning is cleanup, not diagnosis.

## Overlap and composition

Parallel agents must not edit overlapping files unless the work package or integrator plan explicitly names:

- file/path overlap;
- integration owner;
- composition order;
- conflict-resolution owner;
- checks that must be rerun after reconciliation.

If overlap appears unexpectedly, stop independent mutation and enter reconciliation. Do not race to land first.

## Commit contract

Branch commits are **working engineering history**. Protected `main` is the authoritative integration ledger.

Commit requirements:

- commit only intended staged content;
- inspect staged diff first;
- preserve traceability to the work package in the PR/evidence even when individual local commit messages are concise;
- do not encode secrets, tokens, personal data, or transient credentials in messages/content;
- do not use a Conventional Commit prefix or any message style as authority evidence;
- do not require noisy mechanical commit history on `main`; current protected integration remains squash-only.

### Conventional Commits

Conventional Commit prefixes may be used on internal/topic commits when useful to humans or tooling, but BADF does not infer SemVer, authority, risk class, or gate status solely from `feat:`, `fix:`, `chore:` or similar prefixes.

### Rewriting private branch commits

Rebase/amend/squash/fixup may be allowed only when:

- the branch is unmerged and not protected;
- the work package permits the operation;
- collaborators are not silently losing shared history;
- the rewritten source is republished only through an authorized remote-topic update;
- affected evidence/reviews/composition are treated as stale and recomputed.

Use `git range-diff` or equivalent as a **diagnostic** after a rebase to help reviewers understand how a patch series changed. Its textual output is not a stable identity and must not replace SHA/tree/evidence bindings.

If a rewritten remote topic branch must be updated, `--force-with-lease` is the maximum normal force boundary because it checks an expected remote state. Bare `--force` is not a normal BADF workflow. Neither form grants permission; remote mutation still requires work-package/tool authority.

## Publication contract

Before pushing a topic branch:

1. verify repository/remote identity;
2. verify source ref and exact head;
3. fetch/observe relevant remote state;
4. confirm the work package permits remote-topic mutation;
5. verify no prohibited data/secrets are included;
6. record the push operation/outcome.

If push returns an ambiguous failure/timeout, observe the remote ref before retrying. A retry without observation can duplicate or overwrite state.

## Pull request contract

A BADF pull request should carry, in a machine- or reviewer-readable form:

```text
Work-Package: <canonical work-package ID>
Closes #<issue-number>
```

and must make clear:

- objective/outcome;
- source branch and exact reviewed head;
- target branch;
- scope and non-goals;
- affected controls/contracts;
- acceptance criteria;
- verification performed and unrun checks;
- composed-tree status/evidence;
- risk/change class;
- required independent review;
- rollback/recovery path;
- residual risks/unknowns;
- authority boundary (what the PR does not authorize).

The PR title must carry the display label, with the same NNNN as the trailer and the branch (enforced from WP-2026-0070):

```text
BADF-WP-0066: <concise outcome>
```

The label is human-facing only; it maps to the canonical machine work-package ID by NNNN. The PR body trailer `Work-Package: WP-2026-NNNN` (the display form there is refused) and the work-package artifact remain authoritative.

## PR update contract

Any source push after PR review can invalidate:

- source-level verification;
- review findings/approvals according to repository policy;
- composition evidence;
- expected result tree;
- merge authorization.

After source movement:

1. capture the new source head;
2. classify what prior evidence is stale;
3. recompute composition against current target;
4. rerun required checks;
5. repeat required review/authorization.

A tiny commit is still source movement.

## Target movement contract

When `main` advances while a PR is open:

- do not assume the source branch remains integration-safe;
- recompute merge base and expected result tree against current `main`;
- rerun composed checks required by policy;
- record the new target base and invalidate superseded composition evidence.

Whether the source branch itself must be rebased is a separate decision. BADF cares about the **current composed result**, not cosmetic branch freshness by itself.

## Merge contract

The PR author and the skill do not self-authorize protected integration.

At merge time require:

- exact expected head;
- current target/base observation;
- current required checks;
- current independent approvals;
- no unresolved review threads/conditions as required by policy;
- repository-approved merge method;
- composition evidence for the current identities;
- authorized integration actor.

Under the current BADF repository contract, protected integration is squash-only. A future ratified policy can change the repository setting; this skill must follow the higher authority rather than silently retaining stale assumptions.

## Branch cleanup

Delete topic branches/worktrees only after:

- merge/abandon outcome is authoritative and known;
- no recovery/evidence need remains;
- no unknown/uncommitted work exists;
- required reconciliation is complete.

Cleanup is not evidence erasure. PRs, commits, evidence and work-package records remain the audit trail.
