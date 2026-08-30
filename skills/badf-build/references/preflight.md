# CLAIM and PREFLIGHT — nothing mutates before authority is validated

## CLAIM — resolve exactly one Governed Work Package (BLD-I01)

```text
WP identity            demand                 G06 plan
source baselines       scope                  expected surfaces
change class           authority              budget
stop conditions        test obligations       evidence obligations
```

No valid Work Package:

```text
NO BUILD
```

A ticket, a chat instruction, a spec or a plan file is **not** a Work Package. The authorized Governed
Work Package (G06 PASS, authority valid) is the only thing a build may claim.

## PREFLIGHT — before any mutation (BLD-I03)

```text
WP status executable?
dependencies satisfied?
G06 baseline current?
authority current?
expected branch/base current?
permissions sufficient?
budget remaining?
required environment available?
stop contract loaded?
```

Any uncertainty that affects authority:

```text
STOP
```

not guess. Preflight resolves *facts* (is the base current, is the budget positive); it never resolves
*authority* (should this WP run at all). The second kind of question returns upstream.

## What CLAIM consumes from G06

The planning contract already carries what the build needs — `expected_surfaces`, `authority_requirement`,
`execution_budget`, `stop_conditions`, `test_obligations`, `evidence_obligations`, `composition` — as
optional Work Package fields (WP-IMP-B) enforced on the work-breakdown (WP-IMP-C). `badf-build` reads
them; it does not redefine them.
