# Git/GitHub Operation Authority Matrix

This matrix classifies operations for the GitHub-native BADF Git model. Classification does not itself grant permission; the active Work Package, authority matrix, repository ruleset and tool registry remain controlling.

## Operation classes

| Class | Name | Typical operations | Default posture |
| --- | --- | --- | --- |
| `GIT-O0` | Remote Observe | repository metadata, refs, commits, trees/blobs, compare, PRs, reviews, checks, rulesets | read-only; autonomous within data scope |
| `GIT-O1` | Remote Workspace Mutation | create WP source branch/ref, create/update scoped files, create blobs/trees/commits, non-force advance WP ref | Work-Package authority required |
| `GIT-O2` | Remote Topic Rewrite | exceptional rewrite/reconstruction of an already-published WP ref | explicit scope + expected prior SHA; evidence invalidation |
| `GIT-O3` | Collaboration Mutation | create/update PR, request review, comment/label as authorized | Work-Package/collaboration authority |
| `GIT-O4` | Protected Integration | merge PR to protected branch, create governed release tag/release | separate integration/release authority |
| `GIT-O5` | Destructive/Admin | force-update/delete protected ref, move/delete release tag, weaken ruleset, bypass checks | deny by default / higher authority |

## GitHub Remote Workspace operations

### GIT-O0 — Observe

Examples:

- read repository/default branch and permissions;
- read target/source refs and commits;
- read tree/blob/file content by exact ref/SHA;
- compare base/head;
- read PR metadata, changed files, reviews/threads and checks;
- read active branch rulesets/protection.

Evidence: operation, repository, ref/SHA/PR queried, timestamp, returned stable identifiers and outcome.

### GIT-O1 — Workspace mutation

Examples:

- create `wp/<WP>-<slug>` from an exact observed base SHA;
- create a blob/tree/commit within WP scope;
- create/update a scoped repository file on the WP branch;
- advance the WP ref non-force to a commit whose parent is the observed prior head.

Guard:

```text
observed_source_head == expected_pre_state
new_commit.parent == observed_source_head
ref_update.force == false
```

If the ref moved, stop and re-observe. Do not convert the failure into a force update.

### GIT-O2 — Topic rewrite

BADF remote-first flow prefers additive source-branch commits. Rewriting a published topic ref changes identity and invalidates affected checks/reviews/composition. If separately authorized, bind the exact expected prior remote SHA and preserve old/new identities. The safety intent corresponds to `--force-with-lease`; bare force is not normal operation.

### GIT-O3 — Collaboration

A PR/comment/review request may communicate and bind evidence but cannot create merge authority. Mutations must target the correct repository and PR after re-observation.

### GIT-O4 — Protected integration/release

Protected merge must satisfy current rulesets, required checks, current composed evidence, review/challenge requirements and separate authority. Where supported, pass the exact expected PR head SHA. Release/tag operations are a separate authority boundary.

### GIT-O5 — Destructive/admin

Examples:

- force update `main`;
- delete/reset protected `main`;
- move/delete published release tag;
- lower/disable required checks or rulesets;
- use bypass/admin privileges to evade BADF controls.

These are never implied by normal Work-Package write authority.

## Tool mapping

A future implementation may map registered GitHub connector/API operations to these classes, for example:

| GitHub capability | Class |
| --- | --- |
| fetch/read repository/ref/commit/tree/file/PR/check/ruleset | `GIT-O0` |
| create branch; create file/blob/tree/commit; non-force source-ref advance | `GIT-O1` |
| force source-ref rewrite | `GIT-O2` |
| create/update PR; request reviewer; scoped PR metadata/comment | `GIT-O3` |
| merge PR; governed release/tag creation | `GIT-O4` |
| protected-ref force/delete; tag move/delete; ruleset weakening | `GIT-O5` |

The `badf-git` root skill remains declarative and tool-empty while `DESIGNED`; registering a concrete GitHub mutation tool/subskill is a separate governed implementation step.

## Explicit exclusions

The BADF Git execution substrate does not classify `git worktree add`, `git worktree remove`, local worktree-path management, local index/stash inspection or local reflog recovery as required workflow operations. Native local Git commands may exist outside BADF, but they do not define GitHub Remote Workspace state.
