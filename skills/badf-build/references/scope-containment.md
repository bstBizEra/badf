# Scope containment — planned surface vs actual surface (BLD-I04)

G06 produces bounded Work Packages with `expected_surfaces`. The build compares, at reconcile time and
before any handoff:

```text
PLANNED SURFACE
vs
ACTUAL SURFACE
```

Example:

```text
Expected:
  src/auth/**
  tests/auth/**
  docs/auth.md

Actual:
  src/auth/login.py
  tests/auth/test_login.py
  scripts/release.py
```

```text
scripts/release.py  =  UNEXPECTED_SCOPE
```

The agent cannot say "it was necessary, so I changed it too". Instead:

```text
unexpected scope → classify → stop / amend / replan
```

unless the Work Package explicitly grants a **bounded discovery** allowance (declared paths or a
declared class of incidental change), in which case the discovery is recorded in `source-change` as such.

This is one of BADF's largest improvements over ordinary coding-agent workflows: the surface is a
contract checked at mutation time, not a diff summarized afterwards. `source-change` evidence carries the
expected-surface comparison and the unexpected-surface list (see `evidence-packaging.md`).
