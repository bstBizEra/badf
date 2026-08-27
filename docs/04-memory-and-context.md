# Memory, Context, and Knowledge

Status: **NORMATIVE**

## Memory tiers

| Tier | Content | Lifetime | Authority |
| --- | --- | --- | --- |
| Working context | Current observations, hypotheses, scratch notes | Session | None |
| Session memory | Decisions, state, checks, next steps | Until reconciled | None |
| Project memory | Reviewed facts, conventions, known risks | Versioned and reviewed | Informational |
| Decision record | Ratified architectural or policy choice | Until superseded | As assigned |
| Evidence | Proof of an event or result | Retention policy | Supports claims, not authority |
| Institutional knowledge | Generalized validated pattern | Reviewed lifecycle | Informational unless incorporated into policy |

## Memory record requirements

Every durable memory item must include ID, statement, classification (`OBSERVED`, `INFERRED`, `DECIDED`, `SUPERSEDED`), source references, scope, owner, created/review dates, confidence, sensitivity, and supersession link when applicable. Use `schemas/memory.schema.json`.

## Promotion and retrieval

- Promote only facts supported by evidence or decisions supported by authority.
- Distinguish original observation from later interpretation.
- Retrieve by relevance, authority, freshness, and source quality; do not maximize volume.
- Revalidate memory before high-impact use.
- Record which memory influenced a material decision.
- Contradictory memory triggers reconciliation; do not silently pick one.

## Data hygiene

Minimize content, redact secrets and personal data, respect retention and residency, and enforce tenant/project boundaries. Embeddings and summaries inherit the sensitivity of their source.

## Forgetting and supersession

Do not rewrite historical records. Mark stale content `SUPERSEDED`, link the replacement, and remove it from default retrieval. Delete only under an approved retention/privacy process with deletion evidence.

