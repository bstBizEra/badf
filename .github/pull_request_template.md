<!-- BADF PR body = the squash commit message on main (BADF-WP-0034, #27).
     gh pr create --body-file overrides this; CI enforces the shape via
     scripts/check_pr_traceability.py. Keep the two headings and the two
     trailer lines.

     One identity, three faces, one NNNN (BADF-WP-0070 / badf-git GIT-B):
       trailer  Work-Package: WP-2026-NNNN        the binding (machine id)
       title    BADF-WP-NNNN: <concise outcome>   the display label
       branch   wp/WP-2026-NNNN-<slug>            lowercase kebab slug
     CI refuses a PR whose title, branch or trailer disagree. -->

## What

<!-- What this change is, and the Issue it answers. One paragraph. -->

## Verification

<!-- The evidence, from the tree that ships: failing-first, mutation kills,
     `python3 scripts/badf_compose.py --message-file <this body>` in both
     shapes. Cite the SHA you measured. -->

Work-Package: WP-2026-NNNN
Closes #N
