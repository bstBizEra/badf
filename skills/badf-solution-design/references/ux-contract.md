# UX / service-behavior contract

The output contract for the UX / service-design specialist (routed on journey / screen-state / task-flow
/ recovery signals). Composes into **G03** evidence (journeys, service-blueprint, user-validation). The
specialist owns *how* the interaction behaves; `badf-solution-design` owns that its behavior is coherent
with the other artifacts.

## Output contract

- **task flows** — the steps a user/service takes to satisfy a requirement, each traced to a `REQ`/G03 need (SOL-I01);
- **interaction states** — the states each step can be in (idle, in-progress, success, each failure);
- **error / recovery paths** — every material failure exposed to the user has a recovery state (SOL-I08);
- **service blueprint** — the front-stage / back-stage / supporting-system view behind the flow;
- **engineering handoff** — the system actions each step requires (feeding SOL-I03: each has an API contract or an explicit non-API mechanism).

## Seams it must satisfy

- **SOL-I03** — every system action a flow requires resolves to an API operation or a declared non-API mechanism.
- **SOL-I08** — every failure surfaced in a flow has a recovery state.
- **SOL-I09** — each interaction state carries its accessibility behavior (see `accessibility-contract.md`).

The UX specialist must not assert an action the authorization model denies (SOL-I04) or a data effect the
data model cannot hold (SOL-I07); such assertions are reconciled, not shipped.
