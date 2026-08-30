# Non-coverage — the honest boundary is mandatory, per class (VAL-I15)

Every validation class must name the material surfaces and risks it did **not** establish (VAL-I15).
Silence is not coverage. A class that "states nothing unobserved" is not comprehensive — it is
**incomplete**, and the dossier holds it as such. Non-coverage is declared per class and carried into the
G09 dossier, where `quality_authority` decides whether each gap is acceptable.

## What every class must declare

Non-coverage is not one thing; it is the union of everything a class knew about and did not close:

- **Methods not run** — a planned scan, load class, chaos experiment or journey that was skipped.
- **Deferred obligations** — a required surface routed `DEFERRED_WITH_REASON` (VAL-I02).
- **Environment deviations** — every non-`MATCH` axis from the fidelity statement (VAL-I08), e.g.
  `staging PASS ≠ production proven`.
- **Mechanically-unobservable claims** — anything no available runtime could observe (VAL-I04), so it was
  neither passed nor failed.

## The per-class shape

Each class emits its own block; the dossier concatenates them:

```yaml
non_coverage:
  - class: performance-test
    surface: production data volume (~9M rows)
    reason: production dataset not provisioned in staging   # env deviation, VAL-I08
    impact: index/scan behavior at scale not established
    owner: quality_authority
  - class: security-validation
    surface: live payment provider fraud controls
    reason: provider reachable only in sandbox
    impact: real settlement + provider rate-limit behavior not established
    owner: quality_authority
  - class: resilience-test
    surface: multi-region failover
    reason: single-region topology in staging
    impact: cross-region recovery unobserved
    owner: quality_authority
```

## Empty is a claim

`non_coverage: []` for a class asserts that the class comprehensively established its entire declared
scope. That assertion is admissible only when it is actually true and the class contract permits it —
otherwise an empty declaration is held as incomplete. A validator that names nothing unestablished has
described a validation that did not happen.

## Not an escape hatch

Non-coverage is the honest boundary of what was proven — it is **not** a way to pass what was not proven.

```text
declared non-coverage of an OPTIONAL / N/A surface   →  legitimate boundary
declared "non-coverage" of a REQUIRED obligation     →  still a FAIL, not a pass
```

Declaring a gap does not resolve it and does not lower the gate. An unmet REQUIRED class (VAL-I02) cannot
be converted into a PASS by writing it into `non_coverage[]`; a blocking finding cannot be re-labelled as
"not covered" to dodge VAL-I14. Whether a declared gap is acceptable is a `quality_authority` decision
recorded on the dossier as a condition or an accepted risk — never inferred from the declaration's
existence, and never a grant of release authority (G09 ≠ G10, VAL-I18).
