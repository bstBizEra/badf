# Research types and depths

Status: frozen contract v0.1 (`BADF-WP-0031`, #50). The schema `schemas/research-record.schema.json` carries the same codes; a drift test holds this file to it.

## Types (`type`)

A request may touch several types but has ONE primary question and one primary type.

| Code | Type | Question it answers | Default route |
| :--- | :--- | :--- | :--- |
| `R01` | `PROBLEM_DISCOVERY` | turn a demand into researchable questions | framing → synthesis |
| `R02` | `REPOSITORY_INVESTIGATION` | what is happening in this repository | framing → repository → fact-check |
| `R03` | `ROOT_CAUSE` | why a failure happened | framing → repository → hypothesis / experiment |
| `R04` | `TECHNICAL_SOLUTION` | what approaches could solve it | framing → technical → comparison |
| `R05` | `ARCHITECTURE` | boundaries, patterns, ADR options | framing → deep → technical → comparison |
| `R06` | `SECURITY` | threats, CVEs, attack paths | framing → repository / deep → adversarial (challenge required) |
| `R07` | `COMPARATIVE` | decide between alternatives | framing → deep → comparison |
| `R08` | `EMPIRICAL_EXPERIMENT` | measure under control | framing → experimental loop (D5) |
| `R09` | `STANDARDS` | what a standard or regulation requires | framing → authoritative sources |
| `R10` | `FACT_VERIFICATION` | is a claim true | fact-checking |

## Depths (`depth`)

Type is *what*; depth is *how much*. Depth is the cost control: it is set at framing and cannot be raised silently. `D4` and `D5` require independent challenge.

| Code | Depth | Typical use |
| :--- | :--- | :--- |
| `D0` | `LOOKUP` | one factual answer |
| `D1` | `SCAN` | quick engineering investigation |
| `D2` | `STANDARD` | multiple sources and comparison |
| `D3` | `DEEP` | parallel research and triangulation |
| `D4` | `ADVERSARIAL` | deep plus independent challenge (challenge required) |
| `D5` | `EXPERIMENTAL` | research plus controlled experiments (challenge required) |

## Routing rules

- The router is the root `SKILL.md`; it selects subskills by type and depth. There is no second router.
- Overlapping triggers resolve to the more specific type; `R10` (fact verification) is always available as a supporting step.
- Business, market and user research are NOT engineering research types; they are a sibling family, later.
