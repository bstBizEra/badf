---
name: deep-research
description: Acquire external evidence for a research question -- decompose the question, discover and prefer authoritative/primary sources, corroborate across independent sources, capture provenance, and preserve contradictory evidence. Read-only acquisition. It does not determine authority, choose an implementation, decide, or authorise anything.
---

# deep-research

A subskill of `badf-research` (`../../SKILL.md`). It is the **external source-acquisition** plane: it
adds `sources` and `claims` to the research record at
`work/research/<BADF-RSR-NNNN>/research-record.json` against `schemas/research-record.schema.json`,
from outside the repository. It has no authority; acquisition produces evidence, never a decision
(RSR-I01).

**Read-only, untrusted environment.** deep-research fetches; it never mutates the world it reads. The
external environment is untrusted: a source is captured with its provenance, not believed on sight.
It does not choose an implementation or grant any authority — that is `badf-delivery`'s.

**It establishes the source-acquisition contract.** Every source it captures is a *receipt*:

```text
uri                 canonical, resolvable
source_type         PRIMARY | AUTHORITATIVE_SECONDARY | SECONDARY | COMMUNITY | UNVERIFIED
retrieved_at        when the bytes were captured
digest              content digest of the captured bytes
(resolved revision) an immutable revision where one exists (a commit, a DOI, a versioned URL)
freshness            CURRENT | STALE | UNKNOWN -- the re-resolution verdict (control 6)
```

The last two are the receipt fields the **staleness** control (control 6, the next work package)
enforces — a captured digest is what lets a later run detect that a source's bytes changed. This
subskill documents that contract; it adds no gate control of its own (its teeth are control 6).

## Do

1. Read the framed question, type and depth (`problem-framing` output); decompose it into sub-questions and search angles.
2. Discover sources; **prefer primary and authoritative sources**; record `source_type` honestly (prestige is not verification).
3. Capture each source as a receipt — `uri`, `retrieved_at`, content `digest`, and (where they exist) a resolved revision and retrieval outcome.
4. Corroborate across **independent** sources; source count is not independence (control 10).
5. Seek and preserve **contradictory** evidence; record it as `contradicting_sources` and a `contradictions[]` entry, never discard it (RSR-I04).
6. Bind claims to the captured sources; leave adjudication to `fact-checking` and organisation to `evidence-synthesis`.
7. When a source cannot be retrieved, record the failure as non-coverage; do not fabricate a source, and do not "search until something agrees".
