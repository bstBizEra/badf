# BADF Git Cycle and Git Loop

The BADF Git Cycle is GitHub-native. GitHub refs and immutable Git objects are the durable workspace; local filesystem worktrees are not part of the control model.

## Outer cycle

```text
AUTHORITY → BASELINE → ISOLATE → BUILD → VERIFY → PR → COMPOSE → CHALLENGE → AUTHORIZE → SQUASH → RECONCILE → RELEASE → CLEAN → LEARN
```

## 1. AUTHORITY

Resolve the Work Package, demand/Issue, repository, target ref, change class, scope, allowed GitHub operations, acceptance criteria, reviewers, evidence and stop conditions. A connected GitHub tool is capability only.

## 2. BASELINE

Observe from GitHub:

- repository identity and default branch;
- active rulesets/protection relevant to the target;
- target ref, target SHA and target tree;
- source ref/head/tree if it already exists;
- commit/compare state needed to establish ancestry/divergence;
- PR, review-thread and check state if a PR exists;
- policy/test epoch and observation time.

Do not require a local checkout, working-tree status, index, stash, reflog or worktree list.

## 3. ISOLATE

Create/adopt one GitHub source ref for the authorized Work Package from the exact approved base SHA. The source ref + head/tree is the workspace boundary. Parallel work uses different refs.

## 4. BUILD

Use the remote-object loop:

```text
OBSERVE → READ → PATCH → BUILD TREE → CREATE COMMIT → ADVANCE REF → VERIFY → RECONCILE → ↺
```

The implementation may use GitHub contents operations or blob/tree/commit/ref operations, but every mutation must bind:

- expected source head before the operation;
- intended paths/content;
- resulting commit/tree;
- observed source head after the operation.

A non-fast-forward or unexpected ref movement stops the loop for reconciliation; it is never permission to force.

## 5. VERIFY

Verify the exact source revision on GitHub Actions or another authorized remote runner. Preserve source-head SHA, tree, run/check identities and outcome. Source verification is not integration verification.

## 6. PR

Bind the current source ref/head to a PR against the authorized target. The PR body remains the delivery dossier/traceability surface required by repository policy.

## 7. COMPOSE

Compute and verify the exact result that the protected merge method would land. BADF currently uses the canonical `scripts/badf_compose.py` mechanism for squash composition; `badf-git` does not create a second validator.

## 8. CHALLENGE

Run independent review proportional to risk. Reviews bind the exact source/composed identity and become stale when their material input moves.

## 9. AUTHORIZE

Merge readiness is conjunctive: current authority, current target/source/composition, current required checks, required challenge, resolved conditions/threads and no active blocker.

## 10. SQUASH

Execute only the protected merge method permitted by the active repository ruleset. Bind the merge to the exact expected PR head when supported.

## 11. RECONCILE

Observe the landed protected commit/tree from GitHub, compare it with the authorized expected result and reconcile the Work Package/Issue/PR evidence. A successful API response alone is not completion.

## 12. RELEASE

Release/tagging is a separate authority boundary. Release identities are immutable; a corrective release gets a new version/ref.

## 13. CLEAN

Delete/retire the remote topic ref only after the landing and evidence are reconciled and no unique work depends on it. No local worktree cleanup exists in this cycle.

## 14. LEARN

Promote validated lessons about ref races, stale evidence, composition defects, review drift and recovery through BADF learning governance.

## Nested Git Loop stop conditions

Stop and return an explicit hold when:

- authority/scope is missing or changed;
- source ref moved unexpectedly;
- target movement invalidates current integration evidence;
- a mutation returns an unknown outcome;
- a protected ref/tag would be rewritten/deleted;
- required checks/reviews are stale or failing;
- repeated repairs exhaust the configured attempt budget.

Each retry must change an input, hypothesis, candidate implementation or diagnostic. Blind replay of the same remote mutation is prohibited.
