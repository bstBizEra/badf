---
name: fact-checking
description: Verify one or more explicit factual claims against evidence already bound to the research record, preserving uncertainty, contradiction and provenance. A cross-cutting primitive for research type R10 and for every multi-source route. It may strengthen or weaken a claim's status from evidence; it may not acquire new external sources, decide, or authorise anything.
---

# fact-checking

A subskill of `badf-research` (`../../SKILL.md`). It adjudicates the `status` of claims in a research
record at `work/research/<BADF-RSR-NNNN>/research-record.json` against
`schemas/research-record.schema.json`, using the record's existing statuses
(`VERIFIED` / `PARTIALLY_VERIFIED` / `DISPUTED` / `UNVERIFIED` / `FALSIFIED`) and the canonical
derived confidence. It has no authority; a verdict is evidence for a decision, never a decision (RSR-I01).

**Its three invariants:**

```text
NO EVIDENCE   ≠ FALSE      (absence of support does not falsify)
NO CONTRADICTION ≠ VERIFIED (absence of dispute does not confirm)
CITATION      ≠ SUPPORT    (a resolving reference is not adjudication)
SOURCE_EXISTS ≠ SOURCE_SUPPORTS_CLAIM  (a resolving source is not entailment — RSR-I06)
```

`verification_status` is a function of evidence, not of researcher judgment. Status↔evidence
consistency is enforced by the gate: a `FALSIFIED` claim carries a contradicting source, and a
`DISPUTED` claim carries both supporting and contradicting sources (control 21). Whether a source's
content **substantiates** a claim is this skill's judgment, not the gate's: a `VERIFIED` claim on cited
support either carries a `support_assessments` receipt (`{relation, assessment, locator, …}`, one per
supporting source — the locator is where you looked) or declares `semantic_support: NON_COVERAGE`.
The gate refuses silence and refuses a receipt that does not substantiate the binding (control 27,
RSR-I06); it never asserts the entailment itself.

**Scope boundary — this is not the acquisition skill.** It operates only over evidence already in the
record: `repository-research` findings, operator-provided artifacts, and sources bound by an earlier
run. It does **not** crawl or search — that is `deep-research`. When adequate evidence is absent, the
honest outcome is `UNVERIFIED` (or a `MORE_RESEARCH_REQUIRED` disposition), never "search until
something agrees".

## Do

1. **Target** — identify the exact claim to verify.
2. **Atomize** — split a compound assertion into independently verifiable atomic claims without changing meaning.
3. **Bind** — map each atomic claim to `supporting_sources` and `contradicting_sources` already in the record.
4. **Check support** — ask whether the cited evidence actually substantiates the claim; a reference existing is not support. For a `VERIFIED` binding, record the judgment as a `support_assessments` receipt (`relation`, `assessment`, and a `locator` into the digest-bound source) or, honestly, declare `semantic_support: NON_COVERAGE` — never leave it silent (control 27, RSR-I06).
5. **Check contradiction** — inspect the contradictory evidence already available; do not discard it.
6. **Classify** — keep `OBSERVED` / `REPORTED` / `INFERRED` / `HYPOTHESIS` / `DECIDED` distinct.
7. **Adjudicate** — `VERIFIED` / `PARTIALLY_VERIFIED` / `DISPUTED` / `UNVERIFIED` / `FALSIFIED`, consistent with the bound evidence.
8. **Derive confidence** — reuse the canonical pure function; never assert a level.
9. **Declare non-coverage** — state what could not be checked (including any claim whose sources carry no inspectable content).
10. **Hand off** — return adjudicated claims to `evidence-synthesis` / `research-reconciliation`; grant no downstream authority.
