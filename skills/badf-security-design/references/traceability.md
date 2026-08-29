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
coverage and coherence are reconstructable in both directions. (No new global ID family is invented at
freeze — a plain `security-composition` object is sufficient; a dedicated family waits for proven need in
WP-SEC-B.)

| Threat / Abuse | Source (arch/solution) | Sec-Req | Control | Verification obligation |
| :--- | :--- | :--- | :--- | :--- |
| THR-014 | TB-03 · API-017 | SEC-REQ-014 | CTRL-022 | SEC-TEST-031 |
| ABUSE-008 | REQ-021 · API-017 | SEC-REQ-014 | CTRL-022 | TEST-SEC-031 |
