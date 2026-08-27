# BADF G02 RTM Contract

Status: **SKILL REFERENCE — proposed v0.1.0**

## Purpose

The Requirements Traceability Matrix is the canonical G02 artifact. It converts an approved PRD
baseline into testable obligations without collapsing product intent into implementation tasks.

## Node identities

| Prefix | Node | Purpose |
| --- | --- | --- |
| `OBJ-` | PRD objective | Approved upstream outcome |
| `CAP-` | Capability | Product/system ability required to satisfy an objective |
| `EPIC-` | Epic | Coherent delivery slice of a capability |
| `REQ-` | Requirement | Atomic functional, data, security, compliance or operability obligation |
| `NFR-` | Non-functional requirement | Quantified quality/constraint obligation |
| `AC-` | Acceptance criterion | Observable pass/fail condition |
| `TEST-` | Test obligation | Verification that must eventually be executed |
| `EVDREQ-` | Evidence requirement | Proof that must exist for the test claim |
| `SRC-` | Security/compliance source | Threat, compliance, privacy or abuse-case driver |

IDs are stable identities. Labels/statements may evolve only through a new RTM version with
supersession/provenance.

## Allowed edges

- `OBJECTIVE_TO_CAPABILITY`: `OBJ -> CAP`
- `CAPABILITY_TO_EPIC`: `CAP -> EPIC`
- `EPIC_TO_REQUIREMENT`: `EPIC -> REQ`
- `REQUIREMENT_TO_NFR`: `REQ -> NFR`
- `REQUIREMENT_TO_ACCEPTANCE`: `REQ -> AC`
- `NFR_TO_ACCEPTANCE`: `NFR -> AC`
- `ACCEPTANCE_TO_TEST`: `AC -> TEST`
- `TEST_TO_EVIDENCE`: `TEST -> EVDREQ`
- `SOURCE_TO_REQUIREMENT`: `SRC -> REQ`

No other edge is canonical at G02. Requirement-to-requirement sequencing belongs in
`dependencies`, not in traceability edges.

## Completeness invariants

A candidate is structurally eligible for G02 review only when:

1. upstream PRD baseline declares G01 approved/approved-with-conditions and carries approval evidence;
2. every PRD objective has at least one capability;
3. every capability has upstream objective coverage and at least one epic;
4. every epic has upstream capability coverage and at least one requirement;
5. every requirement has an epic parent, at least one quantified NFR, and at least one acceptance criterion;
6. every NFR has at least one requirement parent and at least one acceptance criterion;
7. every acceptance criterion has an upstream requirement/NFR and at least one test obligation;
8. every test obligation has at least one acceptance criterion and at least one evidence requirement;
9. every evidence requirement has at least one test parent;
10. security-sensitive, SECURITY and COMPLIANCE requirements trace to at least one security/compliance source;
11. every source marked `requires_requirement=true` drives at least one requirement;
12. all requirement dependencies resolve to known requirements, are non-self-referential and acyclic;
13. no unresolved decision, blocked dependency or open blocking review finding remains;
14. no placeholder token is present.

These invariants establish **eligibility for review**, not Gate G02 approval.

## NFR quantification

Each NFR carries:

`category + statement + metric + operator + target + unit + measurement_method`

The validator checks presence/type, not whether the selected threshold is commercially or
technically correct.

## Definition of Ready output

The validator computes a coverage summary instead of trusting a self-authored score. A complete
graph returns `ELIGIBLE_FOR_G02_REVIEW` with `authority=NO_GATE_AUTHORITY`.
