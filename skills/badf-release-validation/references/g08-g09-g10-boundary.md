# g08-g09-g10-boundary.md — the lifecycle boundary this capability defends

`badf-release-validation` authors **G09 evidence and nothing else**. Its correctness
depends less on what it produces than on what it refuses to claim. This reference fixes the
three boundaries it defends: **G08 ≠ G09** (**VAL-I17**), **G09 ≠ G10** (**VAL-I18**), and
**G09 ≠ G12** (**VAL-I19**). The lifecycle already separates these gates; the capability
must not blur them.

## The gate chain

```text
G08  ENGINEERING VERIFICATION            independent-review · integration-test ·
       (owner quality_authority)          contract-test · composed-tree-test
        │  "is the engineered change internally coherent and correct?"
        ▼
G09  INDEPENDENT QUALITY & SECURITY      quality-validation · security-validation ·
       VALIDATION  [quality_authority]    performance-test · resilience-test
        │  "does the exact candidate withstand risk-based validation?"
        ▼
G10  UAT & RELEASE READINESS             uat · release-packet ·
       [release_authority]                operational-readiness · go-no-go
        │  "should this candidate progress to release?"
        ▼
G11  DEPLOYMENT & CHANGE CONTROL
        ▼
G12  PRODUCTION VERIFICATION             "did the deployed change succeed in production?"
```

`badf-release-validation` sits at **G09 only**. It reads the exact G08-verified candidate,
routes it through the four validation classes, and normalizes their observed results into
the four G09 evidence types the lifecycle already names. It never authors a G10 or G12
artifact.

## The three frozen boundaries

| Boundary | Invariant | What it forbids |
| :--- | :--- | :--- |
| **G08 ≠ G09** | **VAL-I17** | Engineering verification cannot substitute for independent risk-based validation. |
| **G09 ≠ G10** | **VAL-I18** | A G09 result cannot issue UAT, release-readiness, operational-readiness, or go/no-go. |
| **G09 ≠ G12** | **VAL-I19** | Pre-release testing cannot claim production success. |

### G08 ≠ G09 (VAL-I17)

A G08 review may find a real security defect in a diff (authorization bypass, injection,
unsafe deserialization) and report it as a canonical finding. That does **not** replace
penetration testing, threat-model-driven security validation, budget-backed performance
testing, or fault/recovery testing. Those are G09 evidence, produced under G09's stronger
independence and production-representative conditions. A G08 dossier carrying a
`security-validation` object is not "ahead" — it is out of scope. Where change class
requires G09, G08 approval **opens** G09; it does not satisfy it.

### G09 ≠ G10 (VAL-I18)

G09 is owned by `quality_authority`; G10 by `release_authority`. No quantity of passing G09
classes constitutes a release decision. `uat`, `release-packet`, `operational-readiness`,
and `go-no-go` are G10 evidence types, authored by G10 authority. A G09 dossier that reads
"all classes PASS" is exactly that — validation evidence — and carries no progression
verdict. G09 hands its conjunctive dossier to `quality_authority`; only after G09 PASS does
G10 own release readiness.

### G09 ≠ G12 (VAL-I19)

Staging, load, and chaos runs occur before deployment. A `staging PASS` is not a production
claim; environment deviations from production are declared non-coverage (**VAL-I08**), never
forgotten. `testing-in-production` and post-deploy verification belong to G12 — a separate
gate, run against the deployed system, not against a pre-release candidate.

## The canonical rule

```text
G08 security review   ≠  G09 security validation
G08 integration test  ≠  G09 performance / resilience test
G09 "all classes PASS" ≠  G10 go/no-go
G09 staging PASS      ≠  G12 production success
```

**The BADF gate validates evidence; authority decides progression.** Passing G09
establishes independent pre-release validation evidence — nothing more. There is no second
gate, no fifth evidence type, and no lifecycle change here (**VAL-I20**); G09 semantics stay
inside the canonical gate at a later delivery rung. See
[g09-contract.md](g09-contract.md) for the full G09 contract.
