# Findings and disposition — normalize without laundering the blockers (VAL-I14)

The four validation classes produce findings and results that normalize into the four G09 evidence types
the lifecycle already names — `quality-validation · security-validation · performance-test ·
resilience-test`. Normalization arranges evidence; it may **never erase, downgrade or silently accept** a
blocking finding (VAL-I14). The G09 dossier is **conjunctive**: it is not a vote.

## INFO vs blocking

Every finding carries a severity that determines whether it can refuse PASS:

```text
INFO / OBSERVATION   recorded, does not by itself refuse PASS
                     (a hardening note, a non-material latency, a low-severity lint)

BLOCKING             refuses PASS for its class until resolved
                     (an exploited auth bypass, an SLO breach, a failed recovery,
                      a broken payment oracle)
```

A finding's severity is set against the class threshold (see `thresholds-and-oracles.md`), not by
agent sentiment. An agent-proposed severity is DRAFT (VAL-I05) until the oracle and threshold fix it.

## No majority vote — the dossier is conjunctive

```text
G09 dossier  =  quality PASS  AND  security PASS  AND  performance PASS  AND  resilience PASS
                AND blocking_findings_resolved  AND runtime_evidence_valid
                AND noncoverage_declared
```

A **security blocker cannot be outvoted** by passing performance + quality + resilience (VAL-I14).
"3 of 4 passed → majority PASS" is exactly the laundering this contract forbids. One unresolved blocking
finding in any required class refuses the dossier's PASS.

## A blocker survives into any conditional disposition

Normalization cannot make a blocker disappear by aggregation. If a disposition is anything other than a
clean PASS, every unresolved blocking finding is **carried as an explicit condition** on that disposition —
visible to `quality_authority`, never absorbed:

```yaml
disposition: CONDITIONAL          # or PASS | FAIL
conditions:
  - finding: SEC-blocker-authz-bypass
    class: security-validation
    status: UNRESOLVED
    carried_because: "blocking finding cannot be downgraded by normalization (VAL-I14)"
```

Only `quality_authority` may accept a residual risk — the validator reports it, never accepts it (a
security validator waiving its own finding is forbidden, VAL-I09). Disposition is not release authority:
G09 ≠ G10 (VAL-I18).

## Flake policy is explicit — rerun-until-green is laundering (VAL-I16)

A failed observation is a fact. Re-running until a green appears does **not** erase it:

```text
run 1  FAIL     ← this observation happened and is preserved
run 2  PASS
run 3  PASS
```

The result is not "PASS (best of 3)". A flaky observation is **disclosed**, not laundered: the failure is
recorded, the flake is characterized (rate, suspected cause), and the flake policy that governs
acceptability is pre-declared, not decided after the fact. An undisclosed rerun that overwrites a failure
is a normalization defect.

## What disposition is not

Disposition is not a go/no-go. The conjunctive dossier is G09 evidence handed to `quality_authority`; a
G09 PASS opens G10 release readiness, it does not grant it (VAL-I18), and it never claims production
success (VAL-I19). Normalization's only job is to preserve every material finding faithfully into the four
existing evidence types — no fifth verdict, no second gate (VAL-I20).
