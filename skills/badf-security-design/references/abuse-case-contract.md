# Abuse-case contract

Abuse cases are kept **separate from threat models**: threat models are *structural* (attacker vs. an
asset across a boundary); abuse cases capture **adversarial business behavior** — a legitimate flow
driven to an illegitimate end. Both feed `threat-model` normalization, but they are authored distinctly.

## Shape

```yaml
abuse_case_id: ABUSE-...
requirement_ref: REQ-...       # the legitimate behavior being abused
narrative: "..."               # what the adversary does with the legitimate flow
derived_sec_req_refs: [SEC-REQ-...]
control_refs: [CTRL-...]
verification_obligation: TEST-SEC-...
```

## The example (stronger than a tag)

```text
REQ-021   "Customer may request one refund."
   ↓
ABUSE-008 "Customer automates repeated refund submissions across concurrent sessions."
   ↓
SEC-REQ-014  refund request must enforce idempotency + business-level replay protection
   ↓
API-017   POST /refunds
   ↓
CTRL-022  idempotency + transaction-level uniqueness
   ↓
TEST-SEC-031  parallel replay test
```

That full chain is far stronger than tagging `POST /refunds` with "OWASP API4" — it names the business
requirement abused, the derived security requirement, the concrete control, and the verification
obligation.

## Rules

- **Business provenance.** Every abuse case names the `requirement_ref` (the legitimate behavior) it
  subverts. An abuse case with no legitimate behavior behind it is a threat, not an abuse case.
- **Full chain (SEC-I04).** An abuse case that stops before a derived requirement / control / verification
  obligation is unfinished — the value is the traceable chain, not the narrative.
