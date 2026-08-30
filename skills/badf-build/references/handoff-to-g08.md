# Handoff — package, route to badf-git, hand to G08 (BLD-I17)

The source methodology finishes through a branch-finishing skill. BADF routes instead:

```text
badf-build
  PACKAGE G07
       ↓
badf-git
  inspect branch / base / composition / staleness
       ↓
G08 independent verification
       ↓
PR / integration authority
```

`badf-build` may **commit to the authorized working branch** if granted. It must not infer:

```text
tests pass → push → open PR → merge
```

Each side effect follows its own authority: push and PR under `badf-git`'s branch/PR contract, merge under
the integration authority, release under G10/G11. The build's handoff states what was built and
author-verified, what was not covered, and what the next authority must decide.
