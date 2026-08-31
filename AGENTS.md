# BADF Repository Agent Operating Charter

Status: **NORMATIVE**  
Owner: BADF Governance Authority  
Applies to: every human, agent, subagent, automation, tool, and MCP integration operating in this repository

## 1. Mission

Build and operate the **BizEra Agent Delivery Framework (BADF)** as a governed, evidence-producing delivery control plane from product intent through production operations and institutional learning.

BADF assigns and verifies authority. It does not grant authority merely because an agent can perform an action. Capability, permission, approval, and evidence are separate controls.

## 2. Instruction precedence

Apply instructions in this order:

1. applicable law, organizational security policy, and platform-enforced controls;
2. explicit human authority recorded in an approved work package or decision;
3. this root `AGENTS.md`;
4. the normative documents referenced by this file;
5. the closest nested `AGENTS.md` or `AGENTS.override.md` for the working directory;
6. approved work-package instructions;
7. tool, skill, MCP-server, and agent-role guidance;
8. task-specific preferences.

A lower layer may narrow behavior but must not expand authority or weaken a higher-layer control. On contradiction, stop mutation, record the conflict, and escalate.

## 3. Non-negotiable invariants

- **No work without authority:** every material change must reference an active work-package ID.
- **No claim without evidence:** completion, safety, testing, release, and production claims require immutable or content-addressed evidence.
- **No self-approval:** the author may not supply the independent approval required by a gate.
- **No silent scope expansion:** discovered work becomes a new or amended work package.
- **Fail closed:** missing, ambiguous, stale, unverifiable, or contradictory evidence blocks progression.
- **Least privilege:** use the narrowest tool, credential, scope, and duration needed.
- **Reproducibility:** record the commit, inputs, environment/toolchain identity, commands, outputs, and result digest.
- **Separation of records:** Git is the system of record for versioned delivery artifacts; the approved work system is the system of record for authority and status; observability systems are the system of record for runtime behavior.
- **Production is not closure:** deployment must be followed by production verification, operational acceptance, and learning reconciliation.
- **Memory is not authority:** recalled context can guide discovery but cannot approve, waive, or prove anything.

## 4. Required reading by task

Before acting, read only the documents relevant to the task, plus every document marked mandatory below.

| Task | Required documents |
| --- | --- |
| Any repository change | `docs/00-operating-model.md`, `docs/01-lifecycle-gates.md`, `docs/05-evidence-and-provenance.md` |
| Planning or implementation | `docs/02-engineering-loop.md`, `docs/13-artifact-model.md` |
| Agent delegation or council review | `docs/03-authority-and-agent-councils.md` |
| Agentic team runtime work (seats, planes, AET rungs) | `docs/14-agentic-engineer-team.md` |
| Memory, context, or knowledge work | `docs/04-memory-and-context.md` |
| Session continuation or handoff | `docs/06-sessions-handoffs-recovery.md` |
| Skill creation/use | `docs/07-skills-governance.md` |
| MCP or external tool use | `docs/08-mcp-and-tools.md` |
| Security-sensitive work | `docs/09-security-supply-chain.md` |
| Test or quality work | `docs/10-quality-testing.md` |
| Release or deployment | `docs/11-release-production.md` |
| Production operations or learning | `docs/12-operations-learning.md` |

## 5. Start-of-session protocol

Before mutation, the active agent must:

1. identify the repository root and active instruction chain;
2. inspect repository status without discarding existing changes;
3. resolve the work package, lifecycle gate, scope, authority, and acceptance criteria;
4. load the minimum relevant context and declare assumptions;
5. inventory available skills, MCP servers, tools, credentials, and approval boundaries;
6. select a verification plan and evidence destination;
7. stop if authority, target, or destructive scope is ambiguous.

Create a session record from `templates/session.md` for work spanning multiple actions, agents, or context windows.

## 6. Delivery lifecycle

BADF uses gates `G00` through `G14`, defined in `badf/lifecycle.json` and explained in `docs/01-lifecycle-gates.md`.

An agent may work within an open stage but may not declare the next stage open unless:

- every required artifact and evidence type exists;
- evidence binds to the current change and intended target;
- required checks pass on the composed result, not only the source branch;
- required independent reviewers or human authorities approve;
- exceptions are explicit, scoped, time-bounded, and approved;
- `python3 scripts/badf_gate.py dossier <path>` exits `0` with a rendered verdict of
  `APPROVED` or `APPROVED_WITH_CONDITIONS`. A `BADF GATE HELD` (exit `3`) means the
  dossier is well-formed but its verdict is `REWORK_REQUIRED`, `BLOCKED` or
  `HUMAN_REQUIRED` -- that is not a pass and does not open the next stage.

## 7. Work-package contract

Every material task must define:

- stable ID and accountable owner;
- business objective and expected value;
- in-scope and out-of-scope boundaries;
- dependencies and target lifecycle gate;
- acceptance criteria and non-functional requirements;
- risk, data classification, and change class;
- permitted tools and environments;
- required tests, reviewers, evidence, rollback, and escalation path.

Use `templates/work-package.json`. A chat request is input to a work package, not a substitute for one when the change is material.

## 8. Advanced engineering loop

Operate this bounded loop:

`FRAME -> DISCOVER -> PLAN -> AUTHORIZE -> BUILD -> VERIFY -> CHALLENGE -> RECONCILE -> DELIVER -> OBSERVE -> LEARN`

Rules:

- establish a baseline before editing;
- use the smallest reversible change that tests the hypothesis;
- verify locally before seeking broader validation;
- challenge material work independently;
- reconcile results against acceptance criteria and the current composed tree;
- cap retries; repeated failure triggers diagnosis or escalation, not blind looping;
- preserve failed attempts as evidence when they affect a decision.

## 9. Agent and council policy

- Delegate only bounded, independent tasks with explicit inputs, outputs, non-goals, and evidence requirements.
- Parallel agents must not edit overlapping files unless a designated integrator coordinates them.
- First-round council ballots must be independent and sealed before synthesis.
- Council agreement is advisory unless the authority matrix explicitly makes it a gate.
- High-impact, constitutional, credential, production, data-destructive, and exception decisions remain human-controlled unless a ratified policy explicitly says otherwise.
- The coordinating agent owns integration, conflict resolution, and final evidence completeness.

## 10. Memory, evidence, and sessions

- Store durable verified facts in approved project memory; store working notes in session records; store decisions in ADRs or decision records; store proof in evidence objects.
- Label memory as `OBSERVED`, `INFERRED`, `DECIDED`, or `SUPERSEDED`, with source and review date.
- Never store secrets, tokens, private keys, raw personal data, or unapproved regulated data in prompts, memory, logs, or evidence.
- At session end, record state, changes, checks, unresolved risks, next safe action, and handoff digest.

## 11. Skills

- Use a skill when its declared scope matches the task; read its complete `SKILL.md` before acting.
- Repository skill sources live under `skills/`; runtime installation may place approved copies under `.agents/skills/`.
- A skill cannot grant permissions, override this charter, or self-certify its output.
- Pin external skill provenance and review scripts before execution.
- Validate changed skills and test their deterministic scripts.

## 12. MCP and tools

- Treat MCP servers and tools as untrusted capability boundaries until registered in `badf/mcp-registry.json` or `badf/tool-registry.json`.
- Prefer read-only operations for discovery; separate read, write, destructive, and administrative capabilities.
- Never place credentials in repository configuration. Use approved secret injection and short-lived credentials.
- Verify target identity and preview the exact mutation before external writes.
- Record tool name, operation class, target, approval, result, and returned identifiers in evidence.
- Do not work around sandbox, permission, network, or policy blocks.

## 13. Change and code rules

- Preserve user changes and avoid unrelated edits.
- Do not use destructive Git or filesystem operations unless explicitly authorized and target-verified.
- Keep generated files reproducible; identify the generator and source.
- Add or update tests for behavioral changes.
- Update contracts and documentation in the same change when behavior changes.
- Do not introduce dependencies without license, security, maintenance, and necessity review.
- Avoid compatibility shims or speculative abstractions without an approved requirement.

## 14. Required verification

Before declaring work complete, run the relevant project checks and always run:

```bash
python3 scripts/badf_gate.py repo
python3 -m unittest discover -s tests -p 'test_*.py'
```

For a gate dossier:

```bash
python3 scripts/badf_gate.py dossier path/to/gate-dossier.json
```

Report checks exactly as `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`, including the command and evidence path. Never imply unrun checks passed.

## 15. Completion protocol

A delivery response must state:

- outcome and work-package ID;
- files or systems changed;
- acceptance criteria satisfied;
- verification performed and result;
- evidence object or dossier location;
- residual risks, exceptions, and follow-up owner;
- lifecycle gate reached and who is authorized to advance it.

If any required item is missing, the disposition is `BLOCKED`, `PARTIAL`, or `HUMAN_REQUIRED`—never `COMPLETE`.

## 16. Code review rules

Review for correctness, security, data integrity, concurrency, migration safety, backward compatibility, observability, operability, rollback, tests, and evidence binding. Prioritize defects over style. A reviewer must identify what was not assessed so absence of findings is not misread as full coverage.

## 17. Canonical references

- Operating model: `docs/00-operating-model.md`
- Lifecycle: `docs/01-lifecycle-gates.md` and `badf/lifecycle.json`
- Engineering loop: `docs/02-engineering-loop.md`
- Authority: `docs/03-authority-and-agent-councils.md`
- Memory/evidence/session: `docs/04-memory-and-context.md` through `docs/06-sessions-handoffs-recovery.md`
- Skills/MCP/tools: `docs/07-skills-governance.md`, `docs/08-mcp-and-tools.md`
- Production and learning: `docs/11-release-production.md`, `docs/12-operations-learning.md`
- Artifact schemas: `schemas/`

