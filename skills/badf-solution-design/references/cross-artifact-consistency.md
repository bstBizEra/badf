# Cross-artifact consistency (the heart)

This is the reconciliation contract — the reason `badf-solution-design` exists. A solution is coherent
only when the specialist artifacts agree at their seams. Each invariant below names one seam, the
question to ask, and the failure it prevents. These are **design controls**; deterministic enforcement,
where a seam earns it, lands in the canonical gate through a separate failing-first WP — never a second
validator here (SOL-I12).

## Enforcement status

WP-SOL-C enforces the **matrix-internal** seams — the co-occurrence a composition can be judged on from
the matrix alone — in the canonical `solution` command, each mutation-killed:

| Control | Seam | Rule (matrix-internal) | Status |
| :--- | :--- | :--- | :--- |
| SOL-C04 | SOL-I04 | a row with `api_refs` carries `authorization_refs` | **enforced** (WP-SOL-C) |
| SOL-C05 | SOL-I06 | a row with `authorization_refs` carries `audit_refs` | **enforced** (WP-SOL-C) |
| SOL-C06 | SOL-I09 | a row with `ux_refs` carries `accessibility_refs` | **enforced** (WP-SOL-C) |

The **external-artifact** seams — SOL-I02 (against the architecture baseline), SOL-I05 (default-deny in
the authorization model), SOL-I07 (API↔data schemas), SOL-I10 / SOL-I11 (migration / API-compat) — and
the *semantic* resolution of every ref against its specialist artifact **cannot** be enforced until the
specialist adapters exist; they are **deferred to those WPs**, honestly, not faked. SOL-I01 is structural
(WP-SOL-B, schema-enforced). SOL-I03 / SOL-I08 await a matrix field to disambiguate the non-API / recovery
cases.

## The seams

### SOL-I01 — Requirement provenance
Every material detailed-design element resolves to a `REQ` / `NFR` / a declared G03 design need / an
architecture constraint. **No orphan design.** A screen, endpoint, table or permission that traces to
nothing is either undeclared scope or dead work.

### SOL-I02 — Architecture consistency
Every API boundary, data owner, external integration and trust transition resolves against the
**architecture baseline** (owned by `badf-architecture`). A boundary the baseline does not contain is not
solution-design's to invent — raise `ARCHITECTURE_CHANGE_REQUIRED`.

### SOL-I03 — UX ↔ API
A system action a user/service flow requires has an implementable API contract **or** an explicit
non-API mechanism. "The button approves the refund" with no operation behind it is an inconsistency.

### SOL-I04 — API ↔ authorization
Every protected operation carries `resource`, `action`, `scope`, a `decision point`, and a `default
behavior`. "Any authenticated user can call the endpoint" is pseudo-authorization, not authorization.

### SOL-I05 — Default deny
An authorization tuple that matches no rule resolves to **DENY**.

```text
NO MATCH = DENY
```

### SOL-I06 — Authorization ↔ audit
A security-sensitive authorization decision defines an **audit obligation**. A privileged action that
records nothing cannot be investigated.

### SOL-I07 — API ↔ data
The request/response models and the persistence model cannot silently disagree on **identity,
nullability, cardinality, state, lifecycle, or ownership**. An API that returns a field the data model
cannot produce is a seam defect.

### SOL-I08 — UX ↔ error
Every material API/domain failure exposed to a user has a **recovery state** in the flow. A failure with
no path forward is a dead end.

### SOL-I09 — Accessibility binds behavior
Accessibility binds **interaction states**, not a checklist appended to a screen:

```text
interaction → keyboard behavior → focus behavior → semantic announcement → error behavior → state-change notification
```

### SOL-I10 — Migration safety
A breaking persistence change carries a **reversible or evolvable** migration plan. An irreversible
destructive migration with no plan is a data-loss risk.

### SOL-I11 — API compatibility
A breaking API change is explicitly **identified and dispositioned** (removed operation, required-field
addition, enum narrowing, type/response-code change, auth change, pagination/idempotency change). Silent
breakage is refused.

### SOL-I12 — No second gate
`badf-solution-design` introduces **no** `scripts/badf_solution_design.py`, no competing validator, gate,
schema-authority or lifecycle result. Deterministic evidence semantics belong to the canonical
`badf_gate.py` through separately-authorized work.

## The example the invariants catch

```text
UX:            "Manager approves refund"
Authorization: manager has no refund:approve action        ← SOL-I04 / SOL-I05
API:           POST /refunds/{id}/approve                   ← SOL-I03 ok, but…
Data:          refund has no approval state                 ← SOL-I07
Audit:         nothing                                      ← SOL-I06
Accessibility: approval failure is conveyed only by color   ← SOL-I09 / SOL-I08
```

Every artifact looks reasonable alone; RECONCILE surfaces five seam defects.

## Solution-composition matrix

The detailed-design equivalent of the G02 RTM: one row per requirement, binding the specialist artifacts
that satisfy it, so coverage and coherence are reconstructable in both directions.

| Requirement | UX | API | AuthZ | Data | Audit | A11y | Test |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| REQ-021 | FLOW-04 | API-17 | ACT-09 | ENT-Refund | AUD-12 | A11Y-08 | TEST-31 |
| REQ-022 | FLOW-05 | API-18 | ACT-10 | ENT-Refund | AUD-13 | A11Y-09 | TEST-32 |

Machine shape (no new global ID family is invented at freeze — a `solution-composition` object is
sufficient; a dedicated `SDM-NNNN` family waits for proven need in WP-SOL-B):

```json
{
  "solution_id": "...",
  "requirement_ref": "REQ-021",
  "ux_refs": ["FLOW-04"],
  "api_refs": ["API-17"],
  "authorization_refs": ["ACT-09"],
  "data_refs": ["ENT-Refund"],
  "audit_refs": ["AUD-12"],
  "accessibility_refs": ["A11Y-08"],
  "test_refs": ["TEST-31"]
}
```
