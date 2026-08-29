# Security-requirements contract

Security requirements are **derived** — from threats, abuse cases, NFRs and regulatory obligations — but
they are **cross-cutting**: every other security specialist can produce them, so `security-requirements`
stays a contract, not (at freeze) an independent executor.

## Shape

```yaml
sec_req_id: SEC-REQ-...
derived_from:                 # upstream trace (SEC-I04)
  threat_refs: [THR-...]
  abuse_case_refs: [ABUSE-...]
  requirement_refs: [REQ-..., NFR-...]
statement: "privileged operations require phishing-resistant MFA"
control_refs: [CTRL-...]
verification_obligation: SEC-TEST-...   # downstream trace (SEC-I04)
scope_impact: NONE            # NONE | MATERIAL  (MATERIAL → REQUIREMENT_CHANGE_REQUIRED)
```

## Rules

- **Bidirectional trace (SEC-I04).** A security requirement traces **upstream** to a threat / abuse case /
  requirement / NFR and **downstream** to a verification obligation. An orphan security requirement is
  either undeclared scope or dead work.
- **No silent scope expansion (SEC-I04).** If a derived requirement materially changes product behavior
  or scope (`scope_impact: MATERIAL`), it does **not** rewrite G02 in place:

  ```text
  REQUIREMENT_CHANGE_REQUIRED → G02 requirements revision → solution/architecture reconciliation → resume G05
  ```

  Security design proposes; the requirements gate (G02) and its authority decide. G05 never silently
  rewrites G02.
- **Derived, not invented.** A security requirement with no `derived_from` is not a requirement — it is an
  assertion. Provenance is mandatory.
