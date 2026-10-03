# Learning-plane tool intake: EvoSkill and SkillOpt (`BADF-WP-0155`)

Status: **intake record. Both tools are registered `PROPOSED` in `badf/tool-registry.json`.**
Nothing from either repository was installed, imported or executed to produce this record.
Registration lets the AET *consider* each tool; it grants no authority to run it
(AET-I03, charter §12). Running either tool is a separate, later act (§5).

## 1. What was asked, and what it maps to

The operator asked to "install" two skill-optimisation tools into the Engineer Team. Neither
tool is a skill. Each is a toolkit that runs coding agents against tasks, rewrites their
skills and prompts, and keeps the rewrites that score better. In AET terms (docs/14 §2) that
is the **learning plane**. The learning plane "may improve capability; it never silently
expands authority" (AET-I09). docs/07 adds: "Do not allow skill output to approve the same
skill or gate."

The admissible shape is therefore narrow:

- **A tool that proposes.** It is a registered tool that may, under §5's controls, produce
  candidate skills.
- **Candidates enter BADF as `PROPOSED` skills only.** They then go through the docs/07
  lifecycle (`PROPOSED → … → ACTIVE`) like any hand-written skill, with independent review
  and human approval.
- **Its own score is never evidence for admission.** The tool's internal acceptance score
  counts as a proposal, not as validation.

## 2. Provenance (pinned)

| | EvoSkill | SkillOpt |
| :-- | :-- | :-- |
| Repository | `https://github.com/sentient-agi/EvoSkill` | `https://github.com/microsoft/SkillOpt` |
| Commit | `36f6f04952293d7054145550c2b9f0b0411bff1c` (2026-07-06) | `fa4ca184573e42ec11472959dd57422381418096` (2026-10-01; authored by dependabot) |
| Tree | `59c7976baf767a23b1ba2ac7f141694e91beaacb` | `e0df22e8340c5255eb128a3663bcb3a6e8dba567` |
| Licence | Apache-2.0 | MIT |
| Lock | `uv.lock`: 504 packages with sha256 hashes. Only the `uv` path uses it | **none**; dependencies are `>=` floors only |
| Shape | Python CLI `evoskill`; harnesses for Claude Code, Codex, OpenCode, OpenHands, Goose, Harbor; Docker and Daytona sandboxes | Python package `skillopt` (trainer), `skillopt-sleep` (session-harvesting nightly loop), Gradio WebUI, plugin and MCP shells for Claude Code, Codex, Copilot, Cursor, Devin, OpenClaw |

## 3. Findings, re-measured

Each finding was reported by an independent read-only reviewer and then **re-measured
against the file** at the pinned commit. Findings not re-measured are kept in the session's
review notes and are not relied on here.

### 3.1 EvoSkill

| # | Finding | Evidence |
| :-- | :-- | :-- |
| E1 | **Agents run with all permission prompts bypassed** in its Docker mode, and auto-accept edits everywhere else | `src/registry/sdk_utils.py:42-44` sets `bypassPermissions` when `EVOSKILL_REMOTE=1`, which `src/docker/launcher.py:69` sets |
| E2 | **It rewrites local git branches from a remote sandbox's refs** | `src/remote/daytona.py:499` runs `git branch -f <name> <sha>` for each ref in the downloaded bundle |
| E3 | **It passes the whole environment, secrets included, to the Harbor harness**, contrary to its own comment | `src/harness/harbor/agent.py:228-232` `env = dict(os.environ)`, under "don't leak project secrets" |
| E4 | **It kills processes it did not start** | `src/harness/opencode/executor.py:94` `pkill -f "opencode serve"` |
| E5 | **It stores a Daytona API key in plaintext and uploads it.** The upload excludes neither `.env` nor `.evoskill/` | `src/cli/commands/init.py:342,556-570`; `src/remote/sync.py:11-21` |
| E6 | **It stashes, checks out and deletes branches in the user's repository** without asking | `src/registry/manager.py:516-550` (`stash push -u`/`apply`/`drop`), `:568` (`branch -D`) |

### 3.2 SkillOpt

| # | Finding | Evidence |
| :-- | :-- | :-- |
| K1 | **Its Claude Code execution backend defaults to `bypassPermissions`** | `skillopt/model/codex_harness.py:837,904,1107` `permission_mode or "bypassPermissions"` |
| K2 | **An environment flag turns on `--dangerously-skip-permissions`** | `skillopt_sleep/adapters/superpowers.py:1047-1051` (`SKILLOPT_UNSAFE=1`) |
| K3 | **Without an explicit endpoint, it sends requests to a Microsoft-internal Azure endpoint** | `skillopt_sleep/backend.py:2203,2265` falls back to `https://oaidr9.openai.azure.com/` |
| K4 | **SkillOpt-Sleep harvests Claude Code session transcripts with no redaction** | `skillopt_sleep/harvest.py`: 0 references to `redact` (the other harvesters redact) |
| K5 | **Its acceptance gate is a bare score comparison**, and the default metric blends in the model's own soft score | `skillopt_sleep/gate.py:42-43` `if cand_score > current_score`; `skillopt_sleep/config.py:66` `gate_metric: "mixed"` |
| K6 | **SkillOpt-Sleep edits project memory by default**, and adoption into live files is one flag away | `skillopt_sleep/config.py:74` `evolve_memory: True` (CLAUDE.md); `:89` `auto_adopt: False` (staged by default) |

**What SkillOpt does well, measured (credited, not adopted):** proposals are staged rather
than adopted by default (K6). The research trainer keeps a separate test split from the
selection split. Adoption writes backups and SHA-pinned receipts.

## 4. Reading against BADF

| BADF rule | EvoSkill | SkillOpt |
| :-- | :-- | :-- |
| AET-I09, docs/07: output must not approve itself | **fails as shipped.** It selects on a reused validation split, and its scores live in files the agents can write (reported) | **fails as shipped in Sleep** (K5): the same model mines tasks, writes rubrics, edits and judges, and the default has no test split (reported). The research trainer is closer |
| Charter §12: least privilege, no workarounds | fails (E1, E6) | fails (K1, K2) |
| Charter §12: credentials by approved injection only | fails (E3, E5) | partial: full env inherited by exec agents (reported) |
| Charter §10: no secrets or raw personal data in prompts | n/a | **fails** (K4) |
| Charter §13: dependency review, pinned provenance | partial (lock exists, but the installer and Docker bypass it) | fails (no lock) |
| Destructive scope (charter §3, §13) | **fails** (E2, E4, E6) | passes for git (reported) |

Neither tool may run against a real BADF checkout, a seat's session history, or a
credential-bearing environment. That is an observation about the code as pinned, not a
judgement on the research.

## 5. Conditions before either tool may run

Registration is `PROPOSED`. Moving either tool to an executable status requires a further
work package, a human-reserved approval from `security_authority` (`badf/authority-matrix.json`),
and every condition below. Each condition answers a finding above.

1. **Isolation.** The tool runs only in a disposable container or VM, with:
   - no mount of a BADF checkout or of any agent's home directory (`~/.claude`, `~/.codex` and so on);
   - an egress allowlist naming one model provider endpoint;
   - no git remote.

   *(E1, E2, E4, E6, K1, K2)*
2. **Credentials.** One scoped, budget-capped key is injected per run, with nothing else in
   the environment. Never a Daytona key; never `.env`. *(E3, E5)*
3. **No session harvesting.** SkillOpt-Sleep's harvesters are not run. Task data is an
   explicit, curated, redacted set. *(K4)*
4. **Explicit endpoint.** A run fails closed if no provider endpoint is configured.
   Fallback hosts are blocked at egress. *(K3)*
5. **Independent judge.** A candidate is scored by a judge independent of the tool:
   - a deterministic verifier, or a different model from the optimiser;
   - on a held-out set the tool never sees;
   - with a significance margin, not a bare `>`.

   *(K5; AET-I02)*
6. **Output quarantine.** A candidate leaves the sandbox only as files for review. It
   enters `skills/` as `PROPOSED` through a pull request. The following are forbidden as
   operation classes:
   - auto-adopt;
   - `CLAUDE.md` or memory edits;
   - cron or scheduled runs;
   - MCP `adopt` or `schedule` tools.

   *(K6; AET-E scope)*
7. **Excluded components.** These are not admitted:
   - EvoSkill's `install.sh` (an unpinned `curl | bash` on `main`) and its bundled
     `brainstorming` skill (it instructs itself into every task);
   - SkillOpt's `plugins/openclaw` (hard-coded personal paths), its WebUI and its plugin
     marketplace entry (pinned to `main`).

## 6. Non-coverage

- **No dynamic analysis.** The tools were read, never run.
- **Dependencies were not audited.** Transitive packages were not reviewed.
- **Not everything was re-measured.** Findings outside §3 rest on one reviewer each.
- **The tool and its research are separate questions.** Upstream changes after the pinned
  commits are not covered. Re-pinning is a new intake.
