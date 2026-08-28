# Canonical architecture model

BADF does not make a Mermaid file the architecture. The authoritative artifact is a structured **architecture baseline** from which C4 and other views are rendered (ARCH-I02).

## Baseline shape

```text
Architecture Baseline
├── identity                 (system/product id)
├── baseline_revision        (the pinned revision this baseline describes)
├── upstream_requirements    (PRD / requirement / NFR refs)
├── elements                 (systems, containers, components)
├── relationships            (directional, intent-bearing -- see design-mode.md)
├── boundaries               (system / module / ownership / control-plane)
├── topology                 (deployment / environment)
├── trust_boundaries
├── data_flows
├── data_ownership
├── interfaces               (declared public contracts)
├── nfr_allocations
├── adr_references
├── operability_model
├── fitness_obligations
├── assumptions              (kept separate from facts)
├── risks
└── non_coverage
```

## Views are projections

```text
Architecture Baseline
   ├── C4 Context          (required by default)
   ├── C4 Container        (required by default)
   ├── C4 Component        (optional; complex/high-risk containers only)
   ├── Deployment
   ├── Dynamic flows
   ├── Data-flow view
   └── Trust-boundary view
```

A view is a projection of the baseline. It renders elements, relationships and boundaries that already exist in the baseline; it never introduces an architectural claim absent from it. When a diagram and the baseline disagree, the baseline is authoritative and the diagram is the drift.

## Element and boundary rules

- Every material element belongs to at least one declared boundary (ARCH-I03).
- Every material relationship has a direction and an intent (ARCH-I04); a bare `A → B` is not an architecture relationship.
- Every legitimate boundary crossing is named as an interface; an undeclared crossing is a boundary violation, not an implicit allowance.
- The baseline digest changes whenever a material element, relationship or boundary changes, so a stale baseline cannot silently pass as current.
