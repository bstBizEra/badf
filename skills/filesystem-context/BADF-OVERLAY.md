# BADF overlay — `filesystem-context` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **Struck: agents writing their own instruction files.** `SKILL.md:141` ("Have agents write learned
  preferences and patterns to their own instruction files so subsequent sessions load this context
  automatically") and the "agents that learn and update their own instructions" framing (`:19`) are
  **not adopted**. In BADF, learning never expands authority (AET-I09), and instruction files
  (`AGENTS.md`, skills) change only through a work package and review.
- **Durable memory follows docs/04.** The `memory/preferences.yaml` pattern (`:191-192`) is replaced
  by BADF memory records. Each record is labelled `OBSERVED` / `INFERRED` / `DECIDED` / `SUPERSEDED`,
  with its source and review date. No secrets and no raw personal data (charter §10).
- **Adopted:** scratchpads, tool-output offload and file-backed working notes inside the session's
  scratch area. That is session-record material, not memory (charter §10).
