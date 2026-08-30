# Decomposition

Approved design → candidate deliverable units → **exactly one Governed Work Package per unit** (IMP-I01).
No naked task escapes into execution: if it is executable, it is a WP.

```text
G01–G05 approved design
        ↓  DECOMPOSE
candidate deliverable units
        ↓  one WP each (IMP-I01)
Governed Work Packages
        ↓  GRAPH
the Work Package DAG
```

## Rules

- **Every WP binds its exact upstream baselines** (IMP-I02) — it implements a specific
  requirement/architecture/solution/security digest, not "the design" in general.
- **Every planned requirement is covered or explicitly deferred** (IMP-I03) — coverage is reconstructable
  from the `work-breakdown` + `test-plan`.
- **Material uncertainty is not decomposed into a WP** — it routes to `badf-research` first, then the
  answer feeds decomposition.
