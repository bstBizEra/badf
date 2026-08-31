# Readiness ≠ authorization — and PRODUCTION_AUTHORIZED is derived, never written

PRDY-I19, PRDY-I20, PRDY-I21, PRDY-I22. This is the reference the whole capability is built to protect.

## The ceiling (PRDY-I19)

```text
This skill's strongest positive conclusion:   READY_FOR_AUTHORITY
This skill can never emit:                    PRODUCTION_AUTHORIZED
                                              PRODUCTION_AUTHORIZED_WITH_CONDITIONS
                                              PRODUCTION_NOT_AUTHORIZED
```

Those three are `release_authority`'s **derived predicates**. They appear in this reference only as a
description of what the authority derives — never as an output vocabulary this skill can select from.
`release_authority` is human-reserved in `badf/authority-matrix.json`; nothing in this ladder, at any
rung including `ACTIVE`, grants it.

## Why "derived, never written"

`PRODUCTION_AUTHORIZED` is not a field someone sets to `true`. It is a predicate over two independent
things:

```text
PRODUCTION_AUTHORIZED  ⟺  valid evidence            (this skill's dossier: READY_FOR_AUTHORITY)
                       ∧  valid authority           (release_authority, human, unexpired)
                       ∧  bound to exact candidate, environment, rollout scope,
                          conditions and validity window   (PRDY-I20)
```

A hand-written boolean can be `true` while any conjunct is false, and nothing downstream can tell. That
is the same class of defect as a `confirmation: bool` supplied by the caller it is meant to constrain —
a control-shaped field that carries no control. The derivation is what makes the claim checkable.

## Authorization exactness (PRDY-I20)

An authorization binds **exact candidate, environment, rollout scope, conditions and validity window**.
An authorization for "the release" is unbounded in all five and authorizes more than anyone decided:
a different artifact, a different environment, a wider rollout, a later date, conditions unmet.

## The two gate separations downstream

```text
PRDY-I21  G10 authorization ≠ G11 deployment.
          Being authorized to deploy is not having passed deployment/change control.
PRDY-I22  G11 deployment ≠ G12 production success.
          A deployment that completed is not a release that works in production.
```

## Precedent, not novelty

This boundary is the same shape BADF already holds in three places, and it is cited rather than
re-invented: **SEC-I13** (`badf-security-design` cannot issue its own security approval), **VER-I18**
(`badf-engineering-verification` cannot admit itself), **UAT-I14/I15** (`badf-uat` recommends;
a human accepts), and `badf-release-validation`'s own G09/G10 line. The generalization across all four:
**the capability that produces the evidence for a decision is never the capability that makes it.**
