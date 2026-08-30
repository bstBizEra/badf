# Issue projection

```text
work/WP-2026-NNNN/work-package.json   = the canonical execution contract
GitHub Issue #NNN                      = a tracking / collaboration projection
```

A GitHub Issue displays the WP (objective, acceptance, blocked-by, risk, expected surface), but its state
**cannot grant or revoke authority** (IMP-I14):

```text
Issue "ready-for-agent"   does NOT imply   WP legally executable
```

```text
EXECUTABLE = WP status READY
  AND dependencies satisfied
  AND baseline current
  AND authority valid
  AND budget declared
  AND stop conditions declared
```

Opening or closing an Issue is a tracking act, not a lifecycle or mutation authorization.
