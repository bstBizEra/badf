# Sessions, Handoffs, and Recovery

Status: **NORMATIVE**

## Session identity

Create a stable session ID and bind it to actor, work package, repository, base revision, branch, lifecycle stage, start time, authority receipt, and scope. Session transcripts are not automatically durable project memory.

## Checkpoints

Checkpoint before delegation, context compaction, risky mutation, external write, deployment, handoff, or pause. Each checkpoint records completed actions, changed files, current digests, checks and outcomes, decisions, assumptions, blockers, remaining plan, and next safe action.

## Handoff contract

A receiver must be able to continue without guessing. Include:

- objective, acceptance, scope/non-goals, and authority;
- base/head/result-tree identities and working-tree state;
- completed work with evidence references;
- pending steps, dependencies, risks, and rollback state;
- commands to reproduce and validate;
- explicit statement of secrets/data not transferred.

The receiver verifies source state and acknowledges or rejects the handoff. A stale base, missing evidence, or changed scope requires reconciliation.

## Crash recovery

Recover from Git and sealed checkpoints, not conversational memory. Re-establish authority, inspect working state, verify last completed checkpoint, rerun affected checks, and create a recovery record. Never assume an interrupted external mutation failed or succeeded; query its authoritative system by idempotency key or returned identifier.

## Idempotency

External mutations must use stable idempotency keys where available. Record request intent before action and returned identity after action. Retry only after checking existing state.

