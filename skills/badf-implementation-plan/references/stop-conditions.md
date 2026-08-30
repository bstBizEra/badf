# Stop conditions

Each WP declares the conditions under which execution **halts immediately** (IMP-I12) — authority, safety,
integrity and budget:

```yaml
stop_conditions:
  - AUTHORITY_CONFLICT
  - BASELINE_STALE
  - CREDENTIAL_EXPOSURE
  - UNEXPECTED_DESTRUCTIVE_SCOPE
  - POLICY_BYPASS
  - EVIDENCE_CORRUPTION
  - BUDGET_EXHAUSTED
```

These are the global BADF Engineering-Loop stops made **per-WP and machine-checkable**. `BASELINE_STALE`
ties to IMP-I16: a WP planned against a superseded input stops rather than silently proceeding. Without an
explicit stop contract, an autonomous agent knows a stop rule exists but not where the boundary is here.
