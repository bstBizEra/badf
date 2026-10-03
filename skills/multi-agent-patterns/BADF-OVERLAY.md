# BADF overlay — `multi-agent-patterns` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **Supervisor only; swarms are not adopted.** `SKILL.md:99` ("Prefer swarm architectures over
  supervisors …") and the `forward_message` direct-to-user pattern (`:82-97`) are **not adopted**.
  BADF routes to the minimum necessary specialists, "never as a standing swarm", and the coordinator
  owns integration and evidence completeness (docs/14 §3, §4). Sub-agent output reaches the principal
  through the coordinator.
- **Adopted:** context isolation, bounded hand-offs and time-to-live limits (`:218`). These match
  AET-I01 and AET-I06.
