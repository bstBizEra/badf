# BADF overlay — `harness-engineering` (vendored at ASCE `58b55a8`, `BADF-WP-0156`)

This overlay **takes precedence over the upstream `SKILL.md` and its references** wherever
they conflict (charter §2: tool and skill guidance sits below the charter and docs). The upstream
files are byte-identical to the pinned commit (`BADF-PROVENANCE.json`). This skill is `IMPLEMENTED`
and not routed (`badf/skill-registry.json`, `default_policy: approved-only`).

- **Authority comes from a work package and the channel it was given in, not from a user saying so.**
  Upstream `SKILL.md:77` allows merge, deploy or push "unless the user has explicitly granted that
  permission for the specific action". In BADF, such a grant binds only the session it was made in
  (AET-I13), and only within an active work package.
- **Stopping is a valid outcome.** `:189` ("Treat stopped autonomous loops as harness failures") is
  **not adopted**. A stop code (`BUDGET_EXHAUSTED`, `AUTHORITY_CONFLICT`, …) is the correct result,
  never a defect to engineer away (AET-I06, docs/14 §6).
- **No standing schedules.** `:64` ("Refresh upstream sources on a schedule") is not adopted;
  scheduled autonomy is AET-E admission scope.
- **Dangling links.** `:217-219` point at `researcher/`, which was deliberately not vendored. Ignore
  them.
