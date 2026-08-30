# G08 ≠ G09 — engineering verification is not independent validation (VER-I16)

The lifecycle already separates them. This reference keeps a security-capable G08 reviewer from being
mistaken for G09.

```text
G08 — ENGINEERING VERIFICATION  (owner quality_authority · minimum C1)
  Did this implementation introduce a correctness, security, contract or integration defect?
  independent-review · integration-test · contract-test · composed-tree-test

G09 — INDEPENDENT QUALITY AND SECURITY VALIDATION  (owner quality_authority · minimum C2)
  Does the candidate withstand risk-based quality, security, performance and resilience validation
  under production-representative conditions?
  quality-validation · security-validation · performance-test · resilience-test
```

## What a G08 reviewer may find — and what it does not replace

A G08 review **may** report, as canonical findings:

```text
authorization bypass introduced by the diff
hardcoded secret
SQL injection in a changed query
unsafe deserialization in a new path
```

A G08 review **does not replace**:

```text
penetration testing
risk-based security validation against a threat model
performance and capacity testing against budgets
resilience, failover and recovery testing
```

Those are `security-validation`, `performance-test`, `resilience-test` — G09 evidence, produced under
G09's independence requirement ("risk-based validation independent") and production-representative
conditions (docs/01: "independent validation must use production-representative conditions and must
identify untested surfaces").

## The canonical rule

```text
G08 security review  ≠  G09 security validation
G08 integration test ≠  G09 performance / resilience test
G08 APPROVED         ≠  G09 opened
```

A G08 dossier that carries a `security-validation` object is not "ahead"; it is out of scope. G09 has its
own dossier, its own composed binding and its own decision. Where G09 is required by change class (C2+),
G08's approval opens G09 — it does not satisfy it.
