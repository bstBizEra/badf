# Composition contract

How specialist contracts become one solution. `badf-solution-design` COMPOSES / ROUTES / RECONCILES; it
does not generate a monolith and does not own any specialist's internal method.

## The composition

```text
SPECIALIST DESIGN → CROSS-CONTRACT RECONCILIATION → CONSISTENT SOLUTION DESIGN
```

Each specialist emits a bounded output **contract** (see the per-domain references). Composition:

1. collects the specialist contracts required for the routed concerns;
2. assembles the **solution-composition matrix** (`cross-artifact-consistency.md`) — one row per
   requirement, binding UX / API / authorization / data / audit / accessibility / test refs;
3. runs the SOL-I01…I12 seam checks over the assembled set;
4. records every unresolved inconsistency and blocker explicitly (silence is not coherence);
5. packages the coherent result as G03/G04 evidence for the canonical gate.

## What composition owns vs delegates

| Concern | Owner |
| :--- | :--- |
| the coherent whole; seam reconciliation; the composition matrix | `badf-solution-design` |
| structural boundaries, topology, trust, ownership, ADRs | `badf-architecture` (the spine) |
| each domain's internal design (how UX/authz/data/API/a11y behaves) | the specialist adapter |
| deterministic evidence validation | the canonical `badf_gate.py` |
| lifecycle disposition | authority |

Composition may **detail** an architectural interface; it may **not** create one absent from the
baseline (SOL-I02) — that is an `ARCHITECTURE_CHANGE_REQUIRED` hand-off, not a silent edit.

## Reconciliation output

A composition run yields, at minimum:

- the solution-composition matrix (requirement → specialist refs);
- the list of seam findings (which SOL-I invariant, which artifacts, resolved / open);
- the unresolved decisions and blockers;
- the G03 and G04 evidence the package will carry;
- explicit non-coverage (a routed concern deliberately not designed, and why).

A composition with open blocking seam findings is **not** ready to package; it returns to SPECIALIZE or
raises the architecture hand-off. It never self-authorizes a gate outcome.
