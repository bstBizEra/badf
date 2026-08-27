# Two-plane verdict

**Status:** Normative. Work package `BADF-WP-0005`, implementation tier (§9-A).
**Enforced by:** `scripts/badf_gate.py::verify_two_plane`.
**Ported from:** secb_pf `TWO_PLANE_DECISION_MODEL.md`, whose rule is: *posture is computed
from the register, never from the verdict's prose.*

## Two planes

| Plane | Field | Source |
| :--- | :--- | :--- |
| **A — baseline** | `disposition` | asserted by the author: `PASS · PASS_WITH_CONDITIONS · FAIL · BLOCKED · HUMAN_REQUIRED` |
| **B — obligation** | `obligation_posture` | **computed** from `conditions`: `CLEAR · OPEN_NON_BLOCKING · OPEN_BLOCKING` |

`OPEN_UNCONTROLLED` — a condition without owner, predicate or authority — is not a posture. It
is a decision defect and is refused outright by the conditions control before this one runs.

## Rendering matrix

| Plane A | Plane B | Rendered verdict |
| :--- | :--- | :--- |
| `PASS` | `CLEAR` | `APPROVED` |
| `PASS_WITH_CONDITIONS` | `OPEN_NON_BLOCKING` | `APPROVED_WITH_CONDITIONS` |
| `PASS_WITH_CONDITIONS` | `OPEN_BLOCKING` | **refused** — the honest verdict is `HELD_FOR_CONDITION_CLOSURE`; a gate cannot be passed while a condition blocks it |
| `PASS` | anything but `CLEAR` | **refused** |
| `FAIL` | any | `REWORK_REQUIRED` |
| `BLOCKED` / `HUMAN_REQUIRED` | any | pass-through |

`blocking_scope` must be `none`, a gate id `G00..G14`, or a comma list. Free text is refused:
an unparseable scope cannot be compared to the gate under decision, and treating it as
non-blocking would be the fail-open.

## The verdict is an output

`obligation_posture` and `rendered_verdict` are written by the gate. A dossier may declare
`rendered_verdict`; if it does, it must equal the computed one, or the gate refuses. An
absent declaration is filled in. The author's plane is one input; it is never the verdict.

Proven necessary before it was built: a dossier asserting `PASS_WITH_CONDITIONS` with an OPEN
*Critical* condition whose scope covered the very gate being passed returned `PASS`, exit 0.
