# External methodology provenance

Status: **REFERENCE / ADAPT ONLY — no external executable vendored, no external skill granted authority.**

`badf-build` absorbs engineering discipline from two external sources and puts every mutation back inside
BADF's Governed Work Package, evidence, budget and authority envelope. The sources are references, not
BADF authority; vendoring or direct execution of either requires a separate external-skill admission WP
under `docs/07-skills-governance.md`.

## mattpocock/skills/implement

```text
ADAPT
  ✓ implementation from a bounded source contract   (BADF: the authorized Governed Work Package)
  ✓ TDD where appropriate
  ✓ focused tests during work
  ✓ typecheck/build continuously
  ✓ full verification at finish
  ✓ review after implementation

REJECT
  ✗ ticket as authority
  ✗ implicit permission to commit/push
  ✗ review as gate approval
```

## mattpocock/skills/tdd

```text
ADAPT
  ✓ behavioral tests
  ✓ durable public seams
  ✓ red before green
  ✓ vertical slices
  ✓ anti-tautology discipline

ADAPT, NOT FREEZE EXACTLY
  ~ exact placement of the refactor phase   (BADF: METHOD OPTION, see tdd-contract.md)
```

## obra/superpowers

```text
ADAPT
  ✓ isolated workspace
  ✓ fresh agent context
  ✓ per-unit implementation
  ✓ review loops
  ✓ recovery ledger
  ✓ verification before completion   ("NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE")
  ✓ explicit finish workflow          (BADF: routed through badf-git, see handoff-to-g08.md)

REJECT
  ✗ agent ruling as authority
  ✗ autonomous scope expansion
  ✗ branch finish as merge permission
  ✗ self-review as independent G08 assurance
```

## The divergence, stated once

Superpowers' subagent-driven development permits the executing agent to make "rulings" on ambiguity and
continue, treating the spec as binding authority. That is appropriate there. It is **not** BADF authority
doctrine: a build controller may make local engineering choices only within the already authorized Work
Package contract, and

```text
Superpowers ruling  ≠  BADF authority decision
```
