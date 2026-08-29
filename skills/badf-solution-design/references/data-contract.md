# Data-design contract

The output contract for the database/persistence specialist (routed on entity / constraint / index /
migration signals). Composes into **G04** detailed evidence (coherent with `data-model`). The specialist
owns persistence detail; it does **not** own data ownership — that is architecture.

## Output contract

- **entities** — with identity, fields, nullability, cardinality, and lifecycle/state;
- **constraints** — keys, uniqueness, referential integrity, invariants;
- **normalization** and deliberate denormalization, with the reason;
- **indexing** — for the access patterns the API/UX imply;
- **migrations** — a reversible or evolvable plan for any breaking change (SOL-I10).

## Architecture ownership boundary

The data specialist may decide table structure, normalization, constraints, indexes and migration
mechanics. It **must not** decide, for example, "Service B directly accesses Service A's database" — that
is an architecture ownership decision (SOL-I02). Given an architecture ruling ("Customer Service owns
Customer data"), the specialist designs `customers`, `customer_addresses`, `customer_preferences`,
indexes, constraints and migration strategy **within** that ownership.

## Seams it must satisfy

- **SOL-I07** — the persistence model agrees with the API request/response models on identity, nullability, cardinality, state, lifecycle, ownership.
- **SOL-I10** — a breaking persistence change carries a reversible/evolvable migration plan.
- **SOL-I02** — every data owner and cross-service access resolves against the architecture baseline.
