<!-- BADF PR body = the squash commit message on main (BADF-WP-0034, #27).
     gh pr create --body-file overrides this; CI enforces the shape via
     scripts/check_pr_traceability.py. Keep the two headings and the two
     trailer lines. -->

## What

<!-- What this change is, and the Issue it answers. One paragraph. -->

## Verification

<!-- The evidence, from the tree that ships: failing-first, mutation kills,
     `python3 scripts/badf_compose.py --message-file <this body>` in both
     shapes. Cite the SHA you measured. -->

Work-Package: BADF-WP-NNNN
Closes #N
