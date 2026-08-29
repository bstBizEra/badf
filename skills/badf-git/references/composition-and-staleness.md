# Composition and Staleness Contract

BADF treats integration as a property of the **expected composed result**, not the source branch in isolation.

## Core invariant

```text
SOURCE_HEAD_GREEN != INTEGRATION_SAFE
```

A source branch can pass every source-local check and still fail after integration because the target moved, dependency/order assumptions changed, conflict resolution changed semantics, or the protected merge method produces a different tree than the one tested.

## Canonical composition identity

For every integration claim, bind at minimum:

```yaml
git_composition:
  repository: bstBizEra/badf
  target_ref: refs/heads/main
  target_base_sha: "<sha>"
  source_ref: refs/heads/wp/...
  source_head_sha: "<sha>"
  merge_base_sha: "<sha>"
  merge_method: squash
  expected_result_tree: "<git-tree-sha>"
  ordered_prefix_position: 1
  test_set_epoch: "<epoch>"
  policy_epoch: "<epoch>"
```

When a single change has no ordered multi-change prefix, `ordered_prefix_position` may be omitted only where the governing evidence schema permits. BADF's general evidence doctrine still expects the position for composed multi-change work.

## Source, target and result are separate identities

- **Source head** identifies the candidate branch state.
- **Target base** identifies the exact protected branch state the candidate is composed onto.
- **Merge base** identifies the common ancestry used to reason about divergence.
- **Expected result tree** identifies the content BADF expects protected integration to produce.
- **Landed protected commit** identifies what GitHub actually recorded after integration.

Do not substitute one for another.

## Canonical composition mechanism

For BADF repository changes, use the repository's existing canonical composition mechanism rather than inventing a second validator. At the contract-freeze baseline, CI uses `scripts/badf_compose.py` to compose the exact squash result and verify that result before merge.

This skill describes when composition is required and what must be bound; it does not replace or fork the canonical composition implementation.

## Current protected merge method

The current BADF repository integration contract is squash-only. Therefore the normal composition evidence uses:

```text
merge_method = squash
```

If a future ratified repository policy changes the protected merge method, higher authority supersedes this assumption and all affected composition logic/evidence must be revalidated. A skill file cannot freeze a platform setting forever.

## Staleness model

Evidence is current only for the identities it actually tested/reviewed.

### Source movement

Any source-head change after evidence was produced makes affected evidence stale, including:

- new commit;
- amend;
- rebase;
- interactive rebase;
- cherry-pick that reconstructs the patch series;
- reset followed by recommit;
- conflict-resolution edit;
- generated-file change;
- force-with-lease update to a rewritten topic branch.

Required response:

1. capture new source head;
2. identify affected evidence/reviews;
3. recompute composition;
4. rerun required checks;
5. repeat review/authorization as required.

### Target movement

When `main` moves after composition:

- old target-base-bound evidence becomes stale for protected integration;
- recompute merge base and expected result tree;
- rerun required composed checks;
- re-evaluate conflict/order assumptions;
- do not claim the old result remains safe merely because the source did not change.

### Merge-method movement

Changing merge method changes integration semantics. Evidence for squash does not automatically prove merge-commit or rebase integration safety.

### Policy/rules movement

If required checks, authority rules, branch protection, rulesets or gate policy materially change after evidence, re-evaluate whether prior evidence/approval is still sufficient.

### Test/toolchain movement

When the governing test set/toolchain epoch changes materially, old evidence may remain historically true but may be insufficient for the current claim. Record the new epoch and rerun what policy requires.

### Ordered-prefix movement

For multiple dependent branches/change sets, a change can be safe at prefix position `N` and unsafe after earlier changes are added, removed, reordered or rewritten.

Recompute each affected expected result in order.

## Rebase semantics

A rebase is not merely cosmetic from an evidence perspective:

```text
old source SHA != new source SHA
```

Even if patch intent appears equivalent, the current evidence must bind the new source and current target. Use `git range-diff` as a human diagnostic to compare old/new patch series, not as the machine identity.

If the rebase changes conflict resolution, tests must treat that resolution as new code.

## Patch equivalence

Tools such as `git patch-id` can help investigate whether patch content is similar across rewritten commits, but patch equivalence is not sufficient to preserve BADF evidence identity because:

- context/target may differ;
- ordering may differ;
- merge-base may differ;
- composed result may differ;
- policy/test epochs may differ.

The authoritative binding remains the exact source/target/result identities.

## Conflict resolution

Conflict resolution is an implementation act.

Rules:

- identify which side/requirement each resolution satisfies;
- inspect the resolved diff;
- if `rerere` recalls a prior resolution, treat it as a candidate only;
- recompute the expected result tree after resolution;
- rerun checks affected by the conflict;
- preserve non-obvious conflict rationale in the PR/evidence when it affects review.

`NO CONFLICT` does not imply semantic compatibility, and `CONFLICT RESOLVED` does not imply correctness.

## Expected-head integration guard

Where the platform API supports an expected head SHA, protected merge should bind the exact reviewed head. If the PR head has moved, the merge must be rejected and the work returned to composition/review.

Expected-head checking protects source identity. It does not remove the need to verify current target/composition.

## Before-merge reconciliation checklist

Immediately before protected integration, observe and compare:

- PR source head == evidence source head;
- target base is current for the composition claim;
- merge base corresponds to current source/target;
- merge method matches policy;
- expected result tree is current;
- required status checks refer to the intended current change;
- review approvals are not stale;
- no required thread/condition remains unresolved;
- policy/test epochs are current;
- integration actor is separately authorized.

Any mismatch produces `STALE_EVIDENCE`, `BLOCKED` or `HUMAN_REQUIRED` rather than merge.

## Post-merge reconciliation

After GitHub reports a successful integration:

1. observe the protected commit SHA;
2. inspect/derive its result tree identity as applicable;
3. compare actual landed content to the expected result;
4. reconcile PR/issue/work-package state;
5. record checks attached to the landed commit where required;
6. open recovery if the result differs unexpectedly.

A successful API response is evidence of platform action, not proof that the integrated content satisfies the work package.

## Multiple-change composition

When multiple WPs must land in order:

```text
base₀
 + change₁ → result₁
 + change₂ → result₂
 + change₃ → result₃
```

Each change records its ordered-prefix position and composes against the result of the authorized preceding prefix, not an obsolete base.

After any upstream movement:

- invalidate downstream composed evidence;
- recompute from the changed prefix onward;
- rerun affected tests/reviews;
- do not preserve queue claims from a source-head-only pass.

## Stale evidence is retained, not erased

Stale evidence remains useful provenance. Mark/supersede it; do not delete or mutate it to look current.

A correct record can say:

```text
EVD-OLD: PASS on source A / target B — SUPERSEDED by target movement
EVD-NEW: PASS on source A / target C — current composition evidence
```

Historical truth and current sufficiency are different properties.
