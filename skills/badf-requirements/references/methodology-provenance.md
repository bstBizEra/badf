# External methodology provenance

Status: **REFERENCE / ADAPT ONLY — no external executable vendored.**

Adapted from the requirements-engineering methodology surveyed in the superseded PR #47, salvaged
here as the authoring layer while #47's obsolete gate implementation (a standalone validator and a
custom RTM schema) was discarded. These are methodology references only: they grant no tool access, no
execution permission, no gate authority, and no runtime dependency.

## GitHub Spec Kit — `github/spec-kit`

Sequencing ideas BADF adapts: define/specify before implementation; separate clarification from
specification; use checklists to test requirement quality; run cross-artifact consistency/coverage
analysis before implementation. BADF does **not** delegate its RTM contract, evidence model, lifecycle
gate, or authority decisions to Spec Kit.

## softaworks requirements-clarity — `softaworks/agent-toolkit`

Clarification lenses BADF adapts: functional scope and boundaries; interaction and success/failure
scenarios; technical constraints; business value and success metrics; acceptance criteria and
ambiguity; systematic clarification rather than assumption. BADF does **not** adopt its numeric clarity
score as gate evidence — G02 readiness is the gate's bidirectional RTM plus explicit judgment findings.

## wshobson security-requirement-extraction — `wshobson/agents`

Security concepts BADF adapts: threat/business context → an actionable, specific, testable security
requirement; requirements carry threat/compliance traceability; acceptance criteria and security test
cases are part of the requirement chain. BADF adds the deterministic discipline of **REQ-I06**: a
security/privacy/compliance requirement retains its originating provenance.

## Admission posture

Any future vendoring or direct execution of these sources requires a separate external-skill admission
work package under `docs/07-skills-governance.md`. This skill adapts sequencing and lenses only.
