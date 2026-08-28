# External methodology disposition

BADF adapts external architecture methods; it never adopts them wholesale. "Adopt, adapt, alias": keep the useful patterns, reject anything that would make a diagram the source of truth or let missing information become inferred compliance.

## `muthub-ai/c4-skills/c4designer` — `ADAPT`

Useful patterns adopted: Context → Container → optional Component/Code zoom; supporting Dynamic and Deployment views; explicit element responsibility; explicit technology; labelled directional relationships; assumptions separated from facts; an architecture review checklist; design / retro-document / review / update modes.

Not adopted: Mermaid as the canonical storage format; mandatory human validation at each drafting phase; diagrams as the architecture source of truth. BADF is autonomous-capable — missing information becomes an explicit assumption, open decision, research question or blocker according to authority and uncertainty, not a stall.

## `muthub-ai/c4-skills/adr-scribe` — `ADAPT`

Useful ADR core adopted: Context / Decision / Alternatives / Consequences / Status. BADF extends it with traceability and architectural binding (`adr-contract.md`). Do not conflate `ADR-NNNN` (a system architecture decision) with `BADF-DEC-NNNN` (a governance decision) — ARCH-I10.

## Architecture-review patterns — `ADAPT`

Useful checks adopted: dependency direction, layer violations, module/bounded-context boundaries, circular dependencies, private/internal API leakage, shared-model pollution, ADR drift, cross-cutting concern placement.

BADF tightens these by requiring a declared baseline. If architecture intent is missing, ASSURE may report observations, but it must not infer an architecture from code and then declare that inferred architecture compliant:

```text
NO BASELINE  ≠  COMPLIANT
```
