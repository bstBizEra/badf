# AET-B substrate design — what four agent teams teach the AET (`BADF-WP-0154`)

Status: **PROPOSED design. This document builds nothing, opens no rung and grants no authority**
(docs/14 §5, AET-I03). The AET-B rung stays gated as docs/14 §8 states; §7 below reports the
gate as measured and does not decide it. A design accepted here becomes a set of separately
governed work packages (§6), one per component.

## 1. Sources and method

Four sibling repositories in the `bstBizEra` organisation were studied **read-only**, each by
an independent reader. The load-bearing claims were then re-measured against the files before
they were written here (§1.1). The readers' reports are model output: everything below that
is not in §1.1 is labelled as **reported**, and a design decision that rests on it says so.

| Source | Ref studied | What it is |
| :-- | :-- | :-- |
| `biztrust` | `motor/biztrust-wp-001/r14-1` (`84a51be`) | A product repository running a BADF-shaped **seat registry** with two-language validators, pins held in code, and 15+ independent review rounds |
| `biztrust_ib` | `main` (`f3f8900`) | A product repository whose `BIZTRUST-ADF-ENG-001` v0.3 **names BADF its canonical control plane** and proposes docs/14's six seats; a budgeted heartbeat loop |
| `bERP` | `main` (`d30a3c3`) | An ERPNext fork that **rejected a ten-persona team** for one implementer plus one read-only reviewer, with tested session hooks and a 24/7 build routine |
| `badf-flow-control` | `import/v0.9.0-baseline` | A context-neutral flow-control kernel built as a skill under BADF: lifecycle plus orthogonal holds, capability routing, execution envelopes; a decision library with no runtime |

### 1.1 Re-measured

| Claim | Measurement |
| :-- | :-- |
| biztrust holds seats, not agents | `badf/agents.yaml:3` "A role is a seat, not a person and not an agent"; four seats `may_be_an_agent: false` |
| biztrust's pins live in the validator | `scripts/validate_continuity.py:1541` `PINNED_ROUTING = {`; DEC-025 records the reason |
| biztrust's validator can be edited by a seat an agent holds (its blocker R7-4) | `badf/agents.yaml:91-93` routes `scripts/**` to `platform-engineer` / `peer-reviewer`, both agent-holdable |
| bERP's reason for a two-role team | `docs/adr/0001-lean-quality-gate.md:11` "the same model with a different instruction file. That gives no extra expertise. What an agent can add is a fresh context … and a restricted tool set" |
| bERP's reviewer cannot change what it judges | `.claude/agents/reviewer.md:4` `tools: Read, Grep, Glob`; a `SubagentStop` hook (`.claude/settings.json:83`) |
| bERP's guard declares what it is not | `.claude/hooks/repo-guard.py:14` "a convenience guard, not the security boundary" |
| biztrust_ib puts BADF above its team | `docs/architecture/BIZTRUST-ADF-ENG-001-v0.3.md:21` "BADF remains the canonical control plane … The BizTrust ADF team is the bounded execution and learning plane" |
| biztrust_ib's loop budget fails closed | `docs/next-stage-action-plan.md:35` "if its value cannot be verified, pause without dispatch … An interrupted wake still counts" |
| flow-control's independence is by name only | `skill/scripts/route_work.py` compares `builder_skill == skill.get("name")` and trusts a catalog boolean `independent_controlled` |
| flow-control's neutrality guard cannot fire | `skill/examples/context-neutrality-policy.json:46` `"\\\\bissue…"` is double-escaped, so it never matches |

## 2. Where the four agree

Each of these is practised by at least three of the four sources, and each already has a
home among docs/14's invariants. They are adopted as **design constraints** on every
component in §5.

1. **The control plane decides and the team proposes.** Every source puts deterministic
   records or a human above agent output. biztrust_ib says so about BADF in as many words.
   *(AET-I03, I12)*
2. **Roles are bounded by tools and context, not by persona.** A seat is a role with a
   restricted capability set and a fresh context. bERP's ADR shows that a persona adds
   nothing, and biztrust's "a seat, not an agent" says the same. *(docs/14 §3 "never a
   standing swarm")*
3. **The reviewer is read-only and has a fresh context, and its verdict binds to an exact
   candidate.** bERP's reviewer cannot write. biztrust_ib's review record carries SHA, base
   and blob hashes with a re-review trigger. biztrust re-ran reviewers per round. *(AET-I02,
   I04)*
4. **Hand-offs are file-based, scoped and digest-bound — never pasted history.** These take
   the form of bERP's task brief and review package, flow-control's execution envelope,
   biztrust's self-prompt contract and biztrust_ib's assignment template. bERP measured one
   pasted dispatch at 42k characters, 99% of it history. *(AET-I01, I08)*
5. **Budgets are persisted state that fails closed.** An interrupted attempt counts, and an
   unverifiable counter pauses the loop. *(AET-I06, I07)*
6. **Resume reads recorded state; it never continues from recollection.** biztrust's
   nine-step resume ends in a closed outcome set. *(AET-I07)*
7. **Corrections are appended, not rewritten.** Overclaims are withdrawn on the record
   (biztrust DEC-021). *(docs/learnings extend-only rule)*

## 3. Failure modes the sources measured in themselves

The design must not reproduce these. Each one is a member of the class in
`docs/learnings/a-guard-that-cannot-fail-is-not-a-guard.md`.

| # | Failure | Where | Design consequence |
| :-- | :-- | :-- | :-- |
| F1 | **The enforcer is editable by the enforced.** `scripts/**` routes to agent-holdable seats, so editing the validator defeats every pin | biztrust R7-4 (§1.1) | The AET's own enforcement surfaces (`scripts/badf_gate.py`, `badf/authority-matrix.json`, `badf/seats.json`) carry a review route no agent-holdable seat can satisfy (§5 S1) |
| F2 | **Independence asserted, not recorded.** Independence is a catalog boolean and a name comparison | flow-control (§1.1); biztrust "nothing checks who reviewed" (reported) | A verdict records the reviewing run's and the authoring run's session/run ids, and the validator refuses equality. Shared-account identity stays declared non-coverage (#261) |
| F3 | **A guard that cannot fire.** A double-escaped regex; a fail-open parser; a verdict hook that passes when `jq` is missing | flow-control (§1.1); bERP (reported) | Every AET control enters AET-C with failing-first and mutation evidence (docs/14 §8). Parse failure is a refusal |
| F4 | **The routine outran the authority.** bERP's "one prompt is enough … without pausing" conflicts with its human HARD-GATE, and a 24/7 routine amplifies it. biztrust_ib's heartbeat is paused for lack of approvers | bERP, biztrust_ib (reported) | Scheduled autonomy is **AET-E admission scope**. No AET-B component schedules anything |
| F5 | **State outside the record.** Review records sit in a gitignored folder, heartbeat state lives only in the host, and a slash-command definition is gitignored | biztrust_ib, biztrust (reported) | Every substrate record lives under `work/<WP>/` and is lockfile-covered. Host-only state is non-coverage, stated |
| F6 | **One identity for operator and agent.** The seated human and earlier agent commits shared a git identity | biztrust B6 (reported) | No new mechanism. This is #261's class; the design cites it rather than claiming to close it |

## 4. Explicitly not adopted

- **Persona teams and standing swarms.** bERP's ADR rejected them with evidence, and docs/14
  §3 already forbids them.
- **Council or orchestrator agreement as evidence.** biztrust rejected it, and AET-I03
  already does.
- **Vendoring large skill catalogues.** bERP vendors 63 skills with overlapping duties. Routing
  stays on `badf/skill-registry.json` at execution time (docs/14 §4).
- **A second validator or lifecycle engine.** flow-control's evaluators and bERP's G0–G16
  are not imported. `badf_gate.py` stays the one canonical gate (AET-I12). flow-control's
  ideas enter as data shapes, not as a competing engine.

## 5. Proposed substrate components

Each component is one future work package. It adds records and validation to the
deterministic control plane, and it changes **what is recorded, never what is permitted**.

| ID | Component | Shape | Learned from | Invariants |
| :-- | :-- | :-- | :-- | :-- |
| **S1** | **Enforcement-surface routing** | A pinned list, in validator code, of AET enforcement surfaces whose change requires a human-reserved reviewer from `badf/authority-matrix.json` — never data the surface itself can edit (biztrust DEC-025) | biztrust pins and R7-4 | I01, I10, I12 |
| **S2** | **Dispatch envelope** | `work/<WP>/dispatch/<id>.json`: WP id, seat, base/head SHAs, allowed paths ⊆ `expected_surfaces`, tools, budget, stop codes, required evidence, and the digest of the brief file. The validator refuses a path outside the WP's surfaces | flow-control envelope; bERP task brief; biztrust self-prompt; biztrust_ib assignment template | I01, I06, I08 |
| **S3** | **Review package and verdict record** | A package built from `base..head` that refuses a non-ancestor or empty range (bERP). A verdict bound to the candidate SHA and content tree, carrying the authoring and reviewing run ids, which must differ. Re-review verdicts each prior finding ADDRESSED / NOT_ADDRESSED. A verdict on a moved candidate is stale | bERP review package and re-review; biztrust_ib exact-candidate record; flow-control's independence gap | I02, I04, I08 |
| **S4** | **Budget and resume on the run ledger** | Extends the existing `run-ledger-event` schema (hash-chained, append-only) with attempt events. An interrupted attempt counts. An unverifiable counter yields `BLOCKED`, never a reset. Resume ends in a closed set: `CONTINUE` / `BLOCKED` / `WAIT_FOR_AUTHORITY` / `RECOVERY_REQUIRED` / `COMPLETE` | biztrust_ib budget; biztrust resume protocol; flow-control loop identity | I05, I06, I07 |
| **S5** | **Rulings and closing contract** | When a bounded loop ends with findings it chose not to fix, each ruling is recorded as *what — why — cost if wrong* and listed back to the principal. A session's close names its status, the decisions needed (as options) and the next safe action | bERP rulings ledger and closing contract | I06, I13 |

**Deliberately absent:** a scheduler, a coordinator runtime, model or cost routing,
seat-occupancy automation, and any `badf init` team profile. These are AET-D/E or INIT scope.

## 6. Proposed sequencing

`S1 → S3 → S2 → S4 → S5`.

- **S1 first.** It closes the class (F1) that would let every later control be edited
  away.
- **S3 before S2.** Independent review is the control whose absence the sources felt most,
  and S2's envelope cites S3's verdict record.
- **Every component carries its own controls.** Each is a separate WP with failing-first and
  mutation evidence on each control it adds. That is AET-C's standard applied as each
  component is built, not afterwards.

## 7. The AET-B gate, as measured

docs/14 §8 gates AET-B on **P1-before-P3** — #220/#234 dispositioned and #211/#218 owned or
parked deliberately — **and** on the #246 ratchet having landed. Measured on 2026-10-03
against the issue tracker:

| Prerequisite | State | Reading |
| :-- | :-- | :-- |
| #234 | closed (completed) | met |
| #211 | closed (completed) | met |
| #218 | closed (completed) | met |
| #246 | closed (completed) | met |
| #220 | **open**; last activity 2026-09-02; no assignee, no label, no disposition recorded | **not shown met** |

**Gate reading: `HUMAN_REQUIRED`.** #220 carries live measurement and binding conditions
from four seats, but no ruling that dispositions it. "Dispositioned" is a judgement this
document does not make. AET-B opens by a recorded decision — dispositioning #220, or
re-sequencing the gate — in the operator's own channel (AET-I13). The decision is not
inferred from this design existing or being accepted.

**Update, 2026-10-03 (`BADF-WP-0157`).** The operator recorded the decision this section called
for. `BADF-DEC-0008` dispositions #220 as **parked** (owned, deferred; neither closed nor waived), so
the gate is met and **AET-B is open**. S1 is the first component built. A work package that touches a
pinned enforcement surface must be C3, checked on its declared surfaces by `repo` and on its actual
diff by compose. S2–S5 remain separate work packages. AET-C/D/E remain gated as docs/14 §8 states.

**Update, 2026-10-04 (`BADF-WP-0158`).** S3 is built, second per §6.
- **Review package.** `badf_gate.py review-package <WP>` builds the candidate from `base..head`,
  excluding `work/<WP>/` and the lockfile exactly as the content tree does. It refuses a
  non-ancestor, empty or unknown range.
- **Verdict record.** A verdict lives at `work/<WP>/reviews/REV-NN.json`
  (`schemas/review-verdict.schema.json`), and `repo` validates every verdict. Each one must be:
  - bound to its package digest;
  - written by a reviewing run that is not the authoring run, with no deviation path;
  - explicit about findings or non-coverage;
  - consistent: APPROVE never stands beside a blocking finding.

  A re-review must disposition every prior OPEN finding exactly once.
- **Staleness.** `badf_gate.py review-check <WP>` reads the latest verdict against the head now
  and reports `CURRENT`, `STALE` or `NONE`.
- **What S3 does not do.** It records who reviewed what and permits nothing. No gate yet
  requires a verdict. A run id distinguishes sessions, not people (#261).

## 8. Non-coverage, stated

- **The readers' reports were not re-measured in full.** Rows marked *reported* rest on one
  reader each.
- **Private repositories were read through this session's access.** Nothing from them is
  quoted beyond the cited lines.
- **Identity is not addressed.** The design does not solve operator/agent identity (#261, F6).
  A run id distinguishes sessions, not people.
- **S1 and S3 are built (§7 updates); S2, S4 and S5 are not.** Every claim about those three is a design claim.
