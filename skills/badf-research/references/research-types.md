# Research types

Status: frozen contract v0.2 (`BADF-WP-0031`, evolved by `WP-2026-0041`). The schema `schemas/research-record.schema.json` carries the same codes; drift tests hold this table to the schema.

A request may touch several research concerns but every record has ONE primary question and ONE primary type. Supporting fact verification (`R10`) may be used inside another type without becoming a second router.

| Code | Type | Question it answers | Default route |
| :--- | :--- | :--- | :--- |
| `R01` | `PROBLEM_DISCOVERY` | turn a demand into researchable questions | framing → synthesis |
| `R02` | `REPOSITORY_INVESTIGATION` | what is happening in this repository | framing → repository → fact-check |
| `R03` | `ROOT_CAUSE` | why a failure happened | framing → repository → hypothesis / experiment |
| `R04` | `TECHNICAL_SOLUTION` | what approaches could solve it | framing → technical → comparison |
| `R05` | `ARCHITECTURE` | boundaries, patterns, ADR options | framing → deep → technical → comparison |
| `R06` | `SECURITY` | threats, CVEs, attack paths | framing → repository / deep → adversarial |
| `R07` | `COMPARATIVE` | compare alternatives against declared criteria | framing → deep → comparison |
| `R08` | `EMPIRICAL_EXPERIMENT` | measure under controlled conditions | framing → experimental loop |
| `R09` | `STANDARDS` | what a standard or regulation requires | framing → authoritative sources |
| `R10` | `FACT_VERIFICATION` | whether a material claim is supported | fact-checking |

## Routing rules

- The root `SKILL.md` is the only router.
- Type answers *what kind of uncertainty is being reduced*; depth answers *how much evidence and challenge is required*. See `research-depth.md`.
- Overlapping triggers resolve to the most specific primary type.
- `R02` and `R03` repository work must bind a registered repository baseline to a resolvable revision when that repository is available.
- `R06` always requires independent challenge.
- Business, market and user research are not engineering research types in this v0.2 family; they require their own governed sibling contract rather than being silently forced into these codes.
