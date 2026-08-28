---
name: problem-framing
description: Convert a demand or Issue into a bounded, machine-readable research admission -- the research question, type and depth, scope and non-goals, known and unknown, hypotheses, assumptions, decision context and stop conditions -- before any research runs. The entry subskill for almost every R01-R09 route. Do not research or answer the question; do not decide or authorise anything.
---

# problem-framing

A subskill of `badf-research` (`../../SKILL.md`). It is the **entry** point: it turns a demand into
the framing of a research record at `work/research/<BADF-RSR-NNNN>/research-record.json` against
`schemas/research-record.schema.json`, in a **pre-evidence** state (`PROPOSED` / `FRAMED` /
`BASELINED`). It has no authority; its output is a bounded admission, never a conclusion (RSR-I01).

**Its one invariant: it sharpens the question; it does not research or answer it.** Research quality
is largely fixed before the first search -- so framing manages uncertainty explicitly rather than
accumulating links. A framing record therefore carries **no `claims`, `sources`, or `findings`** --
evidence appears only from `EVIDENCE_COLLECTING` onward (control 20, enforced by the gate).

## Do

1. Read the repository `AGENTS.md`, the originating Issue and its demand record.
2. Resolve the **research question** (one primary question; sub-questions allowed) and the research
   **type** and **depth** (`../../references/research-types.md`) -- the strictest the demand justifies.
3. Bound the run: `scope.include` / `scope.exclude` and explicit **non-goals**; the **known** and the
   **unknown**; the **hypotheses** to be retained or eliminated (each `OPEN` at framing).
4. State the **assumptions** the run rests on -- kept distinct from evidence -- and the
   **decision_context** (the decision this research serves), while `authority.implementation_authority`
   stays `false`.
5. Declare non-empty, bounded **stop_conditions**: the conditions under which the run terminates
   (sufficient evidence, exhausted sources, a discriminating test resolved). Unbounded framing is refused.
6. Hand the framed record to the type's route (`repository-research`, `deep-research`, …); this subskill
   never collects the evidence itself.

What is unknown at framing becomes an explicit `unknown`, a hypothesis, or a stop condition -- never a
guessed fact, and never a premature claim. The framing is the contract every later subskill reads.
