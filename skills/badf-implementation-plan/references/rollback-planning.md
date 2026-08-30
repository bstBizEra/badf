# Rollback planning

Each WP declares reversibility, or explains its irreversibility and the recovery mechanism that replaces
rollback (IMP-I13). The `rollback-plan` artifact carries, per release unit:

```text
trigger              what condition initiates rollback
scope                what is reverted
procedure            the executable steps
owner                who is accountable
data implications    state/data effects
migration reversal   how a schema/data migration is undone (or why it cannot be)
stop condition       when to stop and escalate instead of continuing
proof                that the rollback remains executable
```

An irreversible WP is not forbidden — but it must say so and name what recovery replaces rollback.
