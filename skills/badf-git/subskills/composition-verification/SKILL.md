---
name: composition-verification
description: Bind and verify what protected integration is expected to produce -- write the git-composition record with `badf_compose.py --record`, commit it inside the pull request under work/<WP>/evidence/G07/composition-record.json, and let compose recompute and compare it on the tree that would land, refusing a stale base or a changed content tree. Use at badf-git's COMPOSE stage and again after any rebase or content change. Do not use to merge, to bypass the composed-tree gate, or as a source of authority.
---

# composition-verification

A subskill of `badf-git` (`../../SKILL.md`) for the COMPOSE stage (`../../references/git-cycle.md`)
and the composition contract (`../../references/composition-and-staleness.md`). Its admission
status is recorded in `badf/skill-registry.json`; this file defines behaviour and hardcodes no
lifecycle status.

**The invariant: `SOURCE_HEAD_GREEN != INTEGRATION_SAFE`.** A green source branch proves nothing
about the tree the squash will produce onto *today's* target. BADF's canonical composition
mechanism, `scripts/badf_compose.py`, has always computed that tree; before this subskill it
recorded none of it, and three rebases in one program silently invalidated composition.

## The claim and its binding

`badf_compose.py --record <path>` writes a **git-composition record**: `repository`,
`work_package_id`, `target_ref`, `target_base_sha`, `source_ref`, `merge_base_sha`,
`merge_method: squash`, `expected_result_tree`, **`expected_content_tree`**, `policy_epoch`,
`test_set_epoch` (null -- BADF defines none; declared as non-coverage), `suite_pattern`.

The binding is **`expected_content_tree`**: the composed tree with `work/<WP>/` and
`badf/lockfile.json` removed, computed on a temporary index. That is what lets the record --
and the self-dossier and lockfile that follow it -- live *inside* the pull request they verify
without moving the identity they bind. `source_head_sha` and `expected_result_tree` are
informational: committing the record moves both.

## The author's order of operations

```text
1. commit the content                         (the deliverables, outside work/<WP>/)
2. python3 scripts/badf_compose.py --record work/<WP>/evidence/G07/composition-record.json --message-file <pr-body>
3. python3 scripts/badf_gate.py self-dossier <WP>        (indexes the record as `composition` evidence)
4. commit the record, the dossier and the re-signed lockfile
5. push; CI's compose finds the record on the composed tree and verifies it
```

A rebase, a moved target, or any content change **recomputes the record (step 2 again) --
never edits it**. `git-staleness` (the `commit-integrity` subskill) tells you *that* the
target or source moved; this record binds *what* the composition was expected to produce.

## What compose verifies on the tree that would land

| Finding | Result |
| --- | --- |
| recorded `target_base_sha` == the base composed onto, recomputed content tree == `expected_content_tree`, `merge_method` squash, `target_ref` the default branch | `composition: CURRENT` |
| recorded base differs | **FAIL** -- "composition record is stale … recompute with `--record`" |
| content tree differs | **FAIL** -- "composition record does not match the composed content" |
| non-squash method, foreign target, wrong work package, malformed record | **FAIL** naming the defect |
| no record | `composition: no record` -- backward compatible; requiring one is a later policy decision |

## Boundaries

- Read-only for the source repository; the record file is the only write, and only where asked.
- Reviewer-approval staleness and the expected-head merge guard are GIT-F; comparing the *landed*
  tree with the expected one after merge is GIT-F/G; ordered multi-change prefixes are declared,
  not implemented.
