# BADF overlay — `tool-design` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **No arbitrary-shell reduction.** `references/architectural_reduction.md:35,47` ("Run arbitrary bash
  commands" as a replacement for specialised tools) is **not adopted**. BADF prefers the narrowest
  tool, keeps read, write, destructive and admin capabilities separate, and registers external
  capabilities (charter §12, docs/08). The upstream caveat at `SKILL.md:67` ("Avoid reduction when …
  safety constraints must limit agent actions") always applies here.
