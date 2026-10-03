# An agent team is bounded by tools and records, not by personas

From `BADF-DEM-0139` (Issue #351, `BADF-WP-0154`). The full study is in
`docs/governance/AET_B_SUBSTRATE_DESIGN.md`.

Four sibling repositories built agent engineering teams independently: `biztrust`,
`biztrust_ib`, `bERP` and `badf-flow-control`. Read side by side, they converge, and the
places where they converge are not persona design.

**Learned:**

- **What a role adds is restriction.** A second agent adds a fresh context and a smaller tool
  set, and nothing else (bERP ADR-0001). A seat is defined by what it *cannot* touch and by
  the records it must leave.
- **The worst defect each team found was in its own controls.** It was not in the product:
  - biztrust's validator could be edited by a seat an agent may hold;
  - flow-control's independence check compared names, and its neutrality regex could never
    match;
  - bERP's guard fails open on input it cannot parse.

  Each one is an instance of `a-guard-that-cannot-fail-is-not-a-guard.md`.
- **Scheduled autonomy arrives before the authority to use it.** bERP runs a 24/7 routine that
  conflicts with its own human gates. biztrust_ib's heartbeat is paused because no approver is
  seated. biztrust built five human gates and seated no one able to record them.
- **State that lives outside the record cannot be audited**, however carefully it is kept.
  The examples are gitignored review records, host-only loop counters and an unversioned
  slash command.

**Changed:**

- The AET-B design orders the substrate so that the AET's own enforcement surfaces are pinned
  first (S1).
- A review verdict must record the authoring and reviewing run ids, and the validator must
  refuse a verdict where they are equal (S3).
- Scheduled autonomy is left to AET-E admission.

This learning changes design, not enforcement. Nothing here is checked by a gate until the
corresponding component lands with its own failing-first evidence.
