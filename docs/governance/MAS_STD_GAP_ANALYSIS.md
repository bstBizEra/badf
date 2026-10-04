# MAS-STD gap analysis: BADF's Agentic Engineer Team against the Production Standard for Agentic & Multi-Agent Systems

| | |
| :-- | :-- |
| **Status** | **PROPOSED research record.** It builds nothing, opens no rung and grants no authority (AET-I03). |
| **Repository** | `bstBizEra/badf` @ `b9936e591530a74f919a86c80934b575c3a231e3` (main, after #362) |
| **Date** | 2026-10-04 |
| **Work package** | `WP-2026-0160` (C1, records only), answering #363 (`BADF-DEM-0145`). The research was done read-only; the work package lands the record. Each candidate in §5 is a separate future work package that a human must authorize (charter §7). |
| **Labels** | **OBSERVED** = read in the repo or a cited source. **INFERRED** = reasoned from observed facts. **UNVERIFIED** = from a secondary source or memory, not confirmed. |

---

## 1. Executive summary

### Readiness verdict

**BADF against MAS-STD: `PARTIAL`. The governance layer meets or exceeds the standard. The runtime layers are absent by design.** Not production-ready as a MAS-STD runtime; it does not claim to be one.

- **What MAS-STD describes.** A runtime: a harness, loops, a bus, memory, sandboxes and tracing.
- **What BADF is (OBSERVED).** A deterministic record-and-check control plane:
  - docs/14 §1: "intelligence proposes and executes; deterministic controls authorize transitions";
  - AET-B design §5: "Deliberately absent: a scheduler, a coordinator runtime, model or cost routing".
- **Where BADF is ahead.** On the **Governance & Audit** layer and parts of **Observability/Evaluation** (log attestation), BADF is stricter than MAS-STD in five places:
  - composed-tree verification;
  - candidate-bound review;
  - a hash-chained effect state machine;
  - mutation-tested controls;
  - mandatory non-coverage.
- **Where BADF is absent.** On Harness, Context, Memory engine, Tool runtime, Tracing and Evals, BADF has doctrine but no mechanism, or nothing at all.

The 8-item production checklist scores **0 MET, 5 PARTIAL, 3 ABSENT** (§2.3).

A second readiness fact matters more than any clause.

- **The controls have no operational record.** S1, S3 and S2 are built, but the tree holds **0 review verdicts and 0 dispatch envelopes** on any work package. The only run ledger is `work/WP-2026-0010` (18 events), which predates the WP-0132 authority ratchet. Both are OBSERVED in `badf_gate.py repo` output.
- **So the AET's controls are proven by tests, not by use.** That is exactly AET-D's job. No MAS-STD upgrade should outrun it.

### Top 5 gaps, ranked by risk reduction per unit of effort

1. **The run-ledger schema contradicts the code it documents (OBSERVED defect).**
   - `scripts/badf_gate.py:140` `LEDGER_OUTCOMES` includes `AUTHORITY_CHECKED`, which is mandatory before `COMMITTED` from WP-0132 (`_validate_effect_chain`).
   - `schemas/run-ledger-event.schema.json` omits it from the `outcome` enum.
   - This session ran `check_schema("run-ledger-event", …)` on an `AUTHORITY_CHECKED` event and it was **refused**.
   - It is latent only because `read_ledger` never schema-validates. `tests/test_badf_schema_drift.py` `SHIPPED` does not include the ledger schema.
   - **S4 builds on this schema, so fix it first.** It is cheap.
2. **Declared budgets that nothing enforces (OBSERVED).**
   - `schemas/work-package.schema.json` `execution_budget` declares `max_elapsed_minutes` and `max_cost`.
   - `grep` finds **no reader** in `scripts/`. Only `max_attempts` is enforced (`_check_build_budget_and_stop`, `check_dispatch_envelope`).
   - These are guards that cannot fail (`docs/learnings/a-guard-that-cannot-fail-is-not-a-guard.md`).
   - There is no circuit breaker for identical failure, ping-pong or wall-clock.
   - These are MAS-STD Pillar 2 and checklist item 2, and they belong in **S4**.
3. **The handoff contract is incomplete** (§4.1).
   - The S2 envelope cannot express **read-only**. Both ACTIVE tools in `badf/tool-registry.json` (`local-filesystem`, `local-shell`) are `READ`+`WRITE`, and an envelope cannot narrow operations.
   - It cannot express a **time bound** or **timeout behaviour**, because `budget` is `additionalProperties:false` with only `max_attempts`.
   - It has no **trace correlation**.
   - It has no **single-focus** (one-owner) check across concurrent envelopes.
   - It has no **return/escalation record**.
4. **The tool registry does not conform to BADF's own docs/08 (OBSERVED).**
   - docs/08 §Registration requires each entry to name "timeout, rate limits".
   - Neither ACTIVE tool entry carries either, and `repo` does not check for them.
   - There is no typed tool-error contract. (MAS-STD's error shape is also **not** MCP's; see §6.)
5. **There are no identity-bound approvals, telemetry or trajectory evals.**
   - Approval `principal_type` is self-declared, with no signature or token (`validate_authority`).
   - All seats share one account (`docs/governance/IDENTITY_ATTRIBUTION.md` §1; #261).
   - There is no OTel, no secret scanning in CI (`.github/workflows/badf-gates.yml`), and no trajectory or span-level evals.
   - These are later-rung or human-reserved work (§4.3), but they bound every "tokenized HITL" and "zero-trust identity" claim.

**Recommended first move:** closing gap 1 needs a C1 work package. Then build **S4 as designed, extended** to close gap 2. Do this before any new component.

**What not to build:** see §5.3. In short: no scheduler, bus, mesh, vector store, second policy engine, persona catalogue, or score-threshold gate.

---

## 2. Clause-by-clause assessment

Legend:
- **MET**: an existing control.
- **PARTIAL**: what is missing is stated.
- **ABSENT**.
- **CONFLICTS**: doctrine is quoted.
- **N/A**: argued.

Every cite is OBSERVED in the repo at `b9936e5` unless marked otherwise.

### 2.1 The ten pillars

| # | Clause | BADF | Evidence / what is missing |
| :-- | :-- | :-- | :-- |
| **1 Harness** | Ephemeral, network-isolated sandbox (Wasm, gVisor, MicroVM) | **ABSENT** (as a BADF control) | `tool-registry.json` `local-shell.approval_mode: "sandbox-and-work-package"` is a declared string that nothing verifies. docs/09 says "constrain egress"; that is doctrine. The isolation conditions in `LEARNING_PLANE_TOOL_INTAKE.md` §5.1 are design for two PROPOSED tools only. The sandbox is the host's (for example, this session's container). BADF records no attestation of it. |
| | Virtual FS / env / time for deterministic reproduction | **PARTIAL**, and **exceeds** on source identity | Source and target identity are pinned exactly: `content_tree()`, `build_review_package()`, composition records, `git-baseline`/`git-staleness`, and evidence toolchain fields (docs/05). There is no capture of env or clock virtualization. |
| | Uncaught exceptions → structured payload | **PARTIAL** | `ValidationError` maps to `BADF GATE FAIL` exit 1. HELD is exit 3. `review-check` and `dispatch-check` return JSON dispositions. Stop codes are an enum (`work-package.schema.json` `stop_conditions`). There is no machine-readable error object with a `recoverable` flag. |
| **2 Loop** | Token budget | **ABSENT** | `max_cost` is declared in the work-package schema and never read (gap 2). |
| | Turn caps N≤25 single / N≤60 chain | **PARTIAL**; the number is a convention (§6) | BADF bounds **attempts**, not LLM turns. RETRY count ≤ `execution_budget.max_attempts` (`_check_build_budget_and_stop`). An envelope budget must be ≤ the work package's (`check_dispatch_envelope`). Exhaustion means `BLOCKED` (AET-I06). |
| | Convergence heuristics | **PARTIAL** (doctrine only) | docs/02: "After two materially similar failures, switch to root-cause diagnosis". AET-I06: "a repeated identical failure is not a new attempt". **Nothing computes failure identity.** |
| | Circuit breakers: ping-pong; same failed call >3; wall-clock SLA | **PARTIAL / ABSENT** | Same-failure: doctrine is **stricter** than MAS-STD (2 against >3) but unenforced. Ping-pong: absent. Wall-clock: `max_elapsed_minutes` is declared and unenforced. A recorded `STOP` does dominate (`_check_build_budget_and_stop`): **MET** for halting. |
| **3 Context** | Budget split (≤15% / ≤40% / ≤30% / ≥15%) | **N/A** as a BADF control; convention (§6) | Context allocation is a harness property invisible to a record-and-check plane. BADF's lever is *what is handed over*: a digest-bound brief (S2). |
| | Compaction and pruning of raw tool payloads | **PARTIAL** | docs/06: "Checkpoint before … context compaction". The 15 vendored context-engineering skills (`context-compression` and others) are `IMPLEMENTED`, not routed (`skill-registry.json`). There is no mechanism. |
| **4 Tools** | MCP or typed JSON-RPC/Pydantic | **PARTIAL** | Governance is **MET**: `mcp-registry.json` is `default_policy: deny` with 0 servers, and docs/08 sets operation classes READ/WRITE/DESTRUCTIVE/ADMIN. No typed tool contracts are recorded (no input-schema digest per tool). |
| | Atomic tools, <5 required fields | **N/A**; convention | Tool design guidance. The `tool-design` skill is IMPLEMENTED. It is not a control-plane property. |
| | Typed errors `{status, error_code, message, recoverable}` | **ABSENT**; also **not MCP-conformant** | MCP 2026-07-28 uses `isError: true` plus content, or JSON-RPC errors (§6). |
| **5 Memory** | L1 working | **PARTIAL** (doctrine) | docs/04 tier "Working context … Session … Authority: None". |
| | L2 episodic (vector + BM25, success/failure metadata) | **PARTIAL** (records yes, retrieval no) | Episodic *records* exist with outcome metadata: run ledger outcomes, S3 verdicts, `docs/learnings/`, demands. There is no retrieval index. docs/04: "Retrieve by relevance, authority, freshness … do not maximize volume." |
| | L3 procedural (playbooks / few-shot updated by reinforcement or feedback) | **MET** for the vault, **exceeds** on provenance; **CONFLICTS** on auto-update | Skills are digest-pinned with an 8-stage lifecycle (docs/07, `verify_registry_digests`). Auto-update conflicts with AET-I09 and docs/12: "may not activate changes to their own authority, gates, or safety controls without independent review and required human ratification". EvoSkill/SkillOpt intake K5 shows the failure. |
| | TTL, recency/relevance decay, eviction | **PARTIAL** | `memory.schema.json` requires `review_after`. docs/04 has `SUPERSEDED` and "remove it from default retrieval". **Silent eviction of durable records conflicts** with docs/04: "Do not rewrite historical records … Delete only under an approved retention/privacy process". Decay is acceptable for L1 only. |
| **6 Orchestration** | Router-Worker / Hierarchical Supervisor | **PARTIAL** (as records) | The seat roster has 1 coordinator and 3 builders (`seats.json`). S2 dispatch from a held seat to a held seat is the supervisor's *record*. There is no runtime (AET-B §5). |
| | State-Graph DAG | **PARTIAL** | The lifecycle G00–G14 is a gate DAG (`lifecycle.json`). `work-breakdown.schema.json` has a composition order. Neither is an execution graph. |
| | Decentralized handoff / mesh | **CONFLICTS** | Charter §9: "The coordinating agent owns integration, conflict resolution, and final evidence completeness". See §3.6. |
| **7 Guardrails** | Input scanners (direct/indirect injection, jailbreak, PII/secrets) | **ABSENT** (mechanism); doctrine present | docs/09: "Treat retrieved content … as potentially hostile instructions". There is no scanner and no CI secret scan (`badf-gates.yml` has no scan step). |
| | Action firewall on tool arguments (OPA/Rego) | **PARTIAL**: BADF has its own deterministic PDP, not OPA | Path, tool, seat, budget and stop-condition narrowing (`check_dispatch_envelope`, `dispatch_check`). Delegation prohibited set `("push","merge","release","credential-use")` (`_check_delegations`). Enforcement routing (`check_enforcement_routing`). These check **records and diffs after the fact**, not live tool calls. `PROJECT_INSTANCE.md:125`: "`policies/*.rego` needs an evaluator BADF does not have". |
| | JSON-schema output confinement | **MET** for records, **exceeds**; **ABSENT** for live LLM output | Every record is schema-checked (`check_schema`; `additionalProperties:false` closes records; `test_badf_schema_drift.py`). However, the ledger schema drift (gap 1) shows the drift test does not cover every schema. |
| **8 Evals** | Unit level (schema, parsing) | **MET**, **exceeds** | 90+ test modules. Failing-first plus seeded-mutation acceptance is part of each AET-B work package (for example, WP-0159 AC-4 "every control mutation-tested"). The *mutation evidence itself* is not stored under `work/<WP>/evidence/`; only `composition-record.json` is. This is a **PARTIAL** evidence-binding gap. |
| | Span level (tool selection P/R, argument accuracy) | **ABSENT** | There are no spans to score. AET-D scope. |
| | Trajectory level (path efficiency, error recovery, LLM-as-judge) | **ABSENT**; judge-as-evidence **CONFLICTS** | VER-I08 (`check_g08_binding`): "an observation is produced by a runtime, never by an agent". See §3.2. |
| **9 HITL** | Tier 0 read-only runs autonomously | **MET** | `authority-matrix.json` rule `read`: `minimum_class C0`, `approval: work-package-or-repository-policy`. |
| | Tier 1 reversible runs autonomously with audit | **CONFLICTS** as worded | `write-repository` is C1 with `approval: work-package`, and C1 landing needs `engineering_owner` + `independent_reviewer`. See §3.4. |
| | Tier 2 irreversible needs mandatory human approval | **MET**, **exceeds** in scope | `human_reserved_roles` must be `principal_type: human` (`validate_authority`, BADF-DEC-0003). `destructive-or-admin` → C3 `explicit-human`. BADF also reserves governance edits (S1), not only irreversible ones. |
| | Suspend at Tier 2 with durable serialized state plus an approval ticket | **PARTIAL** | Durable state: ledger `PREPARED`/`AUTHORITY_CHECKED`, `replay_run`, `plan_next_effect` → `RECONCILE_FIRST`. HELD exit 3 on dossier, review and dispatch. There is **no approval-ticket object** and no `WAIT_FOR_AUTHORITY` resume state; that is S4 as designed. |
| | Resume only on a signed approval token | **ABSENT** | Approvals are JSON with a self-declared `principal_type`. There is no signature (`grep signature` finds lockfile-only uses). Identity is unsolved (#261, `IDENTITY_ATTRIBUTION.md` "structural half is NOT implemented"). |
| **10 Tracing** | OTel trace per run, span per LLM step / retrieval / tool call / handoff | **ABSENT** | No OTel anywhere (`grep -i otel\|traceparent` finds only a git-recovery reference). |
| | Context propagation across async boundaries | **PARTIAL** (correlation, not propagation) | AET-I08: work correlates `work_package_id`, session, run, gate, base/head SHAs and content trees. Run ids appear in S3 verdicts and the S2 `issued_by_run_id`. There is no W3C `traceparent`. |
| | Token, latency and cost per span | **ABSENT** | |
| | (Observability layer) Log attestation | **MET**, **exceeds** | Hash-chained, append-only ledger (`read_ledger`, `_event_hash`). The effect state machine refuses double commit (`_validate_effect_chain`, #294). The lockfile is over governance paths (`verify_integrity`). |

### 2.2 The handoff contract

The field-by-field diff against S2 is in §4.1.

| Clause | BADF | Evidence / gap |
| :-- | :-- | :-- |
| Typed JSON handoff | **PARTIAL** | `schemas/dispatch-envelope.schema.json` (closed, typed) plus `check_dispatch_envelope`. 4 of 8 MAS fields have no carrier (§4.1). |
| Rule 1: exactly one owner holds focus | **PARTIAL** | One `seat` per envelope, HELD, and a reviewer seat ≠ the dispatched seat. **No check refuses two open envelopes with overlapping `allowed_paths` for different seats.** Charter §9 forbids that ("must not edit overlapping files unless a designated integrator coordinates them"), but no code enforces it. |
| Rule 2: pass a state slice, never the full context | **PARTIAL**; stronger in kind | The brief is a separate `.md` bound by sha256 digest under `work/<WP>/dispatch/`. Paths are narrowed to ⊆ `expected_surfaces`. Nothing bounds the brief's size or content. AET-B §2.4 records a 42k-character pasted dispatch, 99% of it history, as the failure this guards against. |
| Rule 3: the target returns a validated completion or an explicit escalation code | **PARTIAL**; stronger in kind | `dispatch_check` reads the **actual diff** rather than a self-report: out-of-envelope changes are refused (exit 1), and the result is `COMPLETE` (0) or `HELD` on review (3). There is **no return record from the target** carrying `ESCALATED(<stop code>)` or `BLOCKED`. That record is S5's closing contract. |

### 2.3 The production checklist

| # | Item | BADF | Note |
| :-- | :-- | :-- | :-- |
| 1 | Hard guardrails on all entry points | **PARTIAL** | The repository entry point (PR → CI) is hard-gated: `repo`, unittest, PR traceability and composed-tree verification (`badf-gates.yml`). There are no input guardrails on agent entry points. |
| 2 | Deterministic loops with max N and circuit breakers | **PARTIAL** | Max attempts are enforced. There are no breakers, and wall-clock and cost are unenforced (gap 2). |
| 3 | Shell and code sandboxed in containers | **ABSENT** (as a BADF control) | Host-provided, not attested. |
| 4 | Idempotent mutating tools | **PARTIAL**, **exceeds** on the record | AET-I05; `idempotency_key` in the ledger; `plan_next_effect` → `SKIP_ALREADY_COMMITTED`; double commit is refused. No tool is *certified* idempotent. |
| 5 | HITL at durable checkpoints with tokenized review | **PARTIAL** | Human-reserved roles and the durable ledger exist. There is no token or signature. |
| 6 | Full OTel with token costs | **ABSENT** | |
| 7 | Trajectory benchmarks ≥85%, including synthetic tool-error recovery | **ABSENT**; the threshold **CONFLICTS** with gate semantics | §3.5. |
| 8 | Zero-trust scoped service identities with task-lived credentials | **PARTIAL** (doctrine and specification only) | docs/08: "prefer OAuth or short-lived environment-injected tokens". `IDENTITY_ATTRIBUTION.md` specifies `bst-sa-agent[bot]` with merge-only scope. It is **not implemented**. |

**Tally:** 0 MET, 5 PARTIAL, 3 ABSENT.

### 2.4 Where BADF exceeds MAS-STD (OBSERVED)

MAS-STD has no counterpart for any of these. A MAS-STD-compliant system could still land unverified code; BADF could not.

| Control | Where | Why it is beyond the standard |
| :-- | :-- | :-- |
| Composed-tree verification | `check_g08_dossier` C7; `badf_compose.py`; CI step "Composed-tree verification" | MAS-STD evaluates trajectories. BADF refuses a pass unless the **tree that would land** was tested ("source-head success is not composed verification", VER-I15). |
| Candidate-bound review with staleness | S3: `build_review_package`, `check_review_verdict`, `review_check` | A verdict binds the package digest, the author run must not equal the reviewer run, and a moved head makes it `STALE`. MAS-STD has LLM-as-judge with no binding. |
| No-self-approval by construction | `validate_authority` (author not among approvers; distinct principals per role); S3 run-id inequality | MAS-STD's HITL tiers do not address self-approval. |
| Effect state machine on a hash chain | `_validate_effect_chain`, `read_ledger` | Refuses PREPARED→COMMITTED→PREPARED→COMMITTED. MAS-STD asks for "immutable session state" but not effect-level exactly-once semantics. |
| Enforcer not editable by the enforced | S1 `ENFORCEMENT_SURFACES` pinned in code → C3, human-reserved | MAS-STD's guardrails are silent on who may edit the guardrails. |
| Monotonic authority | `verify_monotonic_authority` | A downgrade of the authority matrix needs a decision record. |
| Mandatory non-coverage | `check_non_coverage`; G08 C5; S3 verdict `non_coverage` | "No findings is not correctness." MAS-STD's evals report scores, not what they did not observe. |
| Mutation testing of the controls themselves | AET-B work packages' acceptance criteria | MAS-STD tests the agent. BADF tests the guards. |

---

## 3. Doctrine conflicts and recommendations

### 3.1 "Consensus / vote" against AET-I03 and the council rules

- **BADF (OBSERVED):**
  - AET-I03: "Coordinator, council, skill and LLM output … is never authority."
  - docs/03: "Majority does not override a mandatory blocking finding or reserved human authority."
  - `verify_council`: "a council REJECT does not refuse the dossier -- it is evidence for the human authority, not a veto. A council APPROVE satisfies no approval quorum."
  - Ballots must be `sealed` and one per principal.
- **Recommendation: ADAPT.**
  - Keep consensus as a **sealed, independent, advisory input** that BADF already implements: docs/03 council protocol and `G08_QUORUM` (C2: 2, C3: 3 distinct reviewers *and* runs, plus mandatory lenses).
  - **Reject** vote-as-decision. A majority vote that moves a gate would let agent agreement stand in for evidence and authority.
- **Why.** Agents that share a model and inputs are not independent voters. bERP ADR-0001 (AET-B §1.1): "the same model with a different instruction file … gives no extra expertise". Counting them would launder correlated error into apparent quorum.

### 3.2 LLM-as-a-judge as evidence

- **BADF (OBSERVED):**
  - VER-I08 in `check_g08_binding`: "a typed … observation carries producer.type 'agent'; a claimed result is not an observation".
  - `LEARNING_PLANE_TOOL_INTAKE.md` K5 records a bare score comparison in which "the same model mines tasks, writes rubrics, edits and judges".
- **Recommendation: ADAPT. Judges may produce *findings* and *learning-plane measurements*, never evidence or gate outcomes.**
  - **As a reviewer.** An LLM judge may author an S3 verdict (`principal_type: agent`, distinct `reviewer_run_id`, findings plus non-coverage). Its findings are challenges that a deterministic check or a human must resolve.
  - **As an eval metric (AET-D).** Use only with:
    - a judge model different from the actor;
    - a held-out set the actor never saw, identified by digest;
    - the inter-rater agreement against human labels reported.
  - **Never** as `producer` of a G08/G09 observation, and never as the sole basis of any rung admission.
- **Why.** A judge's score is an output, and outputs are not authority (AET-I03). Deterministic checkers (does the test pass on the composed tree?) are available for most engineering trajectories and should be preferred.

### 3.3 Personas against docs/14 §3 and bERP ADR-0001

- **BADF (OBSERVED):**
  - docs/14 §3: "never as a standing swarm".
  - AET-B §2.2: "Roles are bounded by tools and context, not by persona".
  - §4: "Persona teams and standing swarms" are explicitly not adopted.
  - `docs/learnings/an-agent-team-is-bounded-by-tools-and-records-not-personas.md`: "What a role adds is restriction."
- **Recommendation: REJECT personas as a capability or role mechanism. ADAPT "system prompts" as the S2 brief.** The brief is digest-bound, scoped to one dispatch, and recorded. A seat's role is enforced by **tool and path narrowing** plus the record it must leave, never by prompt text.
- **Prerequisite.** This needs gap 3's read-only tool, so that a reviewer seat's restriction is expressible.

### 3.4 Tier 1 "autonomous with audit" against the authority matrix

- **BADF (OBSERVED):**
  - `write-repository` needs `approval: work-package` (C1 minimum).
  - C1 landing needs `engineering_owner` + `independent_reviewer`.
  - Class is "the maximum severity across affected surfaces. Ambiguity selects the higher class" (docs/00).
  - S1 makes any enforcement-surface edit C3, however reversible the edit is.
  - `_require_authorized_demand`: a demand must be AUTHORIZED by a human before mutation (BLD-I03).
- **Recommendation: ADAPT. "Pre-authorized, not post-audited."**
  - **Execution** inside an authorized work package and a valid S2 envelope runs without per-action approval. That is the legitimate core of Tier 1, and BADF already permits it.
  - **Landing** still requires independent review (S3) and the class's roles. Audit-only landing is **rejected**.
  - Reversibility is one **input** to class (`compute_council_disposition` "irreversible"), not the classifier. A reversible edit to `badf_gate.py` is still C3.
- **Why.** MAS-STD keys autonomy on reversibility of the *effect*. BADF keys it on the *authority surface touched*. A reversible change to the guard can disable every later guard: AET-B F1, biztrust R7-4.

### 3.5 The ≥85% trajectory benchmark against fail-closed gates

- **BADF (OBSERVED):**
  - Charter §3: "Fail closed: missing, ambiguous, stale, unverifiable, or contradictory evidence blocks progression".
  - Gates are conjunctive per control (docs/02, "Done is conjunctive").
  - docs/10: "Coverage is a diagnostic, not proof".
- **Recommendation: REJECT 85% as a gate or admission threshold. ADAPT benchmarks as AET-D shadow measurements.**
  - Each benchmark record carries a dataset digest, a held-out split, a confidence interval and a per-failure-class breakdown.
  - Any admission threshold for AET-E is set by the human authority in their own channel (AET-I13), per class of failure.
  - **Destructive-scope and authority-violation failures must be 0%, not ≤15%.**
- **Why.** An aggregate rate lets a 15% tail include the failure classes BADF treats as absolute stops (`AUTHORITY_CONFLICT`, `CREDENTIAL_EXPOSURE`, `UNEXPECTED_DESTRUCTIVE_SCOPE`). The 85% figure is a convention (§6). It is not a requirement of any spec examined.

### 3.6 Decentralized mesh against "exactly one owner"

- **BADF (OBSERVED):** Charter §9: "Parallel agents must not edit overlapping files unless a designated integrator coordinates them … The coordinating agent owns integration". The SARCHI seat: "Decomposition, ordering, integration, dispatch".
- **Note (INFERRED).** MAS-STD contradicts itself here. Its Pillar 6 offers a "Decentralized Mesh", while its own handoff rule requires "exactly one owner holds focus at a time".
- **Recommendation: REJECT mesh. ADAPT "decentralized handoff" only as sequential baton-passing.** Each transfer is an S2 envelope plus a return record (S5), with **one recorded focus holder per path set**. The missing overlap check (§2.2 Rule 1) is the control that makes this true.

---

## 4. Mapping to S4, S5 and AET-C/D/E

### 4.1 Does the S2 dispatch envelope already cover the typed handoff contract?

No. It covers the authority-bearing half better than MAS-STD, and lacks the runtime half.

| MAS-STD field | S2 envelope (`dispatch-envelope.schema.json`) | Status |
| :-- | :-- | :-- |
| `handoff_id` | `id` (`^DSP-[0-9]{2,}$`); file name = id (`load_dispatch_envelopes`) | **MET** |
| `source_agent` | `issued_by_run_id`: a *run*, not a seat | **PARTIAL**. No `source_seat`, so "seat X dispatched to seat Y" is not checkable |
| `target_agent` | `seat`: must be rostered and `HELD` | **MET**, stronger |
| `task` | `brief.path` + `brief.digest` (sha256; edit-after-dispatch refused) | **MET**, stronger |
| `context_slice` | The brief **is** the slice. `allowed_paths` ⊆ WP `expected_surfaces.files`; a new glob is refused | **PARTIAL**. No structured slice (no evidence-id references) and no size bound |
| `constraints.read_only` | No carrier. `allowed_tools` names tools, not operations. Every ACTIVE tool is READ+WRITE | **ABSENT, and not expressible today** |
| `constraints.max_execution_time_seconds` | No carrier. `budget` is closed to `max_attempts`. The WP's `max_elapsed_minutes` is unenforced | **ABSENT** |
| `constraints.timeout_behavior` | No carrier. Nearest: the `BUDGET_EXHAUSTED` stop condition → BLOCKED (AET-I06) | **ABSENT**. If added, restrict to `{BLOCK, ESCALATE}`; never `CONTINUE` or `EXTEND` (AET-I06: "never an autonomous extension") |
| `trace_parent` | No carrier. Correlation is via `work_package_id` + `base_sha` + `issued_by_run_id` (AET-I08) | **ABSENT** |
| *(BADF only)* | `base_sha`, `allowed_paths`, `allowed_tools`, `budget`, `stop_conditions` (⊇ WP's), `required_evidence` (non-empty), `review` (reviewer ≠ dispatched seat), `recorded_at` | MAS-STD has no non-widening, evidence or review fields |

### 4.2 S4 and S5 as already designed

**S4: budget and resume on the run ledger.** AET-B §5: attempt events; "An interrupted attempt counts"; an unverifiable counter yields `BLOCKED`; resume ends in `CONTINUE / BLOCKED / WAIT_FOR_AUTHORITY / RECOVERY_REQUIRED / COMPLETE`.

| Disposition | MAS-STD clauses |
| :-- | :-- |
| **Fits S4 as designed** | Pillar 2 attempt bounds and termination invariants; Pillar 9 "suspend … durable serialized state" and "resume" (`WAIT_FOR_AUTHORITY`); checklist 2 (partly) and 5 (the durable-checkpoint half); State & Memory "checkpoint and replay" (`replay_run` exists) |
| **Fits S4 if extended** (same component, same ledger; recommended) | **Wall-clock and cost budgets:** enforce `max_elapsed_minutes`/`max_cost` or remove them. **Identical-failure circuit breaker:** a failure fingerprint (step + normalized error + input digest); the second identical failure is refused per docs/02, stricter than MAS-STD's >3. **Approval-ticket event:** `AUTHORITY_REQUESTED` with the ticket id, resolved only by a human-principal approval record. **Ping-pong detector:** an A→B→A→B envelope cycle on the same path set with no diff progress |
| **Precondition for S4** | Fix the ledger schema/code drift (gap 1) |

**S5: rulings and closing contract.** AET-B §5: findings not fixed are recorded as "what — why — cost if wrong"; a session closes with status, decisions needed and next safe action.

| Disposition | MAS-STD clauses |
| :-- | :-- |
| **Fits S5 as designed** | Handoff Rule 3: the closing contract, extended per dispatch as a **return record** `COMPLETE` / `ESCALATED(<stop code>)` / `BLOCKED`, validated against the envelope and the ledger |
| **Fits S5 if extended** | Pillar 1 structured error payloads at loop end: a typed stop/error record (`code`, `recoverable`, `stop_condition`, `evidence_ref`) |

### 4.3 New AET-B components, later rungs, and a runtime BADF does not have

| Bucket | MAS-STD clauses | Rationale |
| :-- | :-- | :-- |
| **New AET-B components** (records and checks only; each a separately governed work package) | **S2.1 handoff completion:** `source_seat`, `max_elapsed_seconds` ≤ WP, `timeout_behavior` ∈ {BLOCK, ESCALATE}, optional W3C `trace_parent` (format-validated, correlation only), `read_only` *derived* from tool operations, and a **single-focus overlap check**. **S6 tool contract registry:** docs/08 conformance (timeout, rate limit, operations); per-operation registration so a read-only capability exists; input-schema digest; mapping of MCP `isError` and JSON-RPC errors to ledger outcomes. **S7 correlation-to-telemetry map:** a document plus validator. The `work_package_id`/run/DSP ids map to OTel GenAI attributes at a pinned semconv revision. No exporter | Each changes **what is recorded, never what is permitted**, which is the AET-B §5 rule |
| **AET-C** (deterministic controls validated) | Failing-first and mutation evidence for every control above. Store **mutation evidence as an artifact under `work/<WP>/evidence/`**; today it lives only in acceptance criteria and PR prose | docs/14 §8 |
| **AET-D** (self-build shadow) | Pillar 8 span- and trajectory-level evals; MAS-STD's synthetic tool-error recovery tests; context-budget *measurement* (not gating); OTel export in shadow; judge-based metrics per §3.2 | "shadow grants no authority and its measurements are frozen as captured" (docs/14 §8) |
| **AET-E** (admission; C3; human in their own channel) | Unattended or scheduled operation; Tier-1 execution without a seated operator; admitting a sandbox runtime as an *attested* execution environment; any benchmark threshold | AET-B F4: "Scheduled autonomy is AET-E admission scope" |
| **Human-reserved, across rungs** | Signed approval tokens and zero-trust identities (checklist 5 and 8) | Depends on #261 identity provisioning by an operator; `modify-authority-policy` is a reserved action |
| **Runtime BADF deliberately lacks** (host or harness responsibility; BADF records an attestation, never reimplements) | Reason-act loop, context compaction, memory engine (vector/BM25), A2A bus, orchestration topologies, input scanners, Wasm/gVisor/MicroVM sandboxes, an OPA PEP on live tool calls | AET-I12: "no seat, adapter or profile introduces a second validator, competing lifecycle engine or agent-side approval logic". AET-B §4: "A second validator or lifecycle engine" is not adopted. An OPA engine in the harness is admissible **only** as a runtime enforcement point (PEP) whose policy bundle is a governed artifact. `badf_gate.py` stays the sole decision point for transitions |

---

## 5. Roadmap of candidate work packages (PROPOSED)

The ids `CAND-01…` are placeholders. **None is claimed or authorized.** Each needs a human-authorized demand (BLD-I03) and its own work package.

The class rule applies throughout. Under S1 (`ENFORCEMENT_SURFACES`), anything touching these files is **C3**, whose required roles are human-reserved:
- `scripts/badf_gate.py`, `badf_compose.py`, `check_pr_traceability.py`;
- `.github/workflows/badf-gates.yml`;
- `AGENTS.md`;
- `badf/authority-matrix.json`, `lifecycle.json`, `seats.json`;
- `docs/14-agentic-engineer-team.md`.

### 5.1 Sequenced candidates (ordered by risk reduction per unit of effort)

| # | Candidate | Objective → MAS-STD clauses closed | Class | Depends on | Failing-first test idea | Risk / human-reserved |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | **CAND-01: ledger schema/code reconciliation** | Add `AUTHORITY_CHECKED` to `run-ledger-event.schema.json`, and add the ledger schema to `test_badf_schema_drift.py` (assert that `LEDGER_OUTCOMES` equals the schema enum). Closes gap 1 and protects S4. Clauses: State "immutable session log" integrity | **C1** (schema + test; no enforcement surface) | none | A test that schema-validates a WP-0132+ ledger containing `AUTHORITY_CHECKED`. **Already demonstrated failing in this session** | Low. Nothing human-reserved |
| 2 | **CAND-02: S4 budget and resume, extended** | AET-B S4 as designed. Plus: enforce or remove `max_elapsed_minutes`/`max_cost`; an identical-failure breaker (the 2nd identical failure → BLOCKED); a ping-pong detector; an `AUTHORITY_REQUESTED` ticket event → `WAIT_FOR_AUTHORITY`. Clauses: Pillar 2 (all), Pillar 9 suspend/resume, checklist 2, 5 (partly) | **C3** (`badf_gate.py`) | CAND-01 | An interrupted attempt does not reduce the count. A ledger whose elapsed time exceeds budget is refused. Two identical failure fingerprints → BLOCKED. Mutation: drop each check and the test must fail | Medium. The human sets budget values per work package; exhaustion is never auto-extended |
| 3 | **CAND-03: tool registry conformance and operation-level grants** (S6) | Meet docs/08 fields (timeout, rate limit). Register a READ-only capability. Let an envelope narrow operations; `read_only` is derived. Map MCP errors to ledger outcomes. Clauses: Pillar 4, handoff `read_only`, checklist 4 (registry half) | Registry edits C1/C2; the gate check is **C3** | CAND-01 | `repo` refuses an ACTIVE tool without a timeout (fails today). An envelope for the reviewer seat that grants WRITE is refused when `read_only` is required | Medium. Activating any MCP server stays a separate work package with security approval |
| 4 | **CAND-04: S2.1 handoff completion** | Add `source_seat`, `max_elapsed_seconds`, `timeout_behavior` ∈ {BLOCK, ESCALATE}, and optional `trace_parent`. Refuse **overlapping `allowed_paths` across open envelopes** for different seats unless an integrator is named. Clauses: handoff fields, Rule 1 | **C3** | CAND-02, CAND-03 | Two open envelopes on the same path for different seats → refused (fails today). `timeout_behavior: CONTINUE` → refused by the schema | Medium. Who may be an integrator is a seat question; seat changes are C3 |
| 5 | **CAND-05: S5 rulings, closing contract and dispatch return record** | AET-B S5 plus `DSP-NN.return.json` (`COMPLETE` / `ESCALATED(code)` / `BLOCKED`), validated against the envelope and the ledger. Typed stop/error payload. Clauses: Rule 3, Pillar 1 structured errors | **C3** | CAND-04 | A return claiming COMPLETE while `dispatch-check` reports out-of-scope or HELD → refused | Medium. Rulings that accept risk stay with the named authority |
| 6 | **CAND-06: mutation evidence as an artifact** | Store each control's seeded-mutation results under `work/<WP>/evidence/` with a digest, and let the self-dossier read them. Clauses: Evals unit level (evidence binding). AET-C precondition | C1 if evidence-only; **C3** if the gate reads it | none | A work package that claims an "every control mutation-tested" acceptance criterion with no artifact → flagged | Low |
| 7 | **CAND-07: secret scanning in CI** | Add a pinned, licence-reviewed scanner step. Clauses: Pillar 7 secrets, checklist 1 | **C3** (workflow) plus dependency review (charter §13) | none | A fixture commit with a synthetic token pattern fails the job | Medium (supply chain). Security authority approves the tool |
| 8 | **CAND-08: correlation → OTel mapping spec** (S7, doc plus validator) | Map WP/run/DSP/REV ids to OTel GenAI agent-span attributes at a **pinned** semconv revision (status: Development). No exporter, no runtime. Clauses: Pillar 10 (design), checklist 6 (design) | C0 (doc) / C1 (validator) | CAND-04 | Validator rejects a malformed `trace_parent` (W3C format) | Low. Must not imply that tracing exists |
| 9 | **CAND-09: AET-D shadow eval design** | Trajectory metrics, synthetic tool-error injection, a held-out set by digest, judge independence per §3.2, reporting by failure class. **No thresholds as gates.** Clauses: Pillar 8, checklist 7 (measurement only) | C2 (design); its rung admission is **C3** | AET-C reached | n/a (design); later, frozen shadow captures | High if misused as admission. Thresholds are human-reserved at AET-E |
| 10 | **CAND-10: identity-bound approvals** | Operate the #261 identity split. Approval records carry a verifiable signature or token. Clauses: Pillar 9 signed token, checklist 5, 8 | **C3** and **human-provisioned** | #261 operator action | An approval whose signature does not verify for the named human principal → refused | High. Credential handling is a reserved action (`handle-production-credentials` class) |

**Effort and ordering notes (INFERRED).**
- **CAND-01 is hours of work.** It removes a latent contradiction in the substrate that S4 extends.
- **CAND-02 delivers the most standard coverage per work package.** It is already designed and closes most of Pillar 2 and Pillar 9.
- **CAND-03 must precede CAND-04.** `read_only` cannot be derived from a registry that has no read-only capability.
- **CAND-09 and CAND-10 are rung-gated and identity-gated.** No engineering effort can pull them earlier.

### 5.2 What stays human-reserved

These stay human-reserved throughout:
- every C3 work package above (`human_sponsor`, `security_authority`, `release_authority` must be `principal_type: human`);
- dispositioning #261;
- any AET-C/D/E rung opening;
- any benchmark or eval threshold;
- activating any MCP server or the PROPOSED learning-plane tools;
- any change to `ENFORCEMENT_SURFACES`.

No council result, judge score or agent agreement substitutes for any of these.

### 5.3 What NOT to build

| Do not build | Why |
| :-- | :-- |
| A scheduler, coordinator runtime or agent bus (A2A) inside BADF | AET-B §5 "Deliberately absent"; F4; AET-E scope |
| A decentralized mesh topology | §3.6; charter §9 |
| OPA/Rego as a second decision point for gates | AET-I12 one canonical gate. OPA is admissible only as a harness-side PEP under a governed policy bundle |
| A vector/BM25 memory engine inside the control plane | docs/04 retrieval rules; "Memory is not authority" (charter §3). A host concern |
| Persona catalogues or a standing swarm | docs/14 §3; AET-B §4 |
| Gates on context-budget percentages, turn counts N≤25/60 or tool field counts | Conventions, not invariants (§6); invisible to a record plane; they would be guards that cannot fail |
| An LLM-judge or benchmark-threshold gate (including ≥85%) | §3.2, §3.5; AET-I03; VER-I08 |
| Auto-updating procedural memory or skills | AET-I09; docs/12; intake K5/K6 |
| "Tier 1 autonomous landing" | §3.4 |

---

## 6. External verification (dated 2026-10-04)

| Spec | Finding | Label | Source |
| :-- | :-- | :-- | :-- |
| **OTel GenAI semconv** | The docs page says GenAI conventions "have moved to the OpenTelemetry GenAI semantic conventions repository" | OBSERVED | [opentelemetry.io/docs/specs/semconv/gen-ai](https://opentelemetry.io/docs/specs/semconv/gen-ai/) |
| | The agent-spans page carries status **"Development"**. It defines `create_agent`, `invoke_agent` (client and internal), `invoke_workflow`, `plan`, `execute_tool`, `load_skill`, `read_skill_resource`, `command_execution`. It references `gen_ai.usage.input_tokens`/`output_tokens`. **No cost attribute was found on that page** | OBSERVED (via fetch summary) | [semantic-conventions-genai/…/gen-ai-agent-spans.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md) |
| | "Every gen_ai.* attribute … carries … Development"; the move happened at semconv v1.42.0 (12 Jun 2026) | **UNVERIFIED** (secondary blogs) | [dev.to/azena-ai](https://dev.to/azena-ai/opentelemetrys-genai-semantic-conventions-are-not-stable-yet-heres-what-actually-shipped-in-2026-3mke); [praesidia.ai](https://praesidia.ai/blog/opentelemetry-genai-semantic-conventions-status) |
| | **Implication:** MAS-STD's "per-span cost attribution" has no standard attribute. Cost must be derived from tokens times a price table, which is a BADF-side convention. Any mapping (CAND-08) must pin a semconv revision because the conventions are not stable | INFERRED | — |
| **MCP** | Current spec revision **2026-07-28** | OBSERVED | [modelcontextprotocol.io/specification/latest/server/tools](https://modelcontextprotocol.io/specification/latest/server/tools) |
| | Tool errors come in two kinds. **Protocol errors** are JSON-RPC errors (for example `-32602`). **Tool execution errors** are a result with `isError: true` and content. There are **no `error_code` or `recoverable` fields** | OBSERVED | same |
| | `outputSchema` with `structuredContent` ("Servers MUST provide structured results that conform"; "Clients SHOULD validate") | OBSERVED | same |
| | "clients MUST consider tool annotations to be untrusted unless they come from trusted servers"; "there SHOULD always be a human in the loop with the ability to deny tool invocations" | OBSERVED | same. Consistent with docs/08 ("approval mode does not replace BADF authority") |
| | **Implication:** MAS-STD's `{status:error, error_code, message, recoverable}` is a convention layered *over* MCP, not MCP's shape. CAND-03 should map MCP's two error kinds onto BADF ledger outcomes rather than adopt the MAS shape on the wire | INFERRED | — |
| **A2A** | Latest released version **1.0.0**. Task states are `TASK_STATE_SUBMITTED`, `WORKING`, `COMPLETED`, `FAILED`, `CANCELED`, `INPUT_REQUIRED`, `REJECTED`, `AUTH_REQUIRED`. There are `contextId`, Message/Part/Artifact | OBSERVED (via fetch summary) | [a2a-protocol.org/latest/specification](https://a2a-protocol.org/latest/specification/) |
| | **No** `read_only`, `max_execution_time`, `timeout_behavior` or trace-propagation fields in the core handoff | OBSERVED absent in the fetched content; full-spec absence **UNVERIFIED** | same |
| | Governance: the page mentions "A2A joins the Agentic AI Foundation" | **UNVERIFIED** | same |
| | **Implication:** MAS-STD's handoff `constraints` block is its own convention, not A2A's. If an A2A interop shim is ever wanted (AET-E or later), `INPUT_REQUIRED`/`AUTH_REQUIRED` correspond to BADF's `WAIT_FOR_AUTHORITY`/HELD, and `REJECTED` to a refused envelope | INFERRED | — |
| **OPA** | CNCF **graduated** | OBSERVED | [openpolicyagent.org/docs](https://www.openpolicyagent.org/docs) |
| | Latest release **v1.21.1, 2026-09-29** | OBSERVED (via fetch summary) | [github.com/open-policy-agent/opa/releases](https://github.com/open-policy-agent/opa/releases) |
| | Rego v1 syntax has been the default since OPA 1.0 | **UNVERIFIED** (not confirmed on the fetched pages; from background knowledge) | — |
| **Sandbox runtimes** (Wasm, gVisor, Firecracker/MicroVM) | Not assessed | **NOT_RUN** | — |

**Conventions, not spec requirements (INFERRED).** None of the specifications read (OTel GenAI agent spans, MCP 2026-07-28 tools, A2A 1.0.0, OPA docs) states any of the following:
- turn caps N≤25 / N≤60;
- "same failed tool call >3";
- the context split 15/40/30/15 %;
- "<5 required fields";
- the `{status, error_code, message, recoverable}` error shape;
- the ≥85% benchmark threshold;
- the Tier 0/1/2 taxonomy.

These are MAS-STD's own engineering conventions. BADF should treat them as tunable defaults for the AET-D shadow, not as invariants. Where BADF doctrine is stricter (two similar failures, docs/02; 0% tolerance for stop-code classes), the stricter rule stands.

---

## 7. Checks run in this session

| Check | Command | Result | Evidence |
| :-- | :-- | :-- | :-- |
| Repository governance (session checkout) | `python3 scripts/badf_gate.py repo` in `/home/user/badf` | **FAIL**: "WP-2026-0016 claims landed_as 12f5056… which is not a commit in this repository". **Cause:** the session checkout is a shallow clone (`git rev-parse --is-shallow-repository` → `true`; 50 commits). This is environmental, not a repository defect | session scratchpad `repo.log` |
| Repository governance (full clone at `b9936e5`) | same, in a full clone in the session scratchpad | **PASS** (`BADF GATE PASS: repo`, exit 0) | scratchpad `full-repo.log` |
| Unit tests (session checkout) | `python3 -m unittest discover -s tests -p 'test_*.py'` | **BLOCKED**. The run was on a shallow clone, and its progress showed `F` markers alongside shallow-root warnings (`rejected b9936e5 … shallow roots are not allowed to be updated`). I stopped it before completion because a shallow checkout cannot produce a valid result. No summary line exists | scratchpad `ut.log` (partial) |
| Unit tests (full clone at `b9936e5`) | same, in the full clone | **PASS**: `Ran 1332 tests in 2328.474s`, `OK (skipped=26)`, exit 0. A first attempt was killed at a 20-minute background limit I had set; a second was killed by my own `pkill` matching its wrapper. The third ran to completion | scratchpad `full-ut2.log` |
| Ledger schema probe | `check_schema("run-ledger-event", {…"outcome":"AUTHORITY_CHECKED"…})` | **FAIL** (refused). This is the OBSERVED defect behind gap 1 | inline in session |
| Gate dossier validation | `badf_gate.py dossier …` | **NOT_RUN**. No dossier was produced; this is research | — |
| External spec reads | WebFetch/WebSearch as cited in §6 | Done. Some rows **UNVERIFIED** as marked | §6 |

### 7.1 Reading the check results

- **The repository is green at `b9936e5` when checked against full history.** `repo` PASS and 1332 tests OK.
- **The session's own checkout cannot run BADF's checks.** It is a 50-commit shallow clone, and `verify_work_ledger` resolves historical `landed_as` SHAs. Any future session that runs the gate needs a full clone. That is an environment configuration fact, not a repository defect.
- **Green tests do not cover the ledger defect.** The gap-1 schema defect coexists with a passing suite, because no test validates a post-WP-0132 ledger against `run-ledger-event.schema.json`. That is the point of CAND-01.

**Repository state after research:** the research phase changed nothing. Nothing was committed, pushed or opened; no registry, routine or trigger was created. On the operator's later instruction ("Proceed like Professional Engineer Team"), `WP-2026-0160` landed this record, and nothing else, as documentation.

---

## 8. Non-coverage: what was not assessed

- **`docs/governance/GITHUB_CONTROL_PLANE.md`** (2,501 lines) was not read beyond grep hits. It may hold HITL or identity controls relevant to Pillar 9 and checklist 8.
- **The full bodies of `badf_gate.py` and `badf_compose.py`** were not read. Only the functions cited were read. The tests were not read beyond the cited lines.
- **PR bodies and issue threads** (#220, #236, #261, #358, #360, #362) were not read. In particular, the **seeded-mutation evidence for S1/S2/S3 was not inspected**. Its existence is asserted only by the work packages' acceptance criteria.
- **Sibling repositories** (biztrust, biztrust_ib, bERP, badf-flow-control) were not re-read. Their claims come from AET-B design §1.1 as recorded.
- **The vendored context-engineering skills' content** was not assessed for quality, only for registry status.
- **Sandbox technologies** (Wasm, gVisor, Firecracker) were not researched (NOT_RUN).
- **External fetches were summarized by a tool.** Exact quotes are reliable only where reproduced from the MCP page itself.
- **Effort estimates in §5 are judgement** (INFERRED), not measured.
- **Process gaps.** No session record (`templates/session.md`) was created. The report is a design and research document under `WP-2026-0160`, not an evidence object; it carries no evidence binding of its own beyond the lockfile digest.
