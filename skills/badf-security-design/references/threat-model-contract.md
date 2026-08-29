# Threat-model contract

A threat model is **structural and machine-addressable**, not prose. "An attacker might gain access" is
not a threat; it names no asset, no entry point, no path, no disposition. Each material threat resolves
to the baselines it reasoned over (SEC-I01/I02) and carries a disposition (SEC-I03).

## Threat shape

```yaml
threat_id: THR-...
source:                       # provenance — resolves to the baselines (SEC-I02)
  architecture_elements: [...]
  trust_boundaries: [...]
  data_flows: [...]
  api_refs: [...]
  requirement_refs: [...]
actor: external-attacker      # or: malicious-insider, compromised-dependency, compromised-agent, …
asset: customer-account
entry_point: API-017
scenario:
  preconditions: [...]
  attack_path: [...]
  impact: [...]
classification:
  category: authorization     # authn, authz, injection, replay, tampering, disclosure, dos, supply-chain, agent, …
  cwe_refs: [...]
  owasp_refs: [...]
risk:
  likelihood_basis: [...]     # evidence-grounded reasoning, not agent self-confidence
  impact_basis: [...]
controls:
  - control_ref: CTRL-...
    type: preventive          # or detective, corrective, deterrent
residual_risk:
  status: UNASSESSED          # UNASSESSED | MITIGATED | DEFERRED | ACCEPTED-PENDING-AUTHORITY
verification_obligations:
  - SEC-TEST-...              # downstream obligation (SEC-I04); assurance verifies later, not here
```

## Rules

- **Provenance (SEC-I02).** Every `source.*` ref resolves to a real element of the architecture or
  solution baseline. A threat against a component the baseline does not contain is either non-coverage
  (declare it) or an `ARCHITECTURE_CHANGE_REQUIRED` signal — never an invented boundary.
- **Disposition (SEC-I03).** Every material threat is `controlled` (has ≥1 `controls[]`), `DEFERRED`
  (explicit, with reason), `blocked`, or submitted for independent residual-risk acceptance. A threat
  with no disposition is unfinished work.
- **Evidence-grounded risk.** `likelihood_basis` / `impact_basis` cite the baseline and the data
  classification — not a bare severity label. BADF substitutes evidence for agent self-confidence.
- **Verification is an obligation, not a result (SEC-I14).** `verification_obligations` name what
  *assurance* must later prove; the threat model does not itself prove the implementation secure.
- **Residual risk is not accepted here (SEC-I12).** The skill sets `residual_risk.status`; only
  `security_authority` moves it to accepted.

## The example this catches

```text
architecture:  API → Payment Service crosses TB-03; data classification = FINANCIAL
solution:      POST /payments  (principal=customer, action=payment:create, resource=account, scope=own-account)
threats:       credential compromise · BOLA · replay · privilege escalation · transaction tampering
controls:      step-up authentication · ownership authorization · idempotency/replay protection ·
               transaction integrity · audit obligation
```

Each threat binds the exact architecture element and API/solution ref it reasons over — reproducible,
not free-floating.
