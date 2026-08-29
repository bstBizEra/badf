# Authorization-design contract

The canonical BADF authorization concept is **`authorization-design`**, not strictly RBAC — because BADF
projects may need RBAC, ABAC, ReBAC, tenant-scoped RBAC, policy-based, ownership-based, or hybrids. RBAC
is **one** supported model; an `rbac-designer` skill is a specialist methodology for the RBAC case. This
keeps the architecture future-proof.

## Canonical contract

Every protected operation resolves the tuple:

```text
principal · resource · action · scope · context · policy · decision · audit
```

- **decision point** — where the decision is made, and its **default behavior**;
- **SOL-I05 default deny** — a tuple matching no rule resolves to **DENY** (`NO MATCH = DENY`);
- **SOL-I06 audit** — a security-sensitive decision defines an audit obligation.

## Seams it must satisfy

- **SOL-I04** — every protected API operation has resource, action, scope, decision point, default behavior; no "authenticated user can call the endpoint" pseudo-authorization.
- **SOL-I05** — unmatched tuples deny.
- **SOL-I06** — privileged decisions emit audit events.
- **SOL-I02** — a trust transition the model relies on must exist in the architecture baseline; solution-design does not invent a trust boundary.

Authorization detail (roles, scopes, policies) composes into **G04** detailed evidence, reconciled
against the architecture spine's trust boundaries.
