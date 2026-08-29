# Traceability

The detailed-design spine: a G02 requirement fans out to the specialist elements that satisfy it, and
each element binds forward to a test obligation. Architecture surrounds the spine as the coherence frame.

## The spine

```text
G02 requirement
   ├──→ UX task / system behavior
   ├──→ API operation
   ├──→ authorization action
   ├──→ data operation / entity
   ├──→ audit event
   └──→ accessibility obligation
                 │
                 ▼
           test obligation
```

## Architecture surrounds it

```text
            G04 architecture baseline
           /          |           \
      boundary     interface     ownership
          |            |             |
          ▼            ▼             ▼
UX flow → API operation → authorization → data operation
   └──────────┴──────────────┴──────────────┘
                    │
                    ▼
              audit / telemetry
                    │
                    ▼
              test obligations
```

## Rules

- **Backward:** every material element resolves to a `REQ` / `NFR` / declared G03 need / architecture
  constraint (SOL-I01). No orphan design.
- **Forward:** every priority element carries a test obligation; coverage is reconstructable from the
  solution-composition matrix in both directions.
- **Across:** the spine's rows must satisfy the SOL-I01…I12 seams (`cross-artifact-consistency.md`); a
  row that traces cleanly but fails a seam is still incoherent.
- Bidirectional coverage is computed from the link graph — redundant hand-maintained reverse links are
  prohibited, as in the G02 RTM.
- Traceability binds to the architecture **baseline revision**; if the baseline moves, the affected rows
  are re-reconciled, not assumed still coherent.
