# Security traceability

Security conclusions are only defensible if they trace both directions: **upstream** to what motivated
them, **downstream** to how they will be verified (SEC-I04). The chain is the evidence.

## The chain

```text
architecture baseline + solution baseline   (SEC-I01, exact digests bound)
        │
        ▼
threat / abuse case            (SEC-I02: resolves to real assets/interfaces/flows/boundaries)
        │
        ▼
security requirement           (SEC-I04: derived, never invented; scope_impact declared)
        │
        ▼
control                        (disposition of the threat — SEC-I03)
        │
        ▼
verification obligation        (SEC-I14: what ASSURANCE must later prove — G08/G09, not here)
```

## Rules

- **Exact baseline (SEC-I01).** Every artifact records the exact architecture and solution baseline
  digests it reasoned over. A conclusion drawn against a since-changed baseline is stale, not valid.
- **Bidirectional completeness (SEC-I04).** A threat with no disposition, a security requirement with no
  verification obligation, or a control that traces to no threat, is an incomplete chain — a finding, not
  a footnote.
- **Downstream is an obligation, not a result (SEC-I14).** The verification obligation names what a later
  assurance capability must prove. Security design never marks it satisfied; that would be verifying a
  build it has not seen.
- **Non-coverage declared (SEC-I11).** A surface not traced (a component out of scope, a specialist
  `NOT_APPLICABLE_WITH_REASON`) is named in the trace, so an absent link reads as *declared out of scope*,
  never as *secure*.

## Security-composition matrix

The security-design equivalent of the RTM — one row per material threat/abuse case, binding its chain so
coverage and coherence are reconstructable in both directions.

| Threat / Abuse | Source (arch/solution) | Sec-Req | Control | Verification obligation |
| :--- | :--- | :--- | :--- | :--- |
| THR-014 | TB-03 · API-017 | SEC-REQ-014 | CTRL-022 | SEC-TEST-031 |
| ABUSE-008 | REQ-021 · API-017 | SEC-REQ-014 | CTRL-022 | TEST-SEC-031 |

### Enforcement status

WP-SEC-B gives the matrix a schema (`schemas/security-composition.schema.json`) and STRUCTURAL
validation in the one canonical gate — `badf_gate.py security <matrix>` — never a second validator
(SEC-I15). Each `threats[]` row carries `security_id` (`^SEC-THR-[0-9]{3,}$`), a `source` provenance
object, a `disposition` (`controlled|deferred|blocked|pending-authority`), and optional
`control_refs`/`security_requirement_refs`/`verification_refs`/`residual_risk`. Controls, each
mutation-killed:

| Control | Rule (matrix-internal) | Invariant | Status |
| :--- | :--- | :--- | :--- |
| — | a non-empty matrix (an empty one models nothing) | — | **enforced** (WP-SEC-B) |
| SEC-C01 | unique `security_id` | — | **enforced** (WP-SEC-B) |
| SEC-C02 | every threat binds ≥1 provenance `source` ref | SEC-I02 | **enforced** (WP-SEC-B) |
| SEC-C03 | a `controlled` threat carries ≥1 `control_refs` | SEC-I03 | **enforced** (WP-SEC-B) |
| — | `residual_risk` cannot be a bare `ACCEPTED` (enum) | SEC-I12 | **enforced by schema** (WP-SEC-B) |

The **cross-artifact seams** — SEC-I04 bidirectional traceability (a sec-req resolves up *and* down),
SEC-I01 exact-baseline digest binding, and the *semantic* resolution of every ref against the
architecture/solution artifacts — **cannot** be enforced until those artifacts and the sec-req/control
registries exist; they are **deferred to WP-SEC-C**, honestly, not faked. `residual_risk`'s exclusion of
`ACCEPTED` makes SEC-I12 structural: the skill has no value with which to self-accept risk.
