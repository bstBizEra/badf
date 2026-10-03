# BADF overlay — `evaluation` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **"Quality gates" here are measurements, not BADF gates.** The upstream text uses "quality gates"
  (`SKILL.md:3`, `:17`, `:217`) for pipeline thresholds. In BADF, only `badf_gate.py` decides a lifecycle
  transition (AET-I12). An evaluation built with this skill produces evidence for a gate dossier; it
  never replaces one.
- **An unrun check is never a pass** (charter §14: report PASS / FAIL / BLOCKED / NOT_RUN).
