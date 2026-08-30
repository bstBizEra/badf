# Authority and risk

**Authority is derived, never chosen.** BADF already has `change_class` (C0–C3) and an authority matrix
that maps class → required roles. The plan **cannot reduce** the authority required by change class,
reserved actions, target environment or upstream constraints (IMP-I07).

```text
risk/change classification  →  authority matrix  →  required authority
   (NOT: agent chooses an authority class)
```

```yaml
change_class: C2
authority_requirement:
  derived_from: C2
  required_roles: [product_owner, engineering_owner, quality_authority, service_owner]
risk_factors: [contract_change, customer_visible]
```

**Do not introduce an A0/A1/A2 authority-class system** — it would duplicate and could contradict
`change_class`. The single source is the change class and the matrix.
