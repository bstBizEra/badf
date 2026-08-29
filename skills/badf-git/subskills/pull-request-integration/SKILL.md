---
name: pull-request-integration
description: Integrate a BADF work package through its pull request the way the contract requires -- re-check the current target, the exact reviewed head, the merge method, the required checks on that head and the composition claim immediately before merging; merge only through the protected squash bound to the reviewed head SHA; and treat MERGED as unverified until the next branch's `badf_gate.py reconcile` compares what landed with what was verified. Use at badf-git's AUTHORIZE, SQUASH and RECONCILE stages. Do not use to grant merge authority, to bypass a refused reconcile, or to rewrite the protected branch.
---

# pull-request-integration

A subskill of `badf-git` (`../../SKILL.md`) for stages 9–11 of the cycle (`../../references/git-cycle.md`:
AUTHORIZE, SQUASH, RECONCILE) and the integration guard of the composition contract
(`../../references/composition-and-staleness.md`). Its admission status is recorded in
`badf/skill-registry.json`; this file defines behaviour and hardcodes no lifecycle status.

**The invariant: `MERGED != VERIFIED`.** The expected-head guard protects the *source* identity.
It cannot close the window in which the target moves between the last CI run and the merge — in
that window GitHub squashes onto a newer base and the landed tree is not the tree that was
verified. The landing is verified afterwards, from the object store, against the composition
claim GIT-E committed; a mismatch is a refusal that opens recovery, never a note.

## AUTHORIZE — observe, then decide (platform observations, made with `gh`; nothing here is gate code)

| Check | How | Refuse when |
| --- | --- | --- |
| target current | `gh api repos/<o>/<r>/pulls/N --jq .base.sha` vs `git rev-parse origin/<default>` | the base moved since the CI run — re-record (`badf_compose.py --record`), re-dossier, re-push |
| exact reviewed head | `.head.sha` equals the SHA the evidence was measured on | the head moved — the evidence is stale (GIT-I05) |
| merge method | repository policy: squash | anything else |
| required checks on **this** head | `gh api repos/<o>/<r>/commits/<head>/check-runs` all `completed/success` | pending or red |
| composition claim verified on the runner | the compose step printed `composition: CURRENT` | `no record` on a WP that should carry one, or any refusal |
| platform mergeability | `.mergeable_state == "clean"` | `dirty`, `blocked`, `unknown` — re-observe, never force |
| integration actor | a human, or an agent under an explicit human instruction for this merge | tool capability is not authorization (GIT-I01) |

## SQUASH — merge the exact reviewed head, bound

```text
gh api -X PUT repos/<o>/<r>/pulls/N/merge --input - <<< '{"merge_method": "squash", "sha": "<reviewed head sha>",
  "commit_title": "<PR title> (#N)", "commit_message": "<PR body>"}'
```

The `"sha"` binds the reviewed head: if the head moved, the platform refuses and the work returns to
composition/review. The PR body becomes the squash message — the `Work-Package:` trailer the ledger
reads. Never `--force`, never a rewrite of the protected branch to repair a failed claim.

## RECONCILE — the next branch proves the landing

```text
python3 scripts/badf_gate.py reconcile <WP>
```

reads the composition record from the **landed commit's tree**, computes the landed content tree from
the object store alone (`work/<WP>/` and the lockfile excluded), and:

- match → `CLOSED`, `landed_as`, **`landed_content_tree`**, **`composition_verified: true`**;
- mismatch → `BLOCKED: … main moved between verification and merge; open recovery as a forward change` —
  the record stays `IN_PROGRESS`; recovery is a new work package (GIT-G), never a rewrite of `main`;
- no record → `CLOSED`, `landed_as`, `composition_verified: false` — honest and visible, not silent;
- a malformed record → refused, never downgraded to "no record".

Deterministic, network-free, reads only.

## Boundaries

- Approval-freshness *enforcement* and merge queues are outside this subskill (a single collaborator
  runs this repository; condition C-1 stays open and recorded). Release tags are GIT-H; recovery
  automation is GIT-G.
