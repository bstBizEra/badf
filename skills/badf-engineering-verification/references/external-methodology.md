# External methodology provenance

Status: **REFERENCE / ADAPT ONLY — no external executable vendored, no external tool granted authority.**

`badf-engineering-verification` adapts three external sources and puts every verification artifact back
inside BADF's Work Package, evidence, identity and authority envelope. The sources are references, not
BADF authority; vendoring or executing any of them requires a separate external-skill admission WP under
`docs/07-skills-governance.md`.

**Provenance note.** The three sources are characterized here as described in the operator's design
directive of 2026-08-30 (GOV-0083 / #195). They were **not independently fetched** for this freeze; that is
declared as non-coverage of this reference, and a later rung that vendors or pins any of them binds the
source digest at that time.

## OpenAI Codex `review-agent`

```text
ADAPT
  ✓ read-only reviewer — no file modification, commit, push, comment or delegation
  ✓ defect-first — actual introduced regressions, actionable findings, not speculative noise
  ✓ inspect the full diff plus surrounding code, tests and call sites
  ✓ review the change that would actually merge — establish the correct merge base

EXTEND
  + bind the exact candidate AND the exact composed content tree (target-binding.md)
  + BADF provenance and sealed-input digest
  + non-coverage schema on every review
  + execution-level reviewer independence

REJECT
  ✗ AI review verdict as approval
```

## Apache Magpie multi-agent review

```text
ADAPT
  ✓ isolated review axes — correctness / security / conventions run without seeing each other's findings
  ✓ independent parallel passes
  ✓ structured finding output, deduplicated afterwards
  ✓ text embedded in diffs and comments treated as data; attempts to direct the reviewer flagged as prompt injection
  ✓ read-only

EXTEND
  + docs/03 council ballots persisted before synthesis; sealed-input digest
  + mandatory minority-risk preservation (synthesis MUST NOT erase)
  + change-class-driven lens routing (a C1 change is not reviewed by seven agents)
  + the security axis routed to badf-security-assurance, declared non-coverage until it exists
```

## `qa-tester`

```text
ADAPT
  ✓ agent drafts ≠ canonical artifacts — drafts become canonical only after validation and registration
  ✓ deterministic runtime that never calls a model
  ✓ versioned contracts, immutable registration, checksums and provenance
  ✓ runtime-observed execution; safety-bounded environments

DO NOT COPY WHOLESALE
  ✗ its release gate as BADF authority
  ✗ Playwright-centric QA as universal G08
```

## Rejected across all three

```text
✗ AI review verdict as approval           (VERIFICATION ≠ APPROVAL)
✗ all-green as coverage                   (passing tests ≠ coverage)
✗ agent-reported results as observations  (VER-I08)
✗ an external tool's ruling as a BADF authority decision
```
