# Non-coverage — mandatory on every artifact, impossible to omit (VER-I11)

G08's exit criterion says "non-coverage declared". The gate already enforces it at **dossier** level
(`check_non_coverage`, BADF-WP-0014): an evidence type that is `NOT_RUN` or `NOT_APPLICABLE` must be named
in the dossier's `non_coverage[]` with a reason and an owner — an undeclared non-applicability is a missing
test, not a non-coverage.

This contract extends the same discipline to **every artifact**: a review, an integration run, a
contract observation, a composed-tree observation. Each carries:

```yaml
coverage:
  observed:
    - <surfaces, paths, scenarios actually inspected or executed>
  unobserved:
    - <surfaces known to exist and not inspected or executed>
non_coverage:
  - surface: browser Safari
    reason: environment unavailable
    impact: cross-browser behavior not established
    owner: quality_authority          # who decides whether the gap is acceptable
```

## Empty is a claim

`non_coverage: []` means "this artifact claims comprehensive coverage of its declared scope". That claim
is admissible only when the review or test contract explicitly permits it for that scope (a C1
documentation-only change reviewed in full, for example). Otherwise an empty declaration is held as
incomplete — a reviewer that states nothing uninspected has described an inspection that did not happen
(the architecture-assurance rule, control 17, applied to G08).

## What non-coverage prevents

```text
agent did not inspect something  →  forgotten
```

becomes

```text
agent did not inspect something  →  named, owned, decided
```

The security lens today is the canonical example: `badf-security-assurance` is named, not built, so every
G08 review declares it (`references/review-lenses.md`).

## Non-coverage is not a verdict

Declaring a gap does not resolve it and does not lower the gate. Whether a declared gap is acceptable is a
`quality_authority` decision recorded on the dossier as a condition or an accepted risk — never inferred
from the declaration's existence.
