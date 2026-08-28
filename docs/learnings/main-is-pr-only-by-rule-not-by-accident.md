# A safety net held by accident is not a control

From `BADF-DEM-0004` (Issue #19, **RESOLVED** by `BADF-WP-0016`).

Before #19, `main` refused a direct push only because a `governance` status check had never
reported on a push commit — no rule required a PR, and 18 of 23 commits were `--merge` with
zero Issue references. The repository had a safety net it did not actually have; an agent
reading the constitution would have trusted it.

**Learned:** a control that works by accident of configuration is not a control. State what is
actually enforced, and enforce what the doctrine claims. `main` is now PR-only under an active
zero-bypass ruleset, squash-only, with a required composed-tree gate; the doctrine says so and
CI proves it every push.

**Changed:** every merge since is a squash through a PR with an Issue→demand→WP→PR chain, and
`main`'s protection is asserted only where it is true (corrected in `AGENTS.md` under #407).
