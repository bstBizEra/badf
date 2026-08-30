# Target binding — the exact candidate and the exact composed result (VER-I01, VER-I15)

No "review this branch". A G08 object binds the identity BADF already records, and nothing floating.

## The fields, and where each one comes from

```yaml
review_target:
  repository: bstBizEra/<project>
  work_package_id: WP-2026-NNNN
  source_revision: <candidate SHA>                 # the evidence core's own field
  target_base_sha: <the base the candidate composes onto>
  expected_content_tree: <from work/<WP>/evidence/G07/composition-record.json>
  diff_digest: <sha256 of the source-change diff bound by G07>
  staleness: CURRENT                               # badf_gate.py git-staleness verdict
```

- `source_revision` and `target` are the evidence core (`schemas/evidence.schema.json`); they are not
  re-invented here.
- `target_base_sha` and `expected_content_tree` come from the committed **git-composition record**
  written by `badf_compose.py --record` under `badf-git`'s `composition-verification` subskill. The
  content tree — the composed tree with `work/<WP>/` and `badf/lockfile.json` removed — is the identity
  that survives the record, the dossier and the lockfile being committed *inside* the pull request they
  verify. **This skill mints no new composed-identity field**: the record's `expected_content_tree` is the
  composed identity; a `composed-tree-test` binds the recorded value and the recomputed value and requires
  them equal.
- `diff_digest` is the G07 `source-change` binding's change digest, carried forward so review findings
  can name the diff they inspected.

## Freshness is a verdict, not a feeling

`badf_gate.py git-staleness` renders the candidate against a stored baseline:

| Verdict | Meaning for G08 |
| :--- | :--- |
| `CURRENT` | evidence may be produced and remains bound |
| `SOURCE_ADVANCED` | the candidate moved: every review and observation bound to the old `source_revision` is stale — recompute, never relabel |
| `STALE_EVIDENCE` | evidence exists for a revision that is no longer the candidate |
| `TARGET_MOVED` | the base moved: the composition record and every Verifier-plane observation are stale until `badf_compose.py --record` is re-run on the new base |

Target movement, source movement, history rewrite, merge-method change, policy/test epoch change or a
different conflict resolution invalidates affected G08 evidence (the `badf-git` composition-and-staleness
contract). A dossier that carries evidence for a tree other than the one that would land is refused, not
argued with.

## What binding forbids

- reviewing a branch tip when the merge base is elsewhere (Codex's merge-base principle, made a binding);
- reusing a review of an earlier candidate because "only tests changed";
- serializing `composed_tree` as a free-text note rather than the recorded content tree.
