# Rollback and migration — reconciled together, because they constrain each other

PRDY-I13, PRDY-I14. These are one reference rather than two because the design's own §12 reconciles
them: a rollback strategy is only meaningful against a specific migration state, and a migration is
only safe if the rollback it permits is the one that exists. Splitting them would produce two documents
each assuming the other's conclusion. This is a Lean consolidation of two genuinely inseparable
concerns, not a dropped concern.

## Rollback maturity vocabulary (PRDY-I13)

```text
DEFINED    a rollback procedure is written down
VALIDATED  the procedure has been checked against the actual candidate and migration state
REHEARSED  the procedure has been EXECUTED and observed to restore service
```

**A rollback document alone does not establish rollback readiness.** `DEFINED` is not a passing state
for a release whose delta makes rollback mandatory. The same shape as backup ≠ restore
(`references/recovery-readiness.md`): the artifact exists, the property is unmeasured.

## Migration / rollback compatibility matrix (PRDY-I14)

Migration state and rollback strategy must be mutually coherent:

```text
Migration shape              Rollback implication
---------------------------  ------------------------------------------------------
additive, backward-readable  code rollback safe; no data rollback needed
destructive (drop/rename)    code rollback UNSAFE without a data restore path
data backfill in-flight      rollback window bounded by backfill completion
queue/message schema change  rollback constrained by in-flight message compatibility
irreversible transform       rollback is restore-only; RPO/RTO become the real bound
```

An incoherent pair — a destructive migration with only a code-level rollback `DEFINED` — is
`NOT_READY`, not `READY_WITH_CONDITIONS`. The condition that would make it ready does not exist yet;
naming it as a condition would record a plan as a mitigation.

## Both resolve, neither re-executes

This skill resolves the G06 release/rollback plan and the migration evidence produced upstream. It does
not run the migration, rehearse the rollback, or judge the migration's correctness — those belong to
their owning gates (PRDY-I01).
