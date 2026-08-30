# Review lenses — routed by change class and surface, isolated until sealed

Apache Magpie's contribution is the *isolated axis*: each review pass runs alone and no pass sees another's
findings before its own are persisted. BADF already requires that of councils (docs/03 step 4); this
reference turns it into routing, so a C1 documentation change is not reviewed by seven agents.

## Routing by change class

| Change class | Mandatory | Additional lenses (select by surface) |
| :--- | :--- | :--- |
| C1 | one independent review, **correctness** lens | — (a second lens only when the surface demands it) |
| C2 | council; **correctness** + **quality/test** | architecture · data/integration · operations/resilience · conventions/maintainability |
| C3 | council; **correctness** + **quality/test** + **data/integration** | architecture · operations/resilience · conventions/maintainability · compliance |

Lens names are docs/03's ("architecture, security/privacy, data/integration, quality/test,
operations/resilience, UX/accessibility, compliance, composition/integration"). Selection is recorded on
the review contract before sealing; a lens added after a finding appeared is a new sealed pass, not an
amendment.

## What each lens asks

- **correctness** — did this change introduce a regression, a wrong result, a broken invariant, an
  unhandled state? Defect-first; full diff; call sites.
- **quality/test** — do the tests test the behavior (not the implementation)? What did the author's
  red/green evidence actually observe? What is untested?
- **data/integration** — migrations, compatibility, ordering, idempotency, contracts across a boundary.
- **operations/resilience** — failure modes, timeouts, retries, observability of the change in production.
- **conventions/maintainability** — declared repository conventions only; taste is not a finding.
- **architecture** — **routed**: an architecture lens is `badf-architecture` ASSURE run against the
  composed tree (`badf_gate.py assure`), binding one baseline and one observed revision, reporting drift as
  evidence. G08 does not infer an architecture from code and declare it compliant.

## Security — a security-kind finding is a finding; a security lens is assurance

Any lens may report a **security-kind** finding introduced by the diff — an authorization bypass, a
hardcoded secret, an injection, an unsafe deserialization — as a canonical finding with `kind:
[security]`. That is defect-first review doing its job.

A **security lens** — systematic security code review, SAST, SCA / dependency reachability, secrets
scanning, IaC review, attack-oriented API/web/mobile review, remediation verification — is *security
assurance*. BADF names that capability `badf-security-assurance` (G08/G09; `badf-security-design`
SEC-I14: absence of a design finding never establishes implementation security). It is **named, not
built**. Until it exists, every G08 review declares the security lens as non-coverage:

```yaml
non_coverage:
  - surface: security assurance (SAST / SCA / secrets / IaC / attack-oriented review)
    reason: badf-security-assurance is named, not built
    impact: implementation security not established by this review
```

G08 does not absorb that lens to close the gap (VER-I16); it declares the gap.

## Isolation, made checkable (VER-I06)

Each lens pass persists its ballot — findings, non-coverage, completion, `sealed_input_digest` — before
any synthesis reads it. At VER-C the gate refuses a synthesis that cites a ballot whose digest differs
from the council's, or that cites a ballot that does not exist.
