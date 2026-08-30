# Finding contract — the item BADF already has, extended; synthesis without loss

BADF already carries a machine-checked finding shape: the `findings[]` item of
`schemas/architecture-assurance.schema.json`. A G08 finding **reuses it** and adds the fields verification
needs. A second finding vocabulary is the defect this reference exists to prevent.

## The canonical finding

```yaml
finding_id: FIND-<WP>-<n>
kind: [regression]                 # regression · defect · security · contract · data · operability · convention · prompt-injection · …
severity: BLOCKING                 # BLOCKING · MAJOR · MINOR · INFO
baseline_ref: <expected behavior source: requirement, contract, ADR, test-plan obligation>
observed_ref: <candidate source_revision / expected_content_tree>
affected_elements: [payments.retry]
evidence_locations: ["src/payments.py:117-125"]
expected: <what the baseline requires>
observed: <what the change does, or is inferred to do>
impact: <who/what breaks, and how far>
failure_scenario: <concrete inputs/state → wrong output/crash>
recommendation_direction: <direction only — never a patch under the verifier's identity (VER-I17)>
status: OPEN                       # OPEN · RESOLVED · ACCEPTED_BY_AUTHORITY · WITHDRAWN
non_coverage: []                   # what this finding's author could not confirm

# added for verification
lens: correctness
target:
  source_revision: <sha>
  expected_content_tree: <tree>
reported_by: [REV-…-correctness-run1]
also_reported_by: [REV-…-quality-run3]
requirement_refs: [REQ-021]
architecture_refs: []
security_refs: []
evidence_refs: []                  # observed artifacts that demonstrate it, when the Verifier plane reproduced it
```

`observed` may be an inference at the Reviewer plane; it becomes an observation only when
`evidence_refs` names a runtime-observed artifact. The distinction is kept, not blurred.

## Synthesis — MAY and MUST NOT (VER-I12)

```text
SYNTHESIS MAY:
  deduplicate     merge findings that name the same defect at the same location; keep every reporter in also_reported_by
  group           cluster findings by element or root cause
  rank            order by severity, then by blast radius

SYNTHESIS MUST NOT:
  lower severity silently      a downgrade is a decision by quality_authority, recorded with a reason
  erase                        a minority finding survives synthesis; docs/03 step 6
  convert unknown to pass      INDETERMINATE, INSUFFICIENT_EVIDENCE and non-coverage are not resolved by omission
  accept risk                  residual risk is accepted by the authority that owns it, never by the synthesizer
```

`status: ACCEPTED_BY_AUTHORITY` is written only with the accepting role and the decision reference; a
finding without that reference that disappears between a ballot and the dossier is a refusal at VER-C.

## Speculative noise is not a finding (VER-I03)

A finding without `failure_scenario` and `evidence_locations` is a note. Notes may be recorded in the
review artifact for the author's benefit; they cannot carry `severity: BLOCKING` and cannot hold a gate.
