# Equality across copies is not verification

From `BADF-DEM-0002` (**RESOLVED** — govern one non-BADF work package end to end, `WP-2026-0010`).

The first work package BADF governed that was not BADF exposed that `source_revision` was only
ever compared for *equality* across the dossier, its evidence and its approvals. A dossier
whose three copies all agreed on the all-zeros SHA passed. For BADF's own work the SHA was
always BADF's, so the hole never showed.

**Learned:** a dossier must govern a commit that *exists* and *changed what the evidence says*.
`verify_foreign_revision` now resolves the revision in the target repository, checks it
descends from the declared base, and requires the recorded `source-change` diff to equal
`git diff base..revision`. Deny unless established.

**Changed:** the same derive-and-corroborate shape now underlies `landed_as`, the composed-tree
gate, the charter floor and self-dossiers — a record's claim is checked against the world, never
against another copy of itself.
