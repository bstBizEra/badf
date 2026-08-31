# Routing

The root skill routes each concern to the specialist that owns it, and selects **only** the specialists
the work needs. External specialist skills are **REFERENCE / ADAPT**, never BADF authority:

```text
external skill = REFERENCE / ADAPT     (not:  external skill = BADF authority)
```

## Signal → specialist

| Signal | Specialist (adapter) |
| :--- | :--- |
| journey, screen/state, task flow, recovery behavior | `product-design-and-ux` adapter |
| role, permission, resource/action, tenant scope | `authorization-design` (RBAC/ABAC/ReBAC one model) adapter |
| entities, constraints, index, migration | `database-schema-designer` adapter |
| endpoint/resource/event, error model, pagination, version | `api-design` adapter |
| keyboard, focus, semantics, contrast, assistive technology | accessibility adapter |
| architecture boundary / topology / trust decision | **`badf-architecture`** (the spine, not an adapter) |
| uncertainty requiring evidence | **`badf-research`** |
| security threat / risk decision | **`badf-security-design`** (ACTIVE; owns threat model, privacy assessment, supply-chain plan) |

## Routing rules

- Route the minimum: an unneeded specialist is scope, not thoroughness.
- A signal that names an architectural boundary/interface/owner routes to `badf-architecture`, not to a
  specialist — solution-design details interfaces, it does not invent them (SOL-I02).
- An adapter's output is a **contract**, adapted to the BADF domain reference; the external skill's own
  vocabulary, scoring, or lifecycle claims are not adopted as BADF authority.
- Overlapping signals resolve to the more specific domain; a genuinely cross-cutting concern (e.g. an
  authorization decision surfaced in a UX flow with a data effect) is composed across its adapters and
  reconciled at the seam, not forced into one.
- No adapter is **activated** at contract-freeze — routing names who *would* own each concern; specialist
  activation is a later WP.
