# ASSURE shadow calibration (`BADF-WP-0059`, Issue #108)

Before `APPROVED`/`ACTIVE`, the ASSURE substrate is run retrospectively on **real BADF architecture
cases**, spanning the outcome space, and measured — would it detect the real violation, refuse to
manufacture compliance, and handle the undecidable case without a false pass?

Three gate-valid `architecture-assurance` records:

| Record | Conclusion | Real case | What the contract had to do | Result |
| :--- | :--- | :--- | :--- | :--- |
| `…-stdlib-compliant.json` | `COMPLIANT` | the stdlib-only boundary (ADR-0001) holds at `bc9eb30` | bind a baseline + observed revision, ADR `CONFORMANT`, no drift | Faithful — COMPLIANT rests on a bound baseline digest (control 14). |
| `…-pyyaml-drift.json` | `NONCOMPLIANT` | the #57 PyYAML import broke the stdlib boundary at `59c5293` | detect a real `DEPENDENCY_DRIFT`, classify `UNAUTHORIZED_DRIFT` (not approved), ADR `NONCONFORMANT`, MAJOR finding | **True violation detected.** The drift is not self-approved (control 16); the finding carries expected/observed/failure-scenario/evidence. |
| `…-indeterminate.json` | `INDETERMINATE` | ADR-0001 compliance is not statically observable for a dynamic import path at `2e46fe7` | refuse to guess COMPLIANT; conclusion `INDETERMINATE`, ADR `INDETERMINATE`, non-coverage declared | **No false pass.** `INDETERMINATE` did not serialise as a pass (control 15); `NO BASELINE ≠ COMPLIANT` / *don't validate the implementation against itself* held (ARCH-I07). |

## Measurement

| Metric | Result |
| :--- | :--- |
| true violations detected | 1/1 (the PyYAML drift) |
| false positives | 0 (the COMPLIANT case is genuinely conformant) |
| INDETERMINATE handled without a false pass | yes (control 15) |
| drift self-approved | none (control 16 forbids it) |
| non-coverage declared | every run (control 17) |
| single-baseline discipline | every finding bound to the one baseline (control 18) |
| read-only | `implementation_authority` fixed `false` in every record (ARCH-I12) |

**No contract gap surfaced under real conditions.** This is the `SHADOWED` evidence; `badf-architecture`
advances `VALIDATED → SHADOWED`. `APPROVED`/`ACTIVE` remain the operator's admission decision, now
backed by calibration data rather than one synthetic example.
