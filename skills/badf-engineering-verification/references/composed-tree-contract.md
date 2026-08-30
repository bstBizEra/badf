# Composed-tree contract — SOURCE_HEAD_GREEN ≠ COMPOSED_VERIFIED (VER-I15)

A source branch can be correct on its own and fail once composed onto today's target. G08 therefore
reasons against the result that would land:

```text
BASE (target_base_sha)
+ candidate (source_revision)
+ ordered upstream work packages (declared, when a prefix exists)
= COMPOSED RESULT (expected_content_tree)
```

and the final G08 state binds that exact composed identity. `PR head passed → integration safe` is the
inference this contract forbids.

## The mechanism is `badf-git`'s — routed, never duplicated

BADF's canonical composition mechanism is `scripts/badf_compose.py`: it composes base + candidate exactly
as the squash will, points the ledger at the result, and runs `badf_gate.py repo` and the suite **there**.
The `composition-verification` subskill records what the composition is expected to produce
(`badf_compose.py --record` → `expected_content_tree`) and compose recomputes and compares it on the tree
that would land, refusing a stale base or a changed content tree.

The composed run **is the fresh run** (BLD-I09): `badf-build` names it as the authoritative unit-test
execution, and G08 binds it as the `composed-tree-test` observation. This skill adds no second composition
mechanism and no second runner.

## The binding

```yaml
evidence_type: composed-tree-test
work_package_id: WP-2026-NNNN
composition:
  target_ref: main
  target_base_sha: <sha>
  source_revision: <candidate sha>
  merge_method: squash
  recorded_expected_content_tree: <from composition-record.json>
  recomputed_content_tree: <computed in the composed checkout>
  equal: true
execution: {runtime: badf_compose.py | CI composed-tree step, suite_pattern: …, exit_code: 0, output_digest: …, started_at: …, finished_at: …}
staleness: CURRENT
outcome: PASS
non_coverage:
  - surface: test_set_epoch
    reason: BADF defines no test-set/toolchain epoch (badf-git git-cycle section 2)
```

`equal: false` is `outcome: FAIL` with the composition-verification refusal quoted; a missing record is
`outcome: NOT_RUN` and the dossier holds — a composition nobody recorded is not one that was verified.

## Ordered prefixes

Where the target already carries upstream work packages that the candidate depends on, the prefix is
**declared** on the composition (`badf-git`: ordered multi-change prefixes are declared, not implemented).
G08 binds the declaration; it does not compute an order the composition mechanism did not.
