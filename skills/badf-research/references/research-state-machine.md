# Research state machine

Status: frozen contract v0.2 (`BADF-WP-0031`, evolved by `WP-2026-0041`). States and dispositions are machine-readable in `schemas/research-record.schema.json`. Invalid concluded-state combinations fail closed in `badf_gate.py research`.

## States (`state`)

| State | Meaning |
| :--- | :--- |
| `PROPOSED` | a demand exists; framing is not complete |
| `FRAMED` | question, type, depth, scope, assumptions, decision context, hypotheses and stop conditions are explicit |
| `BASELINED` | applicable repository revision and observation time are fixed |
| `EVIDENCE_COLLECTING` | sources are being acquired and provenance/digests recorded |
| `EVIDENCE_ASSESSED` | material claims are classified, sourced and statused |
| `SYNTHESIZED` | findings, alternatives, contradictions and non-coverage are reconciled into a bounded synthesis |
| `CHALLENGED` | required independent challenge has been recorded |
| `RECONCILED` | a controlled disposition is set; the run is closed |

```text
PROPOSED
  → FRAMED
  → BASELINED
  → EVIDENCE_COLLECTING
  → EVIDENCE_ASSESSED
  → SYNTHESIZED
  → (CHALLENGED when required)
  → RECONCILED
```

`CHALLENGED` is mandatory when challenge is required by depth (`D4`/`D5`), type (`R06`) or the framework council policy. Otherwise `SYNTHESIZED` may proceed directly to `RECONCILED`.

A declared stop condition limits collection; it does not skip assessment, challenge or reconciliation.

## Dispositions (`disposition.state`)

A research disposition never returns a delivery PASS/FAIL. It answers whether the bounded research question is sufficiently resolved for the next governed process.

| Disposition | Meaning |
| :--- | :--- |
| `RESEARCH_SUFFICIENT` | enough bounded evidence exists to support a governed downstream decision |
| `MORE_RESEARCH_REQUIRED` | named evidence gaps require another bounded collection loop |
| `EXPERIMENT_REQUIRED` | existing evidence cannot distinguish alternatives but a controlled experiment can |
| `PROTOTYPE_REQUIRED` | only a separately bounded prototype can answer the question |
| `CONTRADICTORY_EVIDENCE` | material sources disagree and the disagreement remains unresolved |
| `SOURCE_INSUFFICIENT` | required primary or authoritative evidence could not be reached |
| `EXTERNAL_AUTHORITY_REQUIRED` | an external or reserved authority is needed before the question can resolve |
| `NO_ACTION_RECOMMENDED` | the question is answered and the evidence supports no downstream action |
| `RESEARCH_BLOCKED` | the run cannot proceed within its declared authority, source, data or tool boundary |

Re-entry from `MORE_RESEARCH_REQUIRED` returns to `EVIDENCE_COLLECTING` with named gaps and the same or explicitly amended framing. A reframed question should become a new research run rather than rewriting the meaning of a closed record.

`RESEARCH_SUFFICIENT` is decision-eligible only. It authorizes nothing; see `routing-authority.md`.
