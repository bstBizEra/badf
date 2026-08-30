# Dependency graph and execution frontier

The central artifact is a **graph**, not a task list. Each node is a Governed Work Package; edges are
typed and must not be collapsed:

| Edge | Meaning |
| :--- | :--- |
| `blocked_by` | execution cannot begin until the other WP is CLOSED |
| `composition_after` | may be implemented independently, but must **land** after another WP |
| `requires_artifact` | consumes another WP's produced contract |
| `conflicts_with` | cannot execute concurrently safely |

The blocking dependencies are valid, resolve, and are **acyclic** (IMP-I05) — the existing
`check_work_breakdown` already enforces the acyclic check on `work-breakdown`.

## The execution frontier

```text
EXECUTION FRONTIER = all WPs where
    blockers are CLOSED
  AND baselines remain current      (IMP-I16 — a stale baseline blocks)
  AND required authority exists     (IMP-I07)
  AND budget + stop conditions declared  (IMP-I11/I12)
```

`READY` is derived from the frontier, never asserted; a GitHub Issue being "ready-for-agent" does not make
a WP executable (IMP-I14).
