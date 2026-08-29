# Normalization — specialists → G05 evidence

Specialist outputs are **normalized** into the three G05 **design** artifacts. This is the mapping that
keeps security design inside the existing lifecycle instead of inventing a new gate.

```text
Specialists                                             G05 design artifact
─────────────────────────────────────────────────────  ─────────────────────
threat-model, abuse-case-analysis, security-requirements,
  api-security-design, iam-security-design,
  ai-agent-security-design                          →   threat-model
privacy-analysis (classification, purpose, collection,
  retention, disclosure, deletion)                  →   privacy-assessment
supply-chain-design (dependency/provenance/SBOM/
  signing/secret-distribution/update policy)        →   supply-chain-plan

security-approval                                   →   NOT produced by the skill — security_authority
```

## Rules

- **Every specialist output lands in exactly one design artifact** (above) or is declared non-coverage
  (SEC-I11). A finding that maps nowhere is a normalization defect, not a silent drop.
- **`security-approval` is never authored here.** It is produced by `security_authority` after reviewing
  the three artifacts, and it references the exact digests of `threat-model`, `privacy-assessment`,
  `supply-chain-plan`, the architecture baseline and the solution baseline — so approval is reproducible,
  not a floating `"approved": true` (SEC-I13).
- **Residual risk is reported, never accepted.** Each threat's `residual_risk.status` may be
  `UNASSESSED` / `MITIGATED` / `DEFERRED` / `ACCEPTED-PENDING-AUTHORITY`; only `security_authority` moves
  it to accepted (SEC-I12).
- **Non-coverage is explicit.** Surfaces not modelled (a component not in the baseline, a specialist
  recorded `NOT_APPLICABLE_WITH_REASON`) are named in the artifact, so silence is never read as coverage.

## What normalization is not

Normalization does not compute a verdict, a score, or a pass. It arranges specialist *design* evidence
into the shapes G05 already expects. The gate validates the evidence; the authority approves it.
