---
name: badf-git
description: Govern Git state, worktrees, branches, staging, commits, synchronization, private-history rewrites, pull requests, composition verification, integration, recovery, tags, and release refs for BADF work packages. Use whenever a BADF task changes Git state or makes a claim about repository history or integration readiness. Do not use to grant authority, bypass repository rules, rewrite protected history, or substitute source-branch success for composed-result evidence.
---

# BADF Git

`badf-git` is the declarative Git contract for BADF delivery work. It coordinates Git actions with the repository charter, work-package authority, evidence binding, composed-tree verification, and protected integration. It is a **router and constraint layer**, not a Git authority, merge bot, release authority, or second gate.

The skill's admission status is recorded in `badf/skill-registry.json`; this file defines behavior and must not hardcode a lifecycle status that can drift from the registry.

## Fundamental rule

```text
GIT_CAPABILITY != GIT_AUTHORITY
SOURCE_HEAD_GREEN != INTEGRATION_SAFE
REUSED_RESOLUTION != VERIFIED_RESOLUTION
MERGED != RELEASED
RELEASED != PRODUCTION_VERIFIED
```

## Required reading

Before a material Git operation:

1. Read repository `AGENTS.md` and its applicable instruction chain.
2. Read `docs/00-operating-model.md`, `docs/01-lifecycle-gates.md`, `docs/02-engineering-loop.md`, `docs/05-evidence-and-provenance.md`, `docs/07-skills-governance.md`, `docs/08-mcp-and-tools.md`, and `docs/13-artifact-model.md` as applicable.
3. Resolve the active work package, target gate, change class, repository, target ref, permitted tools/environments/mutations, acceptance criteria, evidence requirements, rollback, reviewers, and stop conditions.
4. Treat repository settings, rulesets, branch protection, tool registration, authority matrix, and platform controls as higher authority than this skill.

## Invariants

```text
GIT-I01 — No Git Authority
  This skill can guide, constrain and document Git operations. It MUST NOT
  grant repository, credential, merge, release, production, policy, bypass,
  destructive or administrative authority.

GIT-I02 — Source Head Is Not Integration Safety
  A green source branch is insufficient. Integration evidence binds the
  intended target base, source head, merge base, merge method, expected result
  tree, policy epoch and test-set epoch.

GIT-I03 — Exact Identity
  Every material Git change binds one canonical work-package identity, one
  repository, target ref, source ref, before/after revision and evidence set.
  Display labels and branch names are not authority records.

GIT-I04 — Isolation By Default
  Independent agents or work packages use distinct branches and worktrees.
  Overlapping edits require an explicit integrator/composition plan.

GIT-I05 — History Rewrite Invalidates Evidence
  Rebase, amend, reset, cherry-pick or any equivalent source-history change
  makes affected source-head/composition evidence stale until recomputed.

GIT-I06 — Shared History Repairs Forward
  Protected/shared history is not rewritten. Normal rollback of landed work is
  a new forward change, normally a revert. Local lost work is recovered from
  reflog or a recovery branch before destructive cleanup is considered.

GIT-I07 — Intentional Staging
  Inspect the worktree and staged diff before commit. Do not discard unrelated
  state to obtain a clean checkout. `git stash` is not durable handoff or proof.

GIT-I08 — Reused Resolution Is A Candidate
  `rerere` may recall a prior conflict resolution, but recalled content is
  inspected and tested like any new edit. Auto-staging a recalled resolution is
  not evidence of correctness.

GIT-I09 — Exact Protected Integration
  Protected integration must use the repository-approved merge method and the
  exact reviewed head against current composed evidence. Source, target, rules,
  policy or evidence drift makes prior merge authorization stale.

GIT-I10 — Release Refs Are Governance Artifacts
  Release tags and release records bind an authorized, verified `main`
  revision and immutable release evidence. This skill cannot create release
  authority merely by knowing a tag or release command.

GIT-I11 — Destructive Git Is Deny By Default
  Hard reset, destructive clean, forced protected-ref movement, tag rewrite and
  equivalent hard-to-reverse operations require separately granted destructive
  or administrative authority and exact target verification.

GIT-I12 — No Second Gate Or Mutation Engine
  `badf-git` does not introduce a competing Git validator, lifecycle gate,
  ruleset, authority matrix, tool permission, workflow controller, merge bot or
  release bot. Deterministic enforcement belongs in existing canonical controls
  through separately authorized work.
```

## Governed Git cycle

Use the outer delivery cycle:

`AUTHORITY → BASELINE → ISOLATE → BUILD → VERIFY → PR → COMPOSE → CHALLENGE → AUTHORIZE → SQUASH → RECONCILE → RELEASE → CLEAN → LEARN`

`RELEASE` is optional for a work package that does not produce a release. Protected integration uses the repository-approved method; under the current BADF integration contract that method is squash.

Read `references/git-cycle.md` and `references/git-state-machine.md` for the stage contract and hold/failure states.

## Nested Git loop

Within `BUILD` and reconciliation work, use:

`SYNC → INSPECT → EDIT → STAGE → DIFF → COMMIT → VERIFY → RECONCILE → ↺`

Each retry must change a hypothesis, implementation, input, conflict resolution, diagnostic, or evidence set. Repeating the same failing Git action without new information is not progress.

## Operation classes

Use the Git-local classification in `references/operation-authority-matrix.md` only to describe risk and routing:

- `GIT-O0 OBSERVE`
- `GIT-O1 LOCAL_REVERSIBLE`
- `GIT-O2 HISTORY_REWRITE_PRIVATE`
- `GIT-O3 REMOTE_TOPIC_MUTATION`
- `GIT-O4 PROTECTED_INTEGRATION`
- `GIT-O5 DESTRUCTIVE`

These classes **do not replace** the canonical tool classes in `docs/08-mcp-and-tools.md` (`READ`, `WRITE`, `DESTRUCTIVE`, `ADMIN`) and do not assign approval rights. The work package, tool registry, authority matrix, repository policy, and platform controls decide what is permitted.

## Workflow

1. **AUTHORITY** — resolve work-package identity, repository, target, permitted Git operations and reserved decisions. Stop when any mutation authority is ambiguous.
2. **BASELINE** — capture repository identity, target ref/SHA, source ref/SHA if it exists, merge base, worktree/index state, relevant rules/policy epoch, and remote freshness.
3. **ISOLATE** — use a short-lived work-package branch and, for parallel work, a dedicated worktree. Preserve unrelated state.
4. **BUILD** — follow the nested Git loop. Stage intentionally and keep commits coherent enough to review and recover.
5. **VERIFY** — run targeted checks, then required repository checks. A local/source pass is evidence about that source only.
6. **PR** — bind the pull request to the canonical work package, issue/demand, target, source head, scope, evidence and explicit non-goals. See `references/branch-pr-contract.md`.
7. **COMPOSE** — compute and verify the expected integrated result using the canonical BADF composition mechanism. See `references/composition-and-staleness.md`.
8. **CHALLENGE** — obtain required independent review. The author cannot provide an independent approval for their own change.
9. **AUTHORIZE** — verify current head, target, rules, checks, approvals and evidence. Stale identity or evidence returns to reconciliation.
10. **SQUASH** — integrate only through the repository-approved protected method and only with separately granted integration authority. This skill never self-authorizes merge.
11. **RECONCILE** — verify the actual landed revision/result and reconcile it with the expected composed result and work-package acceptance criteria.
12. **RELEASE** — when in scope, bind an authorized version/tag/release to verified `main`; see `references/release-versioning.md`.
13. **CLEAN** — remove only known, merged, disposable local/topic state. Unknown work is preserved and investigated, never silently discarded.
14. **LEARN** — record validated Git failure/recovery/composition patterns through governed learning work; do not mutate policy from a single anecdote.

## Evidence and staleness

Read `references/evidence-contract.md`. For composed changes, the minimum Git composition binding includes:

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

Target movement, source movement, history rewrite, merge-method change, policy/test epoch change, or a different conflict resolution invalidates affected composition evidence. Recompute; do not relabel stale evidence as current.

## Recovery

Read `references/recovery-contract.md` before any operation intended to undo, discard, restore or force state. Shared rollback and local recovery are different contracts. A clean-looking worktree is never worth destroying unknown work.

## Stop states

Stop mutation and emit the applicable disposition when:

- required authority or tool permission is missing → `BLOCKED` or `HUMAN_REQUIRED`;
- target/source/work-package identity is ambiguous → `BLOCKED`;
- target/source/policy/test identity moved after evidence → `STALE_EVIDENCE`;
- preservation or restoration requires destructive scope not explicitly authorized → `RECOVERY_REQUIRED`;
- protected-history rewrite or repository-policy bypass would be required → `HUMAN_REQUIRED` or `BLOCKED`;
- evidence contradicts the intended merge/release claim → `BLOCKED`;
- an external mutation times out or its result is unknown → observe remote state before retrying.

## References

- `references/git-cycle.md` — outer Git delivery cycle and checkpoints.
- `references/git-state-machine.md` — states, transitions, stale/hold semantics.
- `references/branch-pr-contract.md` — work-package branch, worktree and PR binding.
- `references/operation-authority-matrix.md` — Git-local risk classes mapped to canonical tool governance.
- `references/composition-and-staleness.md` — composed-result identity and invalidation.
- `references/recovery-contract.md` — safe recovery, revert/reflog/rerere boundaries.
- `references/release-versioning.md` — release/tag/version design contract.
- `references/evidence-contract.md` — Git evidence and provenance fields.
