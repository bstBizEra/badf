# Composition order

**Landing/composition order is represented separately from execution blockers** (IMP-I06). Two WPs may be
implemented independently (no `blocked_by`) yet must land in a specific order (`composition_after`) — e.g.
a schema migration lands before the code that depends on it.

```text
blocked_by         gates when work may BEGIN
composition_after  gates when work may LAND
```

Collapsing the two loses information: a plan that only has `blocked_by` cannot express "build in parallel,
land in sequence", which is exactly what safe integration needs. The composed-tree landing is realized by
`badf-git` / `badf_compose.py`; the plan only **declares** the order.
