# BADF overlay — `advanced-evaluation` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **A judge's output is evidence, never a verdict.** LLM-as-judge scores, pairwise preferences and
  rubric results may be cited as evidence. They never approve a change, open a gate or satisfy an
  independent-review requirement (AET-I02, AET-I03). `badf_gate.py` is the one canonical gate (AET-I12).
- **Judge independence is recorded, not assumed.** Record the judge model and the run that produced
  the judged output. A judge from the same authoring run is not independent.
