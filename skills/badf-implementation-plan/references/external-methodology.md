# External methodology provenance

Status: **REFERENCE / ADAPT ONLY — no external executable vendored, no external tool granted authority.**

`badf-implementation-plan` adapts external planning methodologies into BADF's governed-WP contract. The
external projects are references, not BADF authority.

## Dispositions

| Source | BADF ADAPTs | BADF does NOT adopt |
| :--- | :--- | :--- |
| GitHub **Spec Kit** (`specify/plan/tasks/taskstoissues/implement/converge`) | plan → decomposition → tracker projection; cross-artifact analysis; convergence thinking | tasks as authoritative execution units; duplicating G01–G05 (specify/plan) |
| **obra/Superpowers** (`writing-plans`, worktrees) | zero-context implementation plans; exact implementation surfaces; independently testable work; TDD; isolated worktrees; review handoff | 2–5-minute steps as the **Work Package** granularity (those are execution steps *inside* a WP); automatic mutation authority |
| **mattpocock/skills/`to-tickets`** | tracer-bullet vertical slices; the blocker graph; the execution frontier; fresh-context sizing; **expand → migrate → contract** for wide refactors | the tracker ticket itself as execution authority |

## Posture

```text
plan → task/ticket = tracking projection      (NOT: ticket = authority)
Plan → Governed Work Package = the bounded execution contract
```

External capability can shape a plan; it can never expand authority. Any future vendoring or direct
execution requires a separate external-skill admission WP under `docs/07-skills-governance.md`.
