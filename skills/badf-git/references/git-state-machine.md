# BADF Git State Machine

This state machine describes Git/GitHub delivery state. It does not replace BADF G00-G14 and none of its states grant lifecycle, merge, release or production authority.

## Progression states

```text
GIT_AUTHORITY_BOUND
  → GIT_BASELINED
  → GIT_ISOLATED
  → GIT_CHANGE_ACTIVE
  → GIT_SOURCE_VERIFIED
  → GIT_PUBLISHED
  → GIT_PR_BOUND
  → GIT_COMPOSED
  → GIT_VERIFIED
  → GIT_MERGE_AUTHORIZED
  → GIT_MERGED
  → GIT_RECONCILED
  → GIT_RELEASED
  → GIT_CLEANED
  → GIT_LEARNED
```

## Hold states

```text
STALE_EVIDENCE
BLOCKED
HUMAN_REQUIRED
OUTCOME_UNKNOWN
RECOVERY_REQUIRED
```

## State meanings and minimum evidence

| State | Meaning | Minimum evidence |
| --- | --- | --- |
| `GIT_AUTHORITY_BOUND` | GitHub operation is bound to an active WP and permitted scope | WP/demand, repository, operation class, target |
| `GIT_BASELINED` | authoritative remote state was observed before mutation | target ref/SHA/tree, source ref/head/tree if present, ruleset/policy observation, timestamp |
| `GIT_ISOLATED` | dedicated GitHub source ref represents the WP workspace | source ref created/adopted from exact authorized base; source head/tree |
| `GIT_CHANGE_ACTIVE` | one or more authorized candidate mutations exist on the source ref | commit/tree identities, changed paths, prior head |
| `GIT_SOURCE_VERIFIED` | exact source revision passed required source checks | source SHA/tree + remote run/check IDs/results |
| `GIT_PUBLISHED` | current candidate exists in the shared GitHub repository | source ref/head observed remotely |
| `GIT_PR_BOUND` | PR binds WP/demand, target and exact source identity | PR number/body, target/source refs and SHAs |
| `GIT_COMPOSED` | expected protected result is computed | target base, source head, merge base/method, expected result tree |
| `GIT_VERIFIED` | required composed checks/challenge are current | composed tree + checks + independent review evidence |
| `GIT_MERGE_AUTHORIZED` | separate authority permits protected integration | authority receipt/decision bound to current inputs |
| `GIT_MERGED` | GitHub reports protected integration completed | PR/merge response, observed protected commit |
| `GIT_RECONCILED` | landed commit/tree and WP/Issue/PR are reconciled | observed landed identity, expected-vs-actual disposition |
| `GIT_RELEASED` | separately authorized release identity exists | version/tag/release + source/artifact provenance |
| `GIT_CLEANED` | remote topic ref is safely retired where allowed | reconciliation complete + cleanup record |
| `GIT_LEARNED` | validated lesson disposition recorded | learning/evidence reference |

## Transition guards

### AUTHORITY_BOUND → BASELINED

Pass only when the target repository/ref is unambiguous and GitHub state can be observed. Missing/ambiguous repository identity or unavailable authoritative state returns `BLOCKED`.

### BASELINED → ISOLATED

Pass only when:

- source ref belongs to the active WP;
- a new source ref starts at the exact recorded base SHA, or an existing source ref is explicitly adopted after re-observation;
- no concurrent actor has moved the ref between observation and creation/adoption.

No local worktree path is evaluated.

### ISOLATED → CHANGE_ACTIVE

Every remote change must be within WP scope. A new commit must name the observed source head as its parent/pre-state. Ref advancement is non-force by default.

### CHANGE_ACTIVE → SOURCE_VERIFIED

Checks bind the exact remote source SHA/tree. A later source movement sends the state to `STALE_EVIDENCE`.

### SOURCE_VERIFIED → PR_BOUND

The PR must point to the exact current source ref/head and authorized target. PR body traceability is mandatory where repository policy requires it.

### PR_BOUND → COMPOSED

Composition binds current source head + current target base + merge semantics. Any movement invalidates the result.

### COMPOSED → VERIFIED

Required composed checks and independent challenge must pass on the current identity and declare relevant non-coverage.

### VERIFIED → MERGE_AUTHORIZED

Authorization is separate from verification. `GIT_VERIFIED` alone cannot transition itself.

### MERGE_AUTHORIZED → MERGED

Immediately before mutation, re-observe the PR head and relevant target/ruleset state. A moved head or stale authorization fails closed. Use expected-head protection where supported.

### MERGED → RECONCILED

Read the actual protected commit/tree from GitHub and compare it with the authorized expected result. Unknown/mismatched result enters `OUTCOME_UNKNOWN` or `RECOVERY_REQUIRED`.

### RECONCILED → RELEASED

Optional and separately authorized. Non-release work may bypass this state and proceed to cleanup according to the governing delivery lifecycle.

### RECONCILED/RELEASED → CLEANED

Only retire the remote source ref after all unique work/evidence is preserved and no open recovery depends on it.

## Stale-evidence transitions

These events send affected integration claims to `STALE_EVIDENCE`:

- source head/tree changes;
- target base changes;
- merge method changes;
- material PR message changes where it affects the squash/ledger;
- relevant policy/ruleset changes;
- material test/toolchain epoch changes.

Recovery is re-observation + recomputation + re-verification, not relabeling stale evidence as current.

## Concurrency rule

A GitHub source ref is an optimistic-concurrency boundary. If the ref moved after it was observed, BADF does not overwrite the newer state. It stops and reconciles. This is the remote equivalent of an expected-value lease.
