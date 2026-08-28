---
name: technical-research
description: Find the technically viable approaches that could solve a problem -- an option set, not one early answer. For research types R04 (technical solution) and R05 (architecture). Produces candidate solutions grounded in the record's evidence, with their mechanisms, limitations, security, compatibility, cost, migration and reversibility. It does not compare-and-choose (comparative-evaluation), decide, or authorise.
---

# technical-research

A subskill of `badf-research` (`../../SKILL.md`). Where `repository-research` asks *what is happening
here?*, technical-research asks *what approaches exist to solve it?* It adds `alternatives` to the
research record at `work/research/<BADF-RSR-NNNN>/research-record.json` against
`schemas/research-record.schema.json`. It has no authority; an option set is evidence for a decision,
never a decision (RSR-I01).

**It yields an option set, not an early answer.** The deliverable is several candidate approaches,
each with its `mechanism` and — in the fuller record — applicability, advantages, limitations,
security, compatibility, operational cost, migration and reversibility. Choosing among them is
`comparative-evaluation`'s job; this subskill widens the option space honestly rather than narrowing
to the first idea.

**Each candidate is grounded in evidence.** An alternative's `evidence_refs` resolve to a claim,
finding or source the record holds — an approach is proposed on the strength of gathered evidence,
not asserted (control 23). A `TECHNICAL_SOLUTION` (R04) run carries at least one alternative; a
technical-solution study that proposes nothing has not been done.

## Do

1. Read the framed question and the record's evidence (`problem-framing`, `deep-research`, `repository-research`).
2. Discover candidate approaches from authoritative sources — official docs, standards, reference implementations, mature OSS, upstream issues, benchmark data — preferring primary sources.
3. Record each as an `alternative` with its `mechanism`, and where captured its applicability, limitations, security, compatibility, operational cost, migration and reversibility.
4. Ground each alternative: its `evidence_refs` point to claims, findings or sources already in the record (add the evidence first if it is missing).
5. Do **not** rank or choose — hand the option set to `comparative-evaluation`; grant no downstream authority.
