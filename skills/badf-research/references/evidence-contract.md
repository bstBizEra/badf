# Research evidence contract

Status: frozen contract v0.1. One record per research run at `work/research/<BADF-RSR-NNNN>/research-record.json`, under the lockfile like every governance artefact. Ids are sequential and never encode the Issue number; `source.issue` carries it. Every run has a demand record (`demand`).

## Sources (`sources[]`)

Every source carries `uri`, `source_type`, `retrieved_at` and, when the bytes are retrievable, a `digest`. A changed digest makes dependent claims stale. Prestige never turns a claim into VERIFIED; independence does.

| Source type | Meaning |
| :--- | :--- |
| `PRIMARY` | the thing itself: a commit, a run log, a spec, a measurement |
| `AUTHORITATIVE_SECONDARY` | maintainer or standards-body documentation |
| `SECONDARY` | reputable reporting of a primary source |
| `COMMUNITY` | forum, issue comment, blog |
| `UNVERIFIED` | provenance unknown |

## Claims (`claims[]`)

Every material statement is a claim with a classification, supporting and contradicting sources, a status and a derived confidence. The five classifications stay semantically distinct (RSR-I03).

| Classification | Meaning |
| :--- | :--- |
| `OBSERVED` | measured by the researcher, reproducibly |
| `REPORTED` | stated by a source |
| `INFERRED` | derived from observed or reported claims |
| `HYPOTHESIS` | proposed, not yet tested |
| `DECIDED` | a recorded decision, not evidence |

| Status | Meaning |
| :--- | :--- |
| `VERIFIED` | ≥1 independent primary source, no open contradiction, and a declared `semantic_support` (RSR-I06, control 27) |
| `PARTIALLY_VERIFIED` | supported, but not independently |
| `DISPUTED` | supporting and contradicting sources both present |
| `UNVERIFIED` | no source reached |
| `FALSIFIED` | contradicted by an OBSERVED claim |

## Confidence (`claims[].confidence`)

Confidence is **derived** from `basis` — `independent_primary_sources` (`ips`), `reproducible`, `contradictions` — by the table below, which is a pure function of those three fields (`badf_gate.py research` recomputes it and refuses a mismatch, like the two-plane verdict). It is never self-reported, never a percentage, and it never enters authority or evidence semantics as an agent's own assessment (the mandate forbids "agent confidence" there by name).

| Level | Derived when |
| :--- | :--- |
| `VERY_LOW` | 0 independent primary sources |
| `LOW` | 1 independent primary source, not reproducible |
| `MODERATE` | 1 independent primary source reproducible, or ≥2 not reproducible |
| `HIGH` | ≥2 independent primary sources, reproducible, with an unresolved contradiction |
| `VERY_HIGH` | ≥2 independent primary sources, reproducible, no contradiction |

## Semantic support (RSR-I06)

`SOURCE_EXISTS != SOURCE_SUPPORTS_CLAIM`. The gate verifies four evidence states deterministically, and stops there:

| State | Verified by |
| :--- | :--- |
| `SOURCE_EXISTS` | schema + a unique `S-` id |
| `SOURCE_BOUND` | the source id resolves in `supporting_sources`/`contradicting_sources` (referential integrity) |
| `SOURCE_CURRENT` | `freshness == CURRENT` — a STALE/UNKNOWN source cannot support a claim (control 6) |
| `SOURCE_SUPPORTS_CLAIM` | **not machine-checkable** — an evidence-assessment judgment, never a policy assertion |

Whether a source's natural-language content entails a claim is `fact-checking`'s judgment, not the policy engine's. A `VERIFIED` claim on cited support declares `semantic_support`:

- `ASSESSED` — the record carries a `support_assessments` receipt for **each** supporting source: `{claim_ref, source_ref, relation, assessment, assessor, method, locator}`. The `locator` (a `LINE_RANGE`/`BYTE_RANGE`/`ANCHOR`/`QUOTE` into the digest-bound source) is where fact-checking looked; it must be non-empty. A receipt whose own `assessment` is `NOT_SUBSTANTIATED` (or whose `relation` does not support) cannot back a `VERIFIED` binding — the record may not represent a source as supporting a claim its own reading refutes.
- `NON_COVERAGE` — the honest fallback: entailment was **not** machine-verified. Silence (neither) is refused (control 27).

`semantic_support` and `support_assessments` are a *reading* of the evidence, not the evidence itself, so they are excluded from `evidence_digest` — recording an assessment does not invalidate the digest, exactly like findings and disposition. RSR-I06 grants no implementation authority (RSR-I01 unchanged).

## Contradictions and non-coverage

`contradictions[]` are preserved with the claims they oppose; a majority does not erase one (RSR-I04). `non_coverage[]` names every surface not inspected, with a reason: silence is not coverage.

## Findings, alternatives, experiments

`findings[]` reference claims; `alternatives[]` reference evidence; `experiments[]` reference a hypothesis and state method and result. `evidence_digest` is the sha256 over the record's material evidence -- its sources, claims, contradictions and experiments -- in canonical JSON; it is computed by the gate, not asserted, and changes when the evidence changes but not when its reading (findings, recommendation, disposition) does (`badf_gate.py research` refuses a mismatch).
