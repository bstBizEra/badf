# G05 contract

`badf-security-design` composes into the **existing** G05 — **Security, privacy and AI safety** — and
changes **no** `lifecycle.json`. G05's contract, unchanged, is:

| Field | Value (from `lifecycle.json`) |
| :--- | :--- |
| id | `G05` |
| name | Security privacy and AI safety |
| owner_role | `security_authority` |
| minimum_change_class | `C2` |
| required_evidence | `threat-model`, `privacy-assessment`, `supply-chain-plan`, `security-approval` |
| exit_criteria | threats and abuse cases controlled · privacy obligations addressed · dependency and secret controls planned · residual risk owned |

## What the skill authors vs. what authority produces

```text
badf-security-design AUTHORS (design evidence):     security_authority PRODUCES (authority):
  threat-model                                        security-approval
  privacy-assessment                                  residual-risk acceptance
  supply-chain-plan
```

The skill normalizes its specialists into the **three design artifacts**; the **fourth**,
`security-approval`, is the owner_role's and references the exact digests of the three plus the
architecture and solution baselines (SEC-I13, and see `references/normalization.md`).

## Boundaries

- **No new gate.** Security design is G05 evidence, not a "Security Design gate". The lifecycle is
  untouched.
- **No self-approval.** `disposition: PASS` on a G05 dossier is the gate + authority's, never the skill's
  (SEC-I12/I13).
- **Design, not verification.** G05 is pre-implementation. Implementation security is verified later at
  G08/G09 by `badf-security-assurance` (`security-validation` is a G09 evidence type), never inferred from
  the absence of a G05 design finding (SEC-I14).
