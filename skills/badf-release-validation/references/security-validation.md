# security-validation — attack-oriented evidence, never self-granted risk acceptance (VAL-I09)

`security-validation` is a **class-aggregator** of independent, attack-oriented and
security-control evidence, normalized into the `security-validation` G09 evidence type the
lifecycle already names. It is the G09 security domain — distinct from the G08 reviewer that may
*find* a defect in a diff (VAL-I17). Scanners produce observations; they are never authority.

## The layering (adapt down, authority up)

```text
badf-release-validation          routes the security obligation (VAL-I02)
        ↓
security-validation              G09 evidence class (this DESIGNED contract)
        ↓  (preferred future)
badf-security-assurance          named, not built — declared non-coverage until it exists
        ↓
OWASP procedure adapters         structured methodology (primary)
        ↓
scanners / test tools            observation producers, never authority
```

Until `badf-security-assurance` exists, `security-validation` is produced here and the missing
dedicated capability is named in non-coverage (VAL-I15) — never silently skipped.

## Primary methodology — OWASP Secure Agent Playbook

The **OWASP Secure Agent Playbook** is the primary methodology: structured, repeatable
procedures yielding OWASP/CWE-grounded findings, not ad-hoc scanning.

```text
security code review        API security          agent security (tool abuse, injection)
SCA (dependency risk)       web security          IaC / configuration security
secrets scanning            mobile security
```

## Tooling adapters — qa-skills security skill

`qa-skills`' security skill contributes **tooling adapters**; each is an observation producer,
never a verdict:

```text
ZAP / DAST                  dynamic attack-surface observations
OSV / SBOM / provenance     dependency + supply-chain observations
Semgrep / SAST              static finding observations
secret scanning             leaked-credential observations
authz tests                 access-control negative-path observations
negative-path tests         abuse-case / forbidden-state observations
```

## The freeze — a finding is not an accepted risk (VAL-I09)

```text
scanner / tester discovers residual risk    →  FINDING (observed)
        ✗ the same validator waives it → accepted        FORBIDDEN
        ✓ the finding is preserved, owned, routed         to security / human authority
```

No security validator may waive, downgrade or accept its **own** discovered residual risk.
Acceptance is a decision reserved to the security authority / human on the dossier — never
inferred from the validator that found it (VAL-I09, VAL-I14). A green scanner is one observation,
not `security-validation` complete (VAL-I13).

## Evidence discipline

- Findings are OWASP/CWE-grounded, bound to the exact candidate (VAL-I01) and to an approved
  runtime observation (VAL-I04); agent-authored findings are draft until validated (VAL-I05).
- Severity thresholds and the blocking bar pre-exist the scan (VAL-I06) — a bar tuned so today's
  findings pass earns no credit.
- Environment and tool versions are bound (VAL-I07); a scan against a non-production target
  declares its deviations (VAL-I08).
- Rerun-until-clean cannot erase a prior finding (VAL-I16); every class names what it did not
  test (VAL-I15).

## Boundary

`security-validation` is G09 evidence only. It does not issue release readiness or go/no-go
(VAL-I18) and does not claim production security (VAL-I19). It composes into the conjunctive G09
dossier where a security blocker cannot be outvoted by passing performance and quality classes
(VAL-I14).
