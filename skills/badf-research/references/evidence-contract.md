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
| `VERIFIED` | ≥1 independent primary source and no open contradiction |
| `PARTIALLY_VERIFIED` | supported, but not independently |
| `DISPUTED` | supporting and contradicting sources both present |
| `UNVERIFIED` | no source reached |
| `FALSIFIED` | contradicted by an OBSERVED claim |

## Confidence (`claims[].confidence`)

Confidence is **derived** from `basis` — `independent_primary_sources`, `reproducible`, `contradictions` — by the table below. It is never self-reported, never a percentage, and it never enters authority or evidence semantics as an agent's own assessment (the mandate forbids "agent confidence" there by name).

| Level | Derived when |
| :--- | :--- |
| `VERY_LOW` | 0 independent primary sources, or contradictions ≥ supporting |
| `LOW` | 1 primary source, not reproducible |
| `MODERATE` | 1 primary source, reproducible, or 2 non-independent |
| `HIGH` | ≥2 independent primary sources, reproducible, no contradiction |
| `VERY_HIGH` | ≥2 independent primary sources, reproducible, contradictions examined and eliminated |

## Contradictions and non-coverage

`contradictions[]` are preserved with the claims they oppose; a majority does not erase one (RSR-I04). `non_coverage[]` names every surface not inspected, with a reason: silence is not coverage.

## Findings, alternatives, experiments

`findings[]` reference claims; `alternatives[]` reference evidence; `experiments[]` reference a hypothesis and state method and result. `evidence_digest` is the sha256 over the sources and claims and changes when material evidence changes.
