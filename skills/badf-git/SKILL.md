---
name: badf-git
description: Govern GitHub-native repository state transitions for BADF work packages from authority and remote baseline through GitHub Remote Workspace isolation, Git objects/commits, pull requests, composed-result verification, protected integration, recovery, release refs, cleanup and learning. Use whenever BADF work inspects or mutates Git/GitHub state. Do not use local git worktree as the BADF execution substrate, and do not treat Git/GitHub capability, branch ownership, CI success or repository state as authority to merge, release, deploy, waive controls or rewrite protected history.
---

# BADF Git

`badf-git` is the repository-state control skill for BADF delivery. It governs Git mechanics and GitHub collaboration; it does not grant Git, merge, release or production authority. The live lifecycle status and digest are authoritative only in `badf/skill-registry.json`.

## Fundamental rules

```text
GIT_CAPABILITY != GIT_AUTHORITY
SOURCE_HEAD_GREEN != INTEGRATION_SAFE
GITHUB_REMOTE_WORKSPACE != NATIVE_GIT_WORKTREE
```

GitHub hosts repositories, refs, commits, trees, pull requests, checks and rulesets. Native `git worktree` is a filesystem checkout mechanism and is not the BADF isolation primitive.

## Invariants

- **GIT-I01 — Authority Before Mutation:** every material Git/GitHub mutation binds to an active Work Package and permitted operation.
- **GIT-I02 — Main Is Ledger, Not Workspace:** `main` changes only through the protected PR integration path; never mutate it directly in normal operation.
- **GIT-I03 — One Work Package, One Source Ref:** material delivery work uses a dedicated topic ref/branch traceable to its Work Package.
- **GIT-I04 — GitHub Remote Workspace Isolation:** independent Work Packages/agents use distinct GitHub source refs. The canonical workspace identity is repository + target ref/base SHA + source ref/head SHA + source-head tree (+ PR identity when opened). No local worktree path, index, stash or reflog is required to establish isolation.
- **GIT-I05 — Exact-State Identity:** record exact target, source and tree identities before consequential mutation or verification.
- **GIT-I06 — Protected History Is Additive:** do not reset, rebase, force-update, delete or move protected `main` history to hide a landed error; use a governed revert/forward repair.
- **GIT-I07 — Remote Object Mutation Is Explicit:** read the exact remote object/content being changed; create/update the candidate commit/tree intentionally; advance the topic ref only from the expected prior head.
- **GIT-I08 — Conflict Resolution Is New Code:** any semantic conflict resolution invalidates affected evidence and requires verification; remembered/automated resolutions are candidates, not proof.
- **GIT-I09 — Composition Binds Integration:** verification for merge binds target base, source head, merge base, merge method and expected result tree.
- **GIT-I10 — Movement Invalidates Evidence:** target movement, source movement, PR-message movement, merge-method movement, policy movement or material test/toolchain movement makes affected evidence stale.
- **GIT-I11 — Destructive Operations Fail Closed:** protected-ref rewrites/deletions, release-tag rewrites and other destructive/admin actions are denied unless separately authorized by higher policy; local destructive cleanup is never required by this skill.
- **GIT-I12 — Separation of Duties:** authoring a Git change, reviewing it, authorizing protected integration and authorizing release are distinct functions where BADF policy requires independence.

## Outer Git Cycle

```text
AUTHORITY → BASELINE → ISOLATE → BUILD → VERIFY → PR → COMPOSE → CHALLENGE → AUTHORIZE → SQUASH → RECONCILE → RELEASE → CLEAN → LEARN
```

### AUTHORITY
Resolve Work Package, originating demand/Issue, repository, target ref, change class, scope, permitted GitHub operations, acceptance criteria, reviewers, evidence and stop conditions. Access to a GitHub write API is capability, not authority.

### BASELINE
Observe GitHub without mutation: repository/default branch, active rulesets, target ref/SHA/tree, existing source ref if any, relevant commits/compare state, PR/check state and policy epoch. Record observation time. Do not require a local checkout, working tree, index, stash or reflog.

### ISOLATE
Create or adopt one authorized GitHub topic ref such as `refs/heads/wp/<WORK-PACKAGE>-<slug>` from the exact observed target-base SHA. That remote ref is the durable BADF workspace identity. Parallel work uses separate refs; overlapping mutations require an integrator.

### BUILD
Operate against remote objects/refs. The preferred conceptual loop is:

```text
OBSERVE → READ → PATCH → BUILD TREE → CREATE COMMIT → ADVANCE REF → VERIFY → RECONCILE → ↺
```

For a ref update, bind the observed source-head SHA as the expected parent/pre-state. Use non-force advancement by default. If another actor moves the ref, stop, re-observe and reconcile instead of overwriting it.

### VERIFY
Run deterministic checks on the exact candidate revision in GitHub Actions or another registered, authorized remote runner. Preserve failing outcomes. A source check proves only that source revision.

### PR
Open/update a PR that binds Work Package, Issue/demand, target ref/base, source ref/head and verification evidence. A PR is an integration proposal, not authority.

### COMPOSE
Use BADF's canonical composition mechanism to verify the tree that would land under the protected merge method. Do not replace `scripts/badf_compose.py` with a second Git gate.

### CHALLENGE
Obtain independent review proportional to risk and declare non-coverage. Source movement makes affected reviews stale.

### AUTHORIZE
Confirm current source head, target base/composition, required checks, review state, conditions and integration authority. Green CI alone never authorizes merge.

### SQUASH
For the current BADF repository policy, protected integration is squash-only. Bind merge execution to the exact reviewed head where the platform supports expected-head checking.

### RECONCILE
Observe GitHub's landed commit/tree and reconcile it against the authorized expected result. Record PR/Issue/WP identifiers, outcome and any discrepancy. Unknown remote outcomes are queried/reconciled before retry.

### RELEASE
Release/tagging is separately authorized. Release refs are immutable identities; never move a published release tag to disguise an error.

### CLEAN
After landing and reconciliation, retire/delete the remote topic ref only when policy permits and no unique evidence depends on it. There is no BADF local-worktree cleanup requirement.

### LEARN
Promote validated Git/GitHub failure patterns, concurrency hazards, composition defects and recovery lessons through governed BADF learning/skill changes.

## Failure and recovery posture

- **Remote ref moved unexpectedly:** `STALE_EVIDENCE` or `BLOCKED`; re-observe and reconcile.
- **GitHub mutation outcome unknown:** query authoritative GitHub state before retry.
- **Topic branch damaged:** preserve known commits and create a recovery ref/branch or forward correction; do not overwrite collaborator state silently.
- **Bad change landed on `main`:** new recovery Work Package + revert/forward-fix PR against current `main`.
- **Release tag wrong:** preserve historical tag; issue a new governed release/supersession. Do not move the tag.

## References

Read only what the operation requires:

- `references/git-cycle.md` — remote Git Cycle and nested Git Loop.
- `references/git-state-machine.md` — Git/GitHub transition states and holds.
- `references/branch-pr-contract.md` — GitHub Remote Workspace, topic-ref and PR binding.
- `references/operation-authority-matrix.md` — operation classes and authority boundaries.
- `references/composition-and-staleness.md` — source/target/result identity and invalidation.
- `references/recovery-contract.md` — remote recovery without protected-history rewrite.
- `references/release-versioning.md` — version/tag/release policy.
- `references/evidence-contract.md` — Git/GitHub transition evidence.

## Non-goals

This skill does not:

- implement a local `git worktree` registry or require local worktree creation/removal;
- make local working-directory/index/stash/reflog state canonical BADF workspace state;
- create `scripts/badf_git.py` or a competing gate;
- grant GitHub mutation, merge, release or deployment authority;
- bypass repository rulesets or composed-result verification;
- claim GitHub provides native Git worktrees.

Report one explicit disposition for material Git operations: `PASS`, `FAIL`, `BLOCKED`, `STALE_EVIDENCE`, `OUTCOME_UNKNOWN`, `RECOVERY_REQUIRED`, or `HUMAN_REQUIRED`.
