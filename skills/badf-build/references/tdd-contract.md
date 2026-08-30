# Governed TDD — required where a durable seam exists, explicit where it does not

BADF does **not** define ~~EVERY CHANGE MUST USE TDD~~. That produces bad tests for change types that have
no meaningful behavioral seam. The doctrine is:

```text
NO UNVERIFIED MUTATION
```

not merely "no code without a unit test".

```text
TDD_REQUIRED
    when a durable observable behavior seam exists.

TDD_NOT_APPLICABLE_WITH_REASON
    when the change is not meaningfully behavior-testable through a stable seam —
    and an alternate verification obligation is declared (BLD-I08).
```

## By change type

| Change | Expected |
| :--- | :--- |
| business behavior | TDD required |
| API behavior | contract/TDD required |
| bug fix | reproducing failing test required where possible |
| parser/validator | TDD strongly required |
| schema validation | failing-first fixture |
| migration | migration forward/backward test |
| IaC | policy/plan validation |
| documentation-only | structural/link/lint checks |
| generated artifact | generator/source verification |
| mechanical refactor | behavioral regression evidence |

## Red before green (BLD-I07)

When TDD applies, the test-required behavioral change carries **observed failing evidence** before the
implementation that makes it pass — recorded, not remembered. The seam is established before the test
is written; one vertical slice at a time; tests exercise behavior through public interfaces, never
internals; tautological tests and bulk speculative tests are refused.

## Refactor placement — METHOD OPTION

`RED → GREEN → optional bounded REFACTOR → GREEN AGAIN`, on condition that the refactor neither expands
scope nor alters acceptance semantics. The exact placement of the refactor phase is a method option
adapted from the source methodology, not a BADF invariant.
