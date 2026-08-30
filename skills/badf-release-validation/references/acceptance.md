# acceptance.md — admission ladder for badf-release-validation

The skill's status is recorded in `badf/skill-registry.json`; **that registry is the single
source of truth.** This ladder is a pointer, not a second status — read the registry for the
current rung rather than trusting any status written here.

## The DESIGNED rung — WP-VAL-A contract freeze

This work package freezes the **contract only**. It ships doctrine, invariants, and a
contract test — no runtime, no gate change. Acceptance for the `DESIGNED` rung:

- **Registry** — `badf-release-validation` present in `badf/skill-registry.json` with
  `status = DESIGNED` and `digest = sha256(SKILL.md)`.
- **No runtime surface** — no `scripts/badf_release_validation.py`, no new schema, no
  `lifecycle.json` change, no `badf_gate.py` change. The four G09 evidence types the
  lifecycle already names are **composed, not replaced**; no fifth `release-validation` type
  is added (**VAL-I20**).
- **Contract test** — a test asserts the frozen model holds:
  - all twenty invariants **VAL-I01…VAL-I20** are stated;
  - the router workflow (`FRAME → BIND_CANDIDATE → ROUTE → CLASS_VALIDATE → OBSERVE →
    THRESHOLD → NORMALIZE → DECLARE_NONCOVERAGE → COMPOSE → HANDOFF`) is present;
  - the capability **composes the existing quartet** (`quality-validation` ·
    `security-validation` · `performance-test` · `resilience-test`) and adds **no fifth
    type**;
  - external sources are **adapt-not-authority**, never imported as decision authority;
  - the **G08/G09/G10/G12 boundaries** (**VAL-I17/I18/I19**) are fixed.
- **Hygiene** — repo clean (no stray artifacts), CI green.

`owner_role = quality_authority`, `allowed_tools = []`. The DESIGNED freeze grants no
execution surface and no authority.

## The delivery ladder

Each rung is a distinct work package; a rung earns its status only on its own evidence, and
the registry records the flip.

| WP | Rung | Delivers |
| :--- | :--- | :--- |
| **WP-VAL-A** | `DESIGNED` | This contract freeze — doctrine, VAL-I01…I20, router workflow, references, registered with no tools. No runtime, no schema, no lifecycle change. |
| **WP-VAL-B** | `IMPLEMENTED` | Typed G09 evidence contracts for the four existing types, specializing the canonical evidence schema. Extends the canonical gate; adds no second one. |
| **WP-VAL-C** | `VALIDATED` | Canonical deterministic controls in the gate — candidate identity, required-class routing, class independence, threshold binding, runtime-observation credit, environment fidelity, blocker preservation, non-coverage completeness. Each failing-first and mutation-killed. Lean mode disabled: HARD INVARIANTS. |
| **WP-VAL-D** | `SHADOWED` | Representative / historical validation shadow (see corpus below); measures true findings, false positives, missed defects, drift, and non-coverage quality. Gaps declared, not implied. |
| **WP-VAL-E** | `ACTIVE` | `quality_authority` / operator admission decision, recorded on its own issue. Registry status flip only, digest unchanged — **grants no new authority.** The human and `quality_authority` gates hold. |

## WP-VAL-D shadow corpus — discriminating power by construction

A shadow that only ever sees healthy candidates proves nothing. The WP-VAL-D corpus must
**deliberately contain known failure classes**, so the controls are measured on their
ability to catch what they exist to catch:

```text
functional regression        authorization defect        SLO regression
recovery failure             flaky test                   stale candidate
wrong environment            mixed-candidate evidence      attempted risk waiver
```

Each maps to the invariant it exercises — e.g. stale candidate / mixed-candidate evidence →
**VAL-I01**; wrong environment → **VAL-I07/I08**; flaky test → **VAL-I16**; attempted risk
waiver → **VAL-I09/I14**; SLO regression → **VAL-I10**; recovery failure → **VAL-I11/I12**.
A control that cannot distinguish these from a clean candidate has not earned `VALIDATED`.

## Standing constraint

No rung — including `ACTIVE` — grants release, deployment, or production authority. The
capability produces G09 evidence and stops; `quality_authority` decides G09 PASS, and only
then does G10 own release readiness (**VAL-I18/I19**). Consult
[g08-g09-g10-boundary.md](g08-g09-g10-boundary.md) and [g09-contract.md](g09-contract.md).
