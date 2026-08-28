# Research routing and authority

Status: frozen contract v0.2 (`BADF-WP-0031`, evolved by `WP-2026-0041`).

## Authority chain

```text
Issue / Discovery
      ↓
BADF-DEM-NNNN
      ↓
BADF-RSR-NNNN
      ↓
BADF-DEC-NNNN
      ↓
WP-2026-NNNN
      ↓
Branch → PR → main
```

Research sits between demand and decision. A research disposition does not create authority downstream by itself. Research may read, search, analyse, run permitted tests and perform explicitly disposable experiments within its demand and tool boundaries; it may not silently turn investigation into implementation.

Branch class for a research run: `research/BADF-RSR-NNNN-<slug>`.

## Normative invariants

- **RSR-I01** — Research output cannot grant implementation authority. `authority.implementation_authority` is fixed to `false` by the schema. **`RESEARCH_SUFFICIENT` ≠ `IMPLEMENTATION_AUTHORIZED`.**
- **RSR-I02** — A material research conclusion must be traceable to evidence: every finding references claims and every VERIFIED claim references qualifying primary evidence.
- **RSR-I03** — `OBSERVED`, `REPORTED`, `INFERRED`, `HYPOTHESIS` and `DECIDED` remain semantically distinct; an inference cannot be serialized as an observation.
- **RSR-I04** — Contradictory evidence cannot be silently discarded.
- **RSR-I05** — Required independent challenge cannot be satisfied by the originating researcher or session.

## Bounded framing rule

The research record must carry explicit assumptions, decision context and one or more stop conditions. These fields constrain inquiry; they do not expand authority. If the question, scope, depth, tool boundary or downstream decision context changes materially, amend through the governed demand path or open a new research run.

## Challenge and council reuse

BADF has ONE council mechanism. Research reuses it; there is no research-specific council.

Challenge is mandatory for `D4`, `D5` and `R06`, and may be required by framework policy or an unresolved high-risk contradiction. First-round ballots remain independent and sealed before synthesis. The researcher cannot count toward their own required challenge; duplicate identities cannot increase quorum; every reviewer declares non-coverage; minority risks and material contradictions remain visible.

Council opinion is advisory unless the authority matrix makes that review binding. A ballot never creates implementation authority.

## No competing mechanisms

- no router beside root `skills/badf-research/SKILL.md`;
- no validator beside `scripts/badf_gate.py`;
- no research-specific authority engine or council;
- no research registry beside `badf/skill-registry.json`;
- no research memory store that substitutes for evidence.

Subskills may specialize collection or analysis, but they consume and produce the canonical contracts defined by this family.
