# ADR contract

Material architectural choices are recorded as Architecture Decision Records. BADF adapts the classic ADR core (Context / Decision / Alternatives / Consequences / Status) and extends it with traceability and architectural binding.

## `ADR-NNNN` is not `BADF-DEC-NNNN` (ARCH-I10)

```text
ADR-NNNN      a product/system architecture decision (this contract)
BADF-DEC-NNNN a BADF governance/authority decision (the framework's decision ledger)
```

They are different objects. Neither substitutes for the other, and an ADR never grants governance authority.

## Canonical ADR shape

```text
ADR-NNNN
├── title
├── status
├── context
├── decision_drivers[]
├── constraints[]
├── alternatives[]
├── decision
├── positive_consequences[]
├── negative_consequences[]
├── risks[]
├── affected_elements[]        (baseline elements this decision binds to -- ARCH-I05)
├── requirement_refs[]
├── nfr_refs[]
├── evidence_refs[]
├── supersedes
└── superseded_by
```

## Decision vs constraint

A material architectural choice with no real alternative distinguishes `DECISION` from `CONSTRAINT`: a mandatory external constraint (a platform mandate, a regulatory requirement) is recorded as a constraint, never dressed up as a choice that was weighed. `alternatives[]` for a genuine decision names what was actually considered and rejected, with the driver that rejected it.

## Binding

Every ADR binds to the baseline elements it affects (`affected_elements[]`) and to its upstream drivers (`requirement_refs[]`, `nfr_refs[]`). An ADR that affects nothing, or cites an unknown requirement/NFR, is not a governed decision. In ASSURE, an active ADR is checked against observable implementation rules and returns `CONFORMANT` / `NONCONFORMANT` / `INDETERMINATE` / `SUPERSEDED` / `NOT_OBSERVABLE` — and `INDETERMINATE` never becomes PASS.
