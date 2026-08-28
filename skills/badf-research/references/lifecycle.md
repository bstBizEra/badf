# Research lifecycle

Status: frozen contract v0.1. States and dispositions are machine-readable in the schema; a transition without its evidence fails closed (deterministic validation is a later work package; the meaning is frozen here).

## States (`state`)

| State | Meaning |
| :--- | :--- |
| `PROPOSED` | a demand exists; no question yet |
| `FRAMED` | question, scope, non-goals, hypotheses, stop conditions |
| `BASELINED` | repository revision and observation time fixed |
| `EVIDENCE_COLLECTING` | sources acquired and digest-bound |
| `EVIDENCE_ASSESSED` | claims classified and statused |
| `SYNTHESIZED` | findings, contradictions, non-coverage |
| `CHALLENGED` | independent challenge recorded, when required |
| `RECONCILED` | disposition set; the record is closed |

```text
PROPOSED → FRAMED → BASELINED → EVIDENCE_COLLECTING → EVIDENCE_ASSESSED → SYNTHESIZED → (CHALLENGED) → RECONCILED
```

`CHALLENGED` is mandatory when `challenge.required` is true (depth `D4`/`D5`, type `R06`, or the council disposition of the framework says so); otherwise the record moves from `SYNTHESIZED` to `RECONCILED`. Re-entry: `MORE_RESEARCH_REQUIRED` returns the record to `EVIDENCE_COLLECTING` with the gaps named.

## Dispositions (`disposition.state`)

A reconciliation never returns PASS/FAIL. It answers *do we know enough to support a governed decision?*

| Disposition | Meaning |
| :--- | :--- |
| `RESEARCH_SUFFICIENT` | enough to support a governed decision — decision-eligible, never implementation-authorised |
| `MORE_RESEARCH_REQUIRED` | named gaps; next loop |
| `EXPERIMENT_REQUIRED` | evidence cannot distinguish alternatives; a controlled experiment can |
| `PROTOTYPE_REQUIRED` | only a bounded build can answer |
| `CONTRADICTORY_EVIDENCE` | sources disagree materially; preserved, not averaged |
| `SOURCE_INSUFFICIENT` | no primary or authoritative source reached |
| `EXTERNAL_AUTHORITY_REQUIRED` | a human or external body must decide |
| `NO_ACTION_RECOMMENDED` | the question is answered: do nothing |
| `RESEARCH_BLOCKED` | cannot proceed; reason stated |

`RESEARCH_SUFFICIENT` makes a decision **eligible**; it authorises nothing (see `routing-and-authority.md`).
