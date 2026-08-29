---
name: badf-git
description: Govern GitHub-native repository state transitions for BADF work packages from authority and remote baseline through GitHub Remote Workspace isolation, Git objects and commits, pull requests, composed-result verification, protected integration, recovery, tags, release refs, cleanup and learning. Use whenever BADF work inspects or mutates Git/GitHub state or makes a claim about repository history or integration readiness. Do not use local git worktree as the BADF execution substrate, and do not treat Git/GitHub capability, branch ownership, CI success or repository state as authority to merge, release, deploy, waive controls or rewrite protected history.
---

# BADF Git

`badf-git` is the declarative Git/GitHub contract for BADF delivery work. It coordinates repository actions with the repository charter, canonical Work-Package identity, evidence binding, composed-tree verification and protected integration. It is a **router and constraint layer**, not Git authority, a merge bot, release authority or a second gate.

The skill's admission status is recorded in `badf/skill-registry.json`; this file defines behavior and must not hardcode a lifecycle status that can drift from the registry.

## Fundamental rules

```text
GIT_CAPABILITY != GIT_AUTHORITY
SOURCE_HEAD_GREEN != INTEGRATION_SAFE
GITHUB_REMOTE_WORKSPACE != NATIVE_GIT_WORKTREE
REUSED_RESOLUTION != VERIFIED_RESOLUTION
MERGED != RELEASED
RELEASED != PRODUCTION_VERIFIED
```

GitHub hosts repositories, refs, commits, trees, pull requests, checks, workflow runs and rulesets. Native `git worktree` is a filesystem checkout mechanism and is not the BADF isolation primitive.

## Required reading

Before a material Git/GitHub operation:

1. Read repository `AGENTS.md` and its applicable instruction chain.
2. Read `docs/00-operating-model.md`, `docs/01-lifecycle-gates.md`, `docs/02-engineering-loop.md`, `docs/05-evidence-and-provenance.md`, `docs/07-skills-governance.md`, `docs/08-mcp-and-tools.md`, and `docs/13-artifact-model.md` as applicable.
3. Resolve the active Work Package, target gate, change class, repository, target ref, permitted tools/environments/mutations, acceptance criteria, evidence requirements, rollback, reviewers and stop conditions.
4. Treat repository settings, rulesets, branch protection, tool registration, authority matrix and platform controls as higher authority than this skill.

## Invariants

```text
GIT-I01 — No Git Authority
  This skill can guide, constrain and document Git/GitHub operations. It MUST
  NOT grant repository, credential, merge, release, production, policy,
  bypass, destructive or administrative authority.

GIT-I02 — Source Head Is Not Integration Safety
  A green source revision is insufficient. Integration evidence binds the
  intended target base, source head, merge base, merge method, expected result
  tree, policy epoch and test-set epoch.

GIT-I03 — Exact Identity
  Every material Git change binds one canonical Work-Package machine identity,
  one repository, target ref, source ref, before/after revision and evidence
  set. Display labels and branch names prove consistency, never authority.

GIT-I04 — GitHub Remote Workspace Isolation
  Independent Work Packages/agents use distinct GitHub source refs. The
  canonical workspace identity is repository + target ref/base SHA/tree +
  source ref/head SHA/tree (+ PR identity when opened). A local worktree path,
  local index, stash or reflog is not required to establish isolation.

GIT-I05 — Movement Or Rewrite Invalidates Evidence
  Source movement, target movement, history rewrite, material PR-message
  movement, merge-method change, policy movement or material test/toolchain
  movement makes affected evidence stale until recomputed.

GIT-I06 — Shared History Repairs Forward
  Protected/shared history is not rewritten. Normal rollback of landed work is
  a new governed revert or forward repair. Remote topic recovery preserves
  known commits and uses a recovery/source ref rather than hiding history.

GIT-I07 — Intentional Remote Object Mutation
  Read the exact remote object/content being changed; build the intended
  candidate tree/commit; advance a topic ref only from the expected prior head.
  Unexpected ref movement stops mutation for re-observation and reconciliation.

GIT-I08 — Conflict Resolution Is New Code
  Any semantic conflict resolution, remembered or automated, is a candidate
  change. Inspect it, bind it to a new source identity and rerun affected
  verification; reuse is not evidence of correctness.

GIT-I09 — Exact Protected Integration
  Protected integration uses the repository-approved merge method and the
  exact reviewed head against current composed evidence. Source, target,
  rules, policy or evidence drift makes prior merge authorization stale.

GIT-I10 — Release Refs Are Governance Artifacts
  Release tags and release records bind an authorized, verified `main`
  revision and immutable release evidence. Knowing a tag/release operation
  never creates release authority.

GIT-I11 — Destructive Git Is Deny By Default
  Forced protected-ref movement, protected-ref deletion, release-tag rewrite,
  ruleset bypass and equivalent destructive/admin operations require separately
  granted authority and exact target verification. They are never normal WP flow.

GIT-I12 — No Second Gate Or Mutation Engine
  `badf-git` does not introduce a competing Git validator, lifecycle gate,
  ruleset, authority matrix, tool permission, workflow controller, merge bot or
  release bot. Deterministic enforcement belongs in existing canonical controls
  through separately authorized work.
```

## Governed Git cycle

Use the outer delivery cycle:

`AUTHORITY → BASELINE → ISOLATE → BUILD → VERIFY → PR → COMPOSE → CHALLENGE → AUTHORIZE → SQUASH → RECONCILE → RELEASE → CLEAN → LEARN`

`RELEASE` is optional for a Work Package that does not produce a release. Protected integration uses the repository-approved method; under the current BADF integration contract that method is squash.

Read `references/git-cycle.md` and `references/git-state-machine.md` for stage and hold semantics.

## Nested GitHub Remote Workspace loop

Within `BUILD` and reconciliation work, use:

`OBSERVE → READ → PATCH → BUILD TREE → CREATE COMMIT → ADVANCE REF → VERIFY → RECONCILE → ↺`

The implementation may use registered GitHub contents operations or Git-data blob/tree/commit/ref operations. Every remote mutation binds its expected pre-state and observed post-state. Each retry must change an input, hypothesis, implementation or diagnostic; blind replay of the same uncertain mutation is prohibited.

## Operation classes

Use `references/operation-authority-matrix.md` only to describe risk/routing:

- `GIT-O0 REMOTE_OBSERVE`
- `GIT-O1 REMOTE_WORKSPACE_MUTATION`
- `GIT-O2 REMOTE_TOPIC_REWRITE`
- `GIT-O3 COLLABORATION_MUTATION`
- `GIT-O4 PROTECTED_INTEGRATION`
- `GIT-O5 DESTRUCTIVE_ADMIN`

These classes do not replace canonical `READ`, `WRITE`, `DESTRUCTIVE`, `ADMIN` tool governance and do not assign approval rights.

## Workflow

1. **AUTHORITY** — resolve canonical Work-Package identity, demand/Issue, repository, target, permitted GitHub operations and reserved decisions. Stop on ambiguity.
2. **BASELINE** — observe GitHub repository/default branch, active rulesets, target ref/SHA/tree, source ref/head/tree if present, relevant compare/PR/check state, policy/test epoch and observation time. Do not require a local checkout, index, stash, reflog or worktree list.
3. **ISOLATE** — create/adopt the enforced `wp/WP-2026-NNNN-<slug>` GitHub topic ref from the exact observed target-base SHA. That remote ref is the durable workspace boundary. Parallel work uses separate refs.
4. **BUILD** — follow the remote-object loop. For ref advancement, bind the observed source head as expected pre-state. Use non-force advancement by default; concurrent movement fails closed.
5. **VERIFY** — run deterministic checks on the exact candidate revision in GitHub Actions or another registered authorized remote runner. A source pass proves only that source revision.
6. **PR** — bind the PR title, canonical machine trailer, source branch/head, target, demand/Issue, scope, evidence and explicit non-goals according to the live GIT-B identity contract in `references/branch-pr-contract.md`.
7. **COMPOSE** — compute and verify the exact expected integrated result using canonical BADF composition. Do not create `scripts/badf_git.py`.
8. **CHALLENGE** — obtain required independent review. Reviews bind exact source/composed identity and become stale after material movement.
9. **AUTHORIZE** — verify current source head, target, composition, rules, checks, reviews, conditions and separate integration authority.
10. **SQUASH** — integrate only through the repository-approved protected method and only with separately granted integration authority; bind expected PR head where supported.
11. **RECONCILE** — observe the actual landed protected commit/tree from GitHub and compare it with the authorized expected result and Work-Package acceptance criteria. Unknown remote outcomes are queried before retry.
12. **RELEASE** — when in scope, bind an authorized version/tag/release to verified `main`; release identity is immutable.
13. **CLEAN** — retire/delete the remote topic ref only after authoritative landing/abandonment and reconciliation. There is no BADF local-worktree cleanup requirement.
14. **LEARN** — promote validated ref-race, stale-evidence, composition, recovery and review-drift lessons through governed BADF learning work.

## Evidence and staleness

Read `references/evidence-contract.md`. For composed changes the minimum binding includes:

```yaml
git_composition:
  target_ref: refs/heads/main
  target_base_sha: "<sha>"
  merge_base_sha: "<sha>"
  source_ref: refs/heads/wp/...
  source_head_sha: "<sha>"
  merge_method: squash
  expected_result_tree: "<git-tree-sha>"
  test_set_epoch: "<epoch>"
  policy_epoch: "<epoch>"
```

Movement invalidates affected evidence; recompute rather than relabel stale evidence as current.

## Recovery

Read `references/recovery-contract.md` before an operation intended to undo, restore or force state. Shared rollback and remote topic recovery are different contracts. Local reflog/index/stash state is not the canonical GitHub Remote Workspace recovery source.

## Stop states

Stop mutation and emit the applicable disposition when:

- required authority or tool permission is missing → `BLOCKED` or `HUMAN_REQUIRED`;
- target/source/Work-Package identity is ambiguous or concurrently claimed → `BLOCKED`;
- target/source/policy/test identity moved after evidence → `STALE_EVIDENCE`;
- a remote mutation outcome is uncertain → `OUTCOME_UNKNOWN`, then observe GitHub before retry;
- preservation/restoration requires destructive scope outside authority → `RECOVERY_REQUIRED`;
- protected-history rewrite, release-tag rewrite or repository-policy bypass would be required → `HUMAN_REQUIRED` or `BLOCKED`;
- evidence contradicts the intended merge/release claim → `BLOCKED`.

## References

- `references/git-cycle.md` — outer Git delivery cycle and GitHub Remote Workspace loop.
- `references/git-state-machine.md` — states, transitions, stale/hold semantics.
- `references/branch-pr-contract.md` — canonical WP identity, GitHub Remote Workspace, branch and PR binding.
- `references/operation-authority-matrix.md` — remote Git/GitHub operation risk classes.
- `references/composition-and-staleness.md` — composed-result identity and invalidation.
- `references/recovery-contract.md` — remote recovery and forward-repair boundaries.
- `references/release-versioning.md` — release/tag/version design contract.
- `references/evidence-contract.md` — Git/GitHub evidence and provenance fields.

## Non-goals

This skill does not implement a local `git worktree` registry, require local worktree creation/removal, make local working-directory/index/stash/reflog state canonical, grant GitHub mutation/merge/release/deployment authority, weaken rulesets/composed verification, or claim GitHub provides native Git worktrees.
