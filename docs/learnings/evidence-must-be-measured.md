# An evidence line is measured output, never inference

From `BADF-DEM-0013` (Issue #24, **REJECTED**).

#24 claimed `schemas/` was not under `INTEGRITY_PATHS`, with an Evidence line quoting a
command returning `[]`. The command was never run in that step; `schemas/*.json` had been
locked since `BADF-WP-0007`. A demand record and a work package were opened on a false
premise before the mistake was caught.

**Learned:** an Evidence line is the *pasted output* of a command executed in the same step —
never a remembered or inferred result. Before filing an Issue that asserts a gap ("X is not
locked / checked / present"), run the positive control first: show the thing present where the
claim says it is absent, or the exact grep returning nothing, in that step. Converting a
partial read into a FAIL claim is the same defect as converting missing evidence into PASS.

**Changed:** #43 (the real `examples/` gap) was filed *with* its measurement pasted. This
learning is enforced socially, not mechanically — the gate cannot know whether a human ran a
command; the discipline is the control.
