# Governed Git Cycle

This reference freezes the **BADF Governed Trunk Git Model (GTGM)**. It describes the Git delivery cycle inside BADF's broader engineering loop; it does not create new repository authority.

## Model

BADF uses one permanent integration branch (`main`) and short-lived, work-package-bound change branches. Lifecycle state lives in BADF records and evidence, **not** in permanent Git branches such as `develop`, `integration`, `staging`, `alpha`, or `beta`.

The governed outer cycle is:

```text
AUTHORITY
  ↓
BASELINE
  ↓
ISOLATE
  ↓
BUILD
  ↓
VERIFY
  ↓
PR
  ↓
COMPOSE
  ↓
CHALLENGE
  ↓
AUTHORIZE
  ↓
SQUASH
  ↓
RECONCILE
  ↓
RELEASE? ── optional
  ↓
CLEAN
  ↓
LEARN
```

The cycle is not a promise that every stage may mutate. Each stage is still constrained by the work package, tool registration, authority matrix, repository rules and platform controls.

## Stage contracts

### 1. AUTHORITY

Resolve before mutation:

- canonical work-package ID and accountable owner;
- issue/demand and target BADF gate;
- repository identity and target ref;
- change class and data classification;
- permitted tools, environments and mutations;
- acceptance criteria and NFRs;
- required tests, evidence and reviewers;
- rollback owner/procedure and escalation conditions.

**Exit condition:** the planned next operation is authorized and target identity is unambiguous.

**Hold:** `BLOCKED` or `HUMAN_REQUIRED` when authority is absent, stale, contradictory, or reserved.

### 2. BASELINE

Observe before editing. Capture at minimum:

- repository full identity;
- current worktree/branch/index status;
- target ref and current target SHA;
- source ref and source SHA when already created;
- merge base when source exists;
- remote freshness/fetch observation;
- applicable rules/policy epoch;
- test-set/toolchain epoch when evidence will depend on it;
- existing unrelated or unknown local state.

Do not make the checkout clean by deleting, resetting, stashing-away-and-forgetting, or overwriting unknown work.

**Exit condition:** a reproducible baseline exists.

### 3. ISOLATE

Create or select one short-lived branch for the work package. For parallel agents/work packages, prefer a dedicated `git worktree` per independent change.

Isolation rules:

- one worktree cannot silently become shared scratch space for multiple agents;
- parallel branches must not edit overlapping files unless an integrator has an explicit composition plan;
- branch names are labels; the canonical work-package record remains the authority source;
- branch creation does not authorize push, merge or release.

**Exit condition:** work has an isolated source ref/worktree and unrelated state is preserved.

### 4. BUILD

Use the nested Git loop:

```text
SYNC → INSPECT → EDIT → STAGE → DIFF → COMMIT → VERIFY → RECONCILE → ↺
```

Commit discipline:

- stage intentionally; `git add -p` or equivalent review is preferred for mixed changes;
- inspect the staged diff before commit;
- commits should be coherent enough to review, bisect locally and recover;
- temporary branch history may be cleaned within the private-history rules, but any rewrite invalidates source-bound evidence;
- do not use commit-message style as a substitute for work-package identity or authority.

**Exit condition:** a coherent source revision exists for verification.

### 5. VERIFY

Run targeted checks and the repository-required verification. Evidence binds to the source revision that was actually tested.

A source branch can be locally correct and still be unsafe to integrate. Therefore:

```text
SOURCE_HEAD_GREEN != INTEGRATION_SAFE
```

**Exit condition:** required source-level checks have explicit outcomes and evidence.

### 6. PR

Publish/bind the proposed change through a pull request when remote review is required. The PR must identify:

- canonical work package;
- demand/issue;
- target and source refs;
- exact source head;
- scope/non-goals;
- acceptance criteria;
- verification evidence;
- composition status;
- independent-review requirements;
- residual risks and explicit holds.

A PR is a review/integration vehicle, not authority by itself.

**Exit condition:** the current proposed source is reviewable and traceable.

### 7. COMPOSE

Compute the exact expected protected integration result using BADF's canonical composition mechanism. Under the current repository contract the protected merge method is squash.

Bind:

- target base SHA;
- source head SHA;
- merge base SHA;
- merge method;
- expected result tree;
- ordered-prefix position when multiple changes compose;
- policy/test epochs.

Run required tests against the composed result, not just the branch head.

**Exit condition:** current composition evidence supports the intended target and exact source.

### 8. CHALLENGE

Obtain required independent review. Review scope should cover the affected risk lenses and explicitly state non-coverage.

Rules:

- author evidence is not independent approval;
- council output is advisory unless policy makes it a gate;
- findings bind to the reviewed revision/composed result;
- source movement after review can make findings/approval stale.

**Exit condition:** required review exists for the current evidence identity, or the work is held.

### 9. AUTHORIZE

Immediately before protected integration, re-check:

- current target SHA;
- exact source head;
- merge method;
- required checks;
- review/approval freshness;
- expected result tree;
- policy/ruleset state;
- unresolved conditions/exceptions.

A previous authorization does not survive material identity drift without explicit recomputation/review.

**Exit condition:** an authorized actor may integrate the exact reviewed/composed change.

### 10. SQUASH

Use only the repository-approved protected integration method. In the current BADF repository that method is squash.

Requirements:

- merge the exact reviewed head;
- do not bypass required checks or rules;
- do not treat tool capability as authorization;
- do not rewrite `main` to repair a failed integration claim.

The protected integration result becomes part of BADF's authoritative Git ledger.

**Exit condition:** the platform reports the landed protected revision or a controlled failure/unknown outcome.

### 11. RECONCILE

After integration, verify the actual landed revision/result against the expected composition and work-package claim.

Reconcile:

- actual protected revision;
- actual result tree;
- issue/PR closure state;
- checks attached to the landed commit as applicable;
- acceptance criteria;
- evidence/dossier references;
- any post-merge drift or unexpected platform behavior.

`MERGED` is not synonymous with `VERIFIED` or `RELEASED`.

**Exit condition:** integration outcome is known and consistent, or a recovery/incident path is opened.

### 12. RELEASE (optional)

When the work package includes a BADF release, bind the release to a verified `main` revision and release packet. See `release-versioning.md`.

Do not rebuild a different artifact and call it the same release. Do not infer release authority from merge authority.

**Exit condition:** immutable release identity/evidence exists, or release remains out of scope.

### 13. CLEAN

Delete only known disposable local/topic state after its retention and recovery requirements are satisfied.

Safe cleanup requires proof that the state is:

- already landed or intentionally abandoned under authority;
- not the only copy of evidence or recovery data;
- not holding unknown/uncommitted user work;
- not needed for an open review, incident or audit.

**Exit condition:** local/topic state is intentionally reconciled without evidence loss.

### 14. LEARN

Record repeated Git failure modes, conflict patterns, composition defects and recovery lessons only after evidence supports a reusable conclusion.

Learning can propose a new test, skill revision, policy change or automation, but each is a separate governed change. A single successful workaround does not automatically become policy.

## Relationship to the BADF engineering loop

GTGM nests inside:

`FRAME → DISCOVER → PLAN → AUTHORIZE → BUILD → VERIFY → CHALLENGE → RECONCILE → DELIVER → OBSERVE → LEARN`

Typical mapping:

| BADF loop | Git cycle contribution |
| --- | --- |
| FRAME / DISCOVER | AUTHORITY, BASELINE |
| PLAN / AUTHORIZE | ISOLATE and permitted operation plan |
| BUILD | BUILD nested Git loop |
| VERIFY | VERIFY + COMPOSE |
| CHALLENGE | CHALLENGE |
| RECONCILE | AUTHORIZE + pre-merge reconciliation |
| DELIVER | SQUASH + post-merge RECONCILE + optional RELEASE |
| OBSERVE | CI/release/runtime observations as applicable |
| LEARN | CLEAN + LEARN |

The mapping is descriptive. It does not alter lifecycle gate authority.
