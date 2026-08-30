# Verification matrix — an evidence map, not a pile of reports

The RTM maps requirements to work; the Solution Composition Matrix maps capabilities to components; the
Security Composition Matrix maps threats to controls. G08 needs the fourth: **what was claimed, what
changed, who challenged it, what was observed, and what that establishes.**

```text
Requirement / acceptance criterion
   ↓
Work Package
   ↓
Change (the G07 source-change binding: changed paths, change digest)
   ↓
Review finding(s)                       Reviewer plane
   ↓
Integration test · Contract test        Verifier plane
   ↓
Composed-tree test                      Verifier plane
   ↓
Result
```

## Rows

| Claim | Change | Review | Integration | Contract | Compose | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| AC-021 | CHG-14 | REV-7 (no open finding) | INT-31 PASS | API-18 CONFORMANT | CMP-9 PASS | **VERIFIED** |
| NFR-08 | CHG-15 | REV-8 (FIND-003 MAJOR open) | INT-32 PASS | — (NOT_APPLICABLE, declared) | CMP-9 PASS | **PARTIAL** |
| AC-030 | CHG-16 | — | — | — | CMP-9 PASS | **UNVERIFIED** |

## Result semantics

- **VERIFIED** — every applicable column carries a canonical artifact with `outcome: PASS` (or a resolved
  finding), bound to the same composed tree.
- **PARTIAL** — at least one applicable column is missing, `BLOCKED`, or carries an open non-blocking
  finding; the gaps are named.
- **UNVERIFIED** — the claim is bound to a change but no Reviewer-plane or Verifier-plane artifact
  addresses it.

A row is never VERIFIED by an artifact bound to a different `expected_content_tree` — the matrix is
recomputed when the composition is.

## What the matrix is for

`quality_authority` decides G08 on the matrix and the dossier, not on a narrative. An UNVERIFIED row is
either non-coverage with a reason and an owner, or a hold. The matrix is built at VER-B as a typed
artifact; at VER-A it is the declared shape.
