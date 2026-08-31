# The two-layer artifact — recommendation vs. human acceptance

UAT-I09, UAT-I14, UAT-I15, UAT-I16. This is the load-bearing boundary of the whole skill: automation
establishes observation; a human authorized under current BADF policy establishes acceptance. The two
are recorded as genuinely separate layers, never merged into one field that could be mistaken for the
other.

## Layer 1 — the recommendation (this skill's output)

```json
{
  "candidate_digest": "...",
  "acceptance_basis_digest": "...",
  "scenario_results": ["... every scenario, every result ..."],
  "defects": ["... classified per references/defect-classification.md ..."],
  "coverage_matrix": "... per references/coverage-matrix.md ...",
  "recommendation": "RECOMMEND_ACCEPT | RECOMMEND_ACCEPT_WITH_CONDITIONS | RECOMMEND_REJECT | RECOMMEND_INSUFFICIENT_EVIDENCE",
  "recommendation_rationale": "..."
}
```

`recommendation` is evidence, not a decision — the same rule the decision-packet pattern applies
elsewhere in BADF governance: an agent's recommended option is an input, never the act itself.

## Layer 2 — human acceptance (issued separately, by the authorized principal)

```json
{
  "acceptance_id": "...",
  "candidate_digest": "... must equal Layer 1's ...",
  "acceptance_basis_digest": "... must equal Layer 1's ...",
  "scenario_set_digest": "... must equal Layer 1's ...",
  "disposition": "ACCEPTED | ACCEPTED_WITH_CONDITIONS | REJECTED",
  "conditions": ["... if ACCEPTED_WITH_CONDITIONS, each one is a real filed condition, not prose ..."],
  "known_defects_acknowledged": ["..."],
  "declared_non_coverage_acknowledged": ["..."],
  "accepted_by": "authorized human principal identity",
  "accepted_at": "timestamp"
}
```

## Why this skill cannot issue Layer 2 (UAT-I14, UAT-I15)

The same "the capability that produces evidence must never be the same capability that decides"
principle that reserves G08 admission and security approval to a human/quorum outside the producing
skill applies here: `badf-uat` computed the observations, so `badf-uat` cannot also be the acceptance
authority — that would let the evidence-producer grade its own evidence. Layer 2 is issued by the human
product/business principal reserved for this decision under current BADF policy, outside this skill's
own execution.

## Binding (UAT-I16)

Layer 2 binds Layer 1's exact digests. An acceptance record whose `candidate_digest` or
`acceptance_basis_digest` does not match its own Layer 1 evidence is void — see
`references/reuat-and-staleness.md`.
