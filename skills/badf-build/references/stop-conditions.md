# Stop conditions dominate (BLD-I13)

The Work Package's `stop_conditions` are loaded at PREFLIGHT and dominate every later stage. In addition
to the WP's own, these always stop mutation:

```text
authority conflict         — the WP, the plan and the observed repository disagree about what is permitted
destructive surprise       — a mutation would delete, rewrite or force beyond the authorized surface
credential exposure        — a secret is read, written or would be committed
policy bypass              — a control, hook, gate or review would be skipped or weakened
evidence corruption        — a baseline, ledger or evidence object cannot be trusted
budget exhaustion          — attempts, time or cost are spent (see retry-and-budget.md)
unexpected scope           — see scope-containment.md
design drift               — see execution-contract.md
```

Stop means: record the transition in the build ledger, package what exists as evidence with declared
non-coverage, and hand off `BLOCKED` or `HUMAN_REQUIRED`. Stop never means: guess, widen, retry
silently, or escalate a subagent's authority to get past the condition.
