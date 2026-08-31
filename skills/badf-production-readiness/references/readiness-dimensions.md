# The twelve readiness dimensions — each resolved from its owning source

Every row names where the evidence actually comes from. This skill **resolves** each; it never
re-performs the owning discipline (PRDY-I01).

```text
Readiness dimension            Primary evidence source
-----------------------------  --------------------------------------------------
Product acceptance             G10 `badf-uat`                                       (PRDY-I07)
Engineering integrity          G08 `badf-engineering-verification`
Security                       G05 design + G09 validation                          (PRDY-I08/I09)
Performance/capacity           G09                                                  (PRDY-I10)
Resilience/recovery            G09                                                  (PRDY-I11)
Data/migration                 G04/G06/G09 + release migration evidence             (PRDY-I14)
Backup/restore                 operational/recovery evidence                        (PRDY-I12)
Rollback                       G06 release/rollback plan + executable proof         (PRDY-I13)
Observability                  architecture/operability + runtime configuration     (PRDY-I15)
Operations/on-call             service owner / runbooks / escalation                (PRDY-I16)
Support/change communication   product/service/release operations                   (PRDY-I17)
Artifact/release identity      Git/composition/build/attestation                    (PRDY-I18)
```

## The bounded readiness vocabulary

Each dimension resolves to exactly one of:

```text
READY                 mandatory evidence present, fresh, non-contradictory, bound to the exact candidate
READY_WITH_CONDITIONS ready subject to named conditions, each filed rather than left as prose
NOT_READY             mandatory evidence absent, failing, or contradicted
BLOCKED               a dependency prevents evaluation
INDETERMINATE         evidence present but cannot be reconciled (references/contradiction-resolution.md)
STALE                 evidence exists but has expired (references/evidence-freshness.md) — no credit
NOT_APPLICABLE        the dimension does not apply, with a stated reason — never a silent omission
```

`NOT_APPLICABLE` is a declaration, not a default. A dimension absent from the dossier is a defect;
a dimension marked `NOT_APPLICABLE` without a reason is the same defect wearing a label.

## The aggregate never hides a mandatory dimension

A dossier cannot report an overall posture that conceals a `NOT_READY`, `BLOCKED` or `STALE` mandatory
dimension. Every mandatory dimension's individual state is enumerated in the dossier, the same
discipline `badf-uat` holds for critical-tier scenarios (UAT-I13) and `badf-release-validation` holds
for its conjunctive G09 dossier.
