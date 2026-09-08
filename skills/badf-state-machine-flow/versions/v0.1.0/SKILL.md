---
name: badf-state-machine-flow
description: Evaluate, explain, audit, and safely route BADF Work Package state transitions using deterministic transition guards, authority checks, evidence binding, invariant failure routing, and resumable exception handling. Use when a BADF task asks what state a Work Package is in, whether it may advance, why it is blocked or waiting for authority, how to reach the next state, how to resume safely, or whether a recorded transition history is valid. Do not use this skill as a substitute for G00-G14 gate evaluation, repository-state inspection, or human approval.
---

# BADF State Machine Flow

## Scope

This skill governs the **Work Package execution-state machine**. It composes with, but does not replace, BADF lifecycle gates `G00`-`G14`.

Canonical forward states:

`DRAFT -> READY -> AUTHORIZED -> IN_PROGRESS -> VALIDATING -> ENGINEERING_READY -> ACCEPTED -> CLOSED`

Exceptional states:

- `BLOCKED` — a mandatory invariant, dependency, control, or evidence condition failed.
- `WAIT_FOR_AUTHORITY` — required authority is missing, ambiguous, stale, insufficient, or unverifiable.

Treat `CLOSED` as terminal. Do not invent additional states. If cancellation, abandonment, or supersession is requested and the canonical machine has no approved transition for it, report `GOVERNANCE_GAP` rather than fabricating a state.

## Required reading

1. Read repository `AGENTS.md`.
2. Read `docs/00-operating-model.md`, `docs/01-lifecycle-gates.md`, `docs/03-authority-and-agent-councils.md`, `docs/05-evidence-and-provenance.md`, `docs/06-sessions-handoffs-recovery.md`, and `docs/07-skills-governance.md` when present.
3. Read the active Work Package, its target gate, relevant authority record, current session, evidence index, and run ledger.
4. Read `references/state-model.md` and `references/transition-matrix.md` before evaluating a transition.
5. Read `references/gate-composition.md` when the request also concerns a G00-G14 gate.

## Core rules

1. **State is not gate.** A Work Package execution state and a BADF lifecycle gate are orthogonal controls. Never infer one from the other.
2. **No skipped forward transitions.** A request such as `READY -> IN_PROGRESS` is denied; authority must first be proven in `AUTHORIZED`.
3. **Guards are deterministic.** Evaluate only verified current facts. Do not fetch, mutate, approve, or create side effects inside a guard decision.
4. **Fail closed.** Missing or stale evidence does not count as `false-but-acceptable`; it prevents advancement.
5. **Authority is bound.** Authorization must match the Work Package identity, contract revision/digest, scope, and requested action.
6. **Evidence is bound.** Validation and acceptance must bind to the exact candidate revision/digest being advanced.
7. **No self-approval.** Independent validation or acceptance cannot be supplied by the author when separation is required.
8. **Exceptions preserve resume context.** `BLOCKED` and `WAIT_FOR_AUTHORITY` records must retain the prior normal state and reason so recovery cannot jump arbitrarily.
9. **Material contract change invalidates stale authorization.** Route the Work Package to `DRAFT` and require the normal progression again.
10. **Acceptance is human-controlled unless ratified policy explicitly says otherwise.** `ENGINEERING_READY` is not equivalent to `ACCEPTED`.
11. **Closure preserves history.** Do not overwrite prior transitions. Record an append-only transition event and retain acceptance/evidence references.

## Operating modes

### `inspect`
Determine the current state from authoritative records without changing it. Report conflicting records explicitly.

### `evaluate`
Evaluate a requested `from_state -> to_state` transition. Run deterministic guards and return one of:

- `ALLOW`
- `DENY`
- `BLOCKED`
- `HUMAN_REQUIRED`
- `GOVERNANCE_GAP`

`ALLOW` means the state-transition contract is satisfied. It does **not** mean the BADF lifecycle gate is approved.

### `explain`
Explain why the current state exists, what proof is present, what is missing, and the exact evidence/authority needed for the next legal transition.

### `audit`
Replay transition history, detect skipped states, stale approvals, evidence/candidate mismatches, invalid recovery, self-approval, terminal-state revival, and hand-maintained derived state.

### `recover`
Resolve `BLOCKED` or `WAIT_FOR_AUTHORITY` only after the blocking fact or authority deficiency is independently resolved. Resume the recorded prior state if the contract is unchanged; otherwise route to `DRAFT`.

## Evaluation procedure

1. Resolve `work_package_id`, current lifecycle gate, Work Package contract revision/digest, current state, requested target state, actor, and candidate revision when applicable.
2. Verify the current state from the authoritative Work Package/state record and reconcile it with session/run-ledger evidence. Do not silently choose between conflicts.
3. Verify referenced evidence with existing BADF schemas/scripts. A path or claim is not proof merely because it exists in text.
4. Normalize verified facts into the contract accepted by `scripts/evaluate_transition.py`.
5. Run:

```bash
python3 skills/badf-state-machine-flow/scripts/evaluate_transition.py <transition-request.json>
```

6. If the evaluator returns `BLOCKED`, route to `BLOCKED` and record failed invariant, evidence, remediation owner, and `resume_state`.
7. If it returns `HUMAN_REQUIRED`, route to `WAIT_FOR_AUTHORITY` and record required role/action, missing authority proof, and `resume_state`.
8. If it returns `DENY`, leave state unchanged and report the illegal transition or missing non-authority guard.
9. If it returns `ALLOW`, record the transition as an append-only, hash-linked event using the repository's run-ledger/evidence model. Mutation still requires the Work Package's normal authority and tool permissions.
10. Report state transition separately from gate disposition.

## Transition events

Use these event names when recording state changes:

- `CONTRACT_COMPLETED` — `DRAFT -> READY`
- `AUTHORITY_GRANTED` — `READY -> AUTHORIZED`
- `EXECUTION_STARTED` — `AUTHORIZED -> IN_PROGRESS`
- `VALIDATION_STARTED` — `IN_PROGRESS -> VALIDATING`
- `VALIDATION_COMPLETED` — `VALIDATING -> ENGINEERING_READY`
- `HUMAN_ACCEPTED` — `ENGINEERING_READY -> ACCEPTED`
- `KNOWLEDGE_RETAINED` — `ACCEPTED -> CLOSED`
- `REWORK_REQUIRED` — `VALIDATING -> IN_PROGRESS`
- `CHANGES_REQUESTED` — `ENGINEERING_READY -> IN_PROGRESS`
- `CONTRACT_MATERIALLY_CHANGED` — governed return to `DRAFT`
- `INVARIANT_FAILED` — route to `BLOCKED`
- `AUTHORITY_UNRESOLVED` — route to `WAIT_FOR_AUTHORITY`
- `EXCEPTION_RESOLVED` — resume from an exceptional state under the recovery rules

## Compatibility with current BADF schemas

Do not assume the repository already stores all canonical states. Existing BADF versions may expose legacy Work Package statuses such as `APPROVED` or `SUPERSEDED`, or project/session states with different enums. Never map legacy values to `AUTHORIZED`, `ENGINEERING_READY`, or `ACCEPTED` by inference.

Until a schema migration is ratified, this skill may operate in **assessment/shadow mode** using an explicit transition request and existing evidence. See `references/legacy-compatibility.md`.

## Outputs

Every evaluation must report:

```text
work_package_id
lifecycle_gate
from_state
requested_to_state
event
verdict
recommended_state
guards_passed
guards_failed
missing_or_stale_evidence
authority_required
candidate_or_contract_digest
residual_risk
next_safe_action
```

When state changes are authorized and persisted, also report the transition-event/evidence identifier and resulting digest.

## Stop conditions

Stop mutation and report the appropriate disposition when:

- Work Package or current state cannot be resolved;
- state records conflict;
- a forward state is skipped;
- authority cannot be proven;
- authority does not bind to the current contract/scope;
- evidence binds to a different candidate revision;
- an invariant fails;
- a material contract change makes prior authority stale;
- validator/acceptor independence is not satisfied;
- a request attempts to revive `CLOSED`;
- a requested lifecycle outcome has no canonical state/transition.

## Verification

For changes to this skill, run its unit tests and the repository's required BADF validation commands. This skill cannot approve itself, its own registry promotion, or the Work Package it evaluates.
