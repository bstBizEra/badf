# BADF learnings

> Every resolved Issue becomes potential institutional learning. (`GITHUB_CONTROL_PLANE.md`)

When a demand reaches a terminal status (`RESOLVED` or `REJECTED`), it carries a `learning`
disposition: a file in this directory, or the literal `NONE_DECLARED`. `badf_gate.py repo`
refuses a terminal demand with neither — an explicit "nothing learned" is a claim; silence is
drift (`BADF-WP-0035`, Issue #29).

Slugs are `[a-z0-9-]+.md`. An entry states the demand it came from, what was learned, and how
it changes practice. Learnings are extend-only: correct one with a new entry, do not rewrite
history.
