# BADF overlay — `memory-systems` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **Conflicts are reconciled, never silently resolved.** `SKILL.md:114` ("Prefer the fact with the
  most recent `valid_from`") is **not adopted**. A contradiction is surfaced and resolved per docs/04,
  and the superseded fact is labelled `SUPERSEDED`, not dropped.
- **No raw personal data.** The `LIVES_AT` address example (`:135-137`) is illustrative only. BADF
  memory never stores secrets, tokens or raw personal data (charter §10).
- **Classification is required.** Every durable fact carries `OBSERVED` / `INFERRED` / `DECIDED` /
  `SUPERSEDED`, a source and a review date. Memory is not authority (charter §3).
- **Declared dependency:** `scripts/memory_store.py` needs `numpy`. Under BADF it is not executable
  before `VALIDATED`.
