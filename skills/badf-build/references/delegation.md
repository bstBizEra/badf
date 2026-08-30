# Delegation — subagents may execute; authority can only narrow

Fresh-context subagents reduce context contamination and are welcome. BADF adds a stronger rule:

```text
Parent WP authority
        ↓
delegated task contract
        ↓
STRICT SUBSET
```

```text
delegated_authority  ⊆  WP_authority  ⊆  repository_policy
```

No escalation through delegation (BLD-I10). A subagent may receive:

```yaml
task:
  wp: WP-2026-NNNN
  acceptance_refs:
    - AC-021
  allowed_paths:
    - src/payments/**
    - tests/payments/**
  allowed_tools:
    - filesystem
    - shell
  prohibited:
    - push
    - merge
    - release
    - credential-use
    - schema-outside-scope
  budget:
    attempts: 2
```

It may **never** receive more authority than the parent Work Package.

## The Work Package remains the governed unit

```text
Governed WP
   ├── execution slice A
   ├── execution slice B
   └── execution slice C
```

Slices may be dispatched to fresh agents, but all of them remain inside WP scope, WP authority, WP risk,
WP budget and the WP evidence contract. Therefore:

```text
subagent task  ≠  new Work Package
```

unless the work genuinely needs independent authority, lifecycle, rollback or landing — in which case
it returns to planning as a new Work Package, never as a task that quietly grew one.

A subagent's "ruling" on ambiguity is an engineering choice inside granted scope at most; it is never
a BADF authority decision.
