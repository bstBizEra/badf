# Independent advisory: WP-2026-0161 budget recording

Actual reviewer: `/root/delegation_authority_review`; WP-local functional route: BADF-REV advisory. Read-only analysis of policy, retained reports/logs and progress; no implementation, test execution, human approval, budget amendment or policy edit.

## Disposition

The available evidence establishes **at least six substantive retry transitions** under the existing WP. This minimum excludes fixture-only corrections, planned TDD RED/GREEN transitions, exploratory diagnostics, successful initial slice executions and additional verification of unchanged successful code. It already exceeds the machine C6 refusal threshold of more than five RETRY events. Remaining Task6/Task7 implementation/verification cannot honestly be declared within a remaining autonomous execution budget on that evidence.

Preserve the candidate, evidence and original five-attempt budget. Pause additional build/fix dispatches, reconcile the actual attempt history and prepare a BLOCKED handoff with the precise unfinished work and the next bounded work-authority decision. This is a budget boundary, not a request to repeat the accepted identity or initial implementation authorization. This advisory does not itself extend the budget, issue a human decision, or retrospectively approve execution beyond the ceiling.

## Contract and distinction

- `work/WP-2026-0161/work-package.json` declares `execution_budget.max_attempts: 5`; there is no independent per-slice budget in that governing value.
- `skills/badf-implementation-plan/references/execution-budget.md` describes a **per-WP executable constraint** defined before autonomous execution.
- `skills/badf-build/references/delegation.md` states that every execution slice remains inside **WP scope, authority, risk, budget and evidence contract**. A fresh subagent is not a new work package and cannot reset its budget.
- `skills/badf-build/references/retry-and-budget.md` and BLD-I11 require a retry to change hypothesis, input, implementation or diagnostic. A repeat of the same command/hypothesis/input earns no new engineering attempt. Exhaustion yields BLOCKED, never autonomous extension.
- `docs/02-engineering-loop.md` requires root-cause diagnosis after two materially similar failures and a blocked handoff after the retry budget.
- `scripts/badf_gate.py::_check_build_budget_and_stop` reads ledger events for refusal, never permission; STOP dominates, and `RETRY` count greater than the WP maximum refuses. Its numerical check is not a definition that excludes substantive failed-build corrections merely because they occurred inside a planned slice.

The phrase **“5 review fix rounds per task”** in `.superpowers/sdd/allocator-implementation-plan/progress.md` is inconsistent with the actual WP-level ceiling. Do not reinterpret the original number as five new rounds for every fresh agent or task. Retain the original statement and append the correction rather than silently rewriting the history.

The seven planned task slices are not seven retries: each advances a new predeclared obligation. Expected failing-first tests before implementing that obligation are RED evidence, not an unexpected failed execution followed by a retry. Successful initial slice builds and prescribed independent verification do not become retries merely because they run commands.

Conversely, when an attempted implemented slice fails unexpectedly and implementation/input is corrected to attempt it again, that is a substantive engineering retry. Independent review returning CHANGES_REQUIRED and redispatching the implementation for corrective work also qualifies. Neither a new child-agent context nor the presence of an expected regression RED inside the corrective dispatch erases that retry; count the corrective dispatch once, not once per regression subtest.

## Minimum justified RETRY transitions

These labels identify observations for reconstruction, not invented historical ledger event IDs or timestamps. Ordering follows the retained progress/reports; exact original transition timestamps are not established here.

| Observation | Failed execution/challenge and changed response | Retained evidence |
| --- | --- | --- |
| R1 | Task1 independent CHANGES_REQUIRED; redispatched fix changes retained-page projection, source-shape handling and negative coverage | `progress.md` Task1 fix round1; `task-1-review.md`, appended `task-1-report.md`, Task1 `round1-red.*`, `round1-green.*` or actual retained final GREEN names |
| R2 | Task2 independent CHANGES_REQUIRED; redispatched fix adds malformed-record validation and every-contender assertions | `progress.md` Task2 fixround1; Task2 `task-2-review.md`, appended `task-2-report.md`, `fix1-red.*`, `fix1-verified-green.*` |
| R3 | Task3 attempted build fails with import-edit indentation error; production implementation corrected and generation command rerun | Task3 `task-3-report.md` “Failed development attempts”; `attempt1.json/.stderr` followed by changed implementation and later attempt |
| R4 | Task3 subsequent attempted build exposes invalid generated `council:null`; generated dossier implementation corrected before another generation run | Task3 report; `attempt2.json/.stderr`, `attempt3.*`; production change omits invalid optional null |
| R5 | Task4 unexpected broad GREEN run fails target-refusal ordering; production initial-target validation ordering corrected, same four-module verification rerun | `.superpowers/sdd/allocator-implementation-plan/task-4-report.md`; Task4 `green-attempt.json/.stderr` (64 tests, one failure), `verified-green.*` |
| R6 | Task4 independent Important I1 requires another implementation dispatch to correct premature COMMITTED evidence; changed ledger-generation/validation implementation reverified | `progress.md` Task4 fixround1; Task4 review, report Fix round1, `fix1/red.*`, `fix1/extended-red.*`, `fix1/green.*` |

All six are substantive behavior/build corrections even if one adopts the most permissive interpretation of fixture-only corrections. R3 and R4 have different concrete causes; do not claim they were materially identical failures or invent a root-cause event that was not recorded.

## Additional observations requiring faithful recording

- Task1 report records an interim focused failure from reused mutated fixture evidence, followed by changed setup. Retain this as an unexpected fixture failure and changed-input continuation; it cannot simply disappear because production behavior was not at fault.
- Task2 report records a contender-winner fixture assumption failure visible in the tool transcript but not retained as stdout/stderr files, and `green-attempt.*` retains another failed implemented run from missing `framework.inputs` in a schema fixture. The two causes are different; correlate actual commands/changes before grouping anything. State the artifact gap honestly.
- Task3 `green.json/.stderr` is a failed eleven-case run from subprocess bytecode caches; changed fixture environment (`PYTHONDONTWRITEBYTECODE=1`) produces final GREEN. This is not a production-mutation defect, but it is an unexpected executed GREEN failure followed by a changed-input continuation. A diagnostic terminated after a 50-second timeout is also retained in the report; classify its actual purpose/inputs rather than counting it as an additional whole-WP retry automatically.
- Task2 multiple initial RED forms and Task1 corrected regression RED shapes must remain in the evidence. Converting a missing-interface/runtime failure into a meaningful failing-first assertion before the corresponding behavior implementation is diagnostic/TDD evidence, not a separate successful build attempt. Do not use this distinction to relabel an unexpected implemented GREEN failure as planned RED.
- Task5's report available during this review says named GREEN pending and identifies an injection-fixture mismatch inside the initial RED exercise. No completed Task5 GREEN, independent-review fix or retry count is inferred. Update from the actual eventual record; do not erase any work that already happened.

These additional observations make the complete history larger or less certain; they cannot reduce the source-backed six-transition minimum. A final comprehensive count must distinguish planned test obligations from unexpected implemented failures using actual code/input boundaries. No need to invent a precise higher total to recognize the present budget hold.

For transparent cost accounting, the identified inventory is **six substantive correction transitions plus four additional fixture-related candidate retries = ten identified candidate transitions**: Task1's mutated-fixture correction; Task2's contender-winner assumption correction; Task2's missing `framework.inputs` fixture correction; and Task3's bytecode-cache fixture/environment correction. This is not a proven exhaustive upper bound. BLD-I11 explicitly includes changed inputs, so fixture-only status does not by itself exempt these four; record them as retries unless actual command/input chronology establishes that a particular event was solely preparatory TDD/diagnostic work rather than a failed implemented execution followed by another attempt. The Task5 RED injection adjustment, initial missing-interface RED corrections and the Task3 timed diagnostic are additional observations with different purposes, retained above rather than folded into an invented exact total. The successor packet must carry this full inventory and its uncertainty, not just the conservative six.

## Honest reconstruction and handoff

1. Preserve original reports, logs, progress and WP budget. Append the correction to the per-task budget claim and retain this assessment as advisory evidence.
2. Record each established material transition in `build/progress.jsonl` using the canonical hash chain, actual recording time and `provenance: RECONSTRUCTED`. Bind the evidence/source commit, actual actor and changed hypothesis/input/implementation in notes. Original event times remain unknown unless independently supported; do not substitute command-file timestamps or fabricated historical dates.
3. Record observed initial starts, planned RED/GREEN and verification separately from RETRY. Do not emit only the three review rounds, omit inconvenient implementation/fixture failures, use empty history to pass C6, or edit/remove prior ledger events after a refusal.
4. Once the six justified RETRY transitions are represented, the existing numerical C6 check should refuse under `max_attempts: 5`. Preserve that refusal and a STOP/BUDGET_EXHAUSTED handoff. This review has not executed that check and supplies no claim that it already returned a particular result.
5. Hand off the exact current candidate and unfinished Task5/Task6/Task7 obligations, mandatory composed checks, Windows non-coverage and separate C3 acceptance/merge/BizTrust-G00 decisions. The work authority may decide a prospective bounded continuation through the approved work-package/decision mechanism. Do not enlarge/reset the original budget autonomously, move the same remaining execution to a nominally new WP merely to evade history, or claim that later authority retrospectively proves prior compliance.

## Non-coverage

This is a report/log consistency assessment, not complete replay of every tool invocation or an authoritative human budget decision. Original command evidence is uneven: some report-described executions have no retained streams, and timestamps/actor fields are not fully correlated here. No prior canonical build ledger was found in this review beyond `build/session.json`; this does not imply no attempts occurred. The conservative six-transition minimum is sufficient for the hold without resolving every diagnostic/fixture classification. Existing user implementation authorization remains accepted; only continued execution budget and acceptance evidence remain to be reconciled.

## Follow-up: continuation after a recorded STOP

The exact C6 implementation first gathers **all** build-ledger events whose `step == "STOP"` and refuses if any exist. It does not check whether a later RESUME event exists, and provides no budget-amendment, epoch-reset, acknowledged-STOP or successor override for that same work package. No inspected recovery rule supplies such a mechanism. Appending RESUME or raising WP-0161's maximum would therefore leave the stopped package unpackageable under the unchanged checker. Deleting, relocating or relabeling STOP/RETRY history to obtain a pass is not a legitimate continuation.

The smallest available normal route is an **explicitly authorized successor WP**, not an autonomous reset of WP-0161. Keep WP-0161 BLOCKED with its complete stopped history and exact partial candidate. The successor must disclose that history, account for the already produced code as inherited/unaccepted inputs, and have a new prospective bounded execution decision. This is legitimate replanning after handoff, rather than splitting slices into nominal WPs to evade an unchanged budget: fresh authority must knowingly accept the failed attempt history and authorize the precisely measured remaining work. The successor does not certify historical compliance or accept/merge the original work by existing.

The inspected demand contract requires an Issue or authorized demand for each WP; it does not impose one WP per demand. Therefore a new demand ID is **not intrinsically required** by these inspected rules. If DEM-0147 and frozen Issue365 still accurately describe the remaining scope, a new successor-specific human decision may bind that exact existing export plus the new successor packet. This is new authority, not reuse of the old WP-0161 approval. If a materially changed source/scope requires a new demand/export, allocate/export that separately. Keep all previous identities and decisions unchanged and referenced.

### Concrete successor decision packet to finish before asking

Freeze the presently running Task5 command's actual result and code state first; do not predict its outcome. Then prepare one reviewable packet containing:

- New successor WP ID from a complete current sweep and published claim; no guessed next number. Demand choice and exact export identity, with new export/claim only if required by the selected demand route.
- Original stopped WP-0161, unchanged budget five, full retry/STOP ledger digest, blocked-handoff digest, actual outstanding review findings and explicit historical budget overrun/non-coverage.
- Exact inherited candidate commit/head/content tree, dirty-tree diff or untracked artifact digests where applicable, sealed Task5 result and artifact manifest. Distinguish original framework baseline from the current partial candidate; neither is an accepted new framework release.
- Exact remaining plan and its digest: complete/adjudicate Task5's actual result, Task6 receipt-version lineage/compatibility and required documentation, Task7 current composed repository/full-suite checks and required independent assurance; specify precisely whether additional fixes are included and their allowed surfaces.
- One **global** proposed retry/attempt budget for the whole successor, declared semantics, stop conditions and no per-task reset. For example, propose three global changed-information corrective rounds, with original five spent attempts disclosed separately; the human must approve the actual chosen budget/semantics. The current ambiguity between `max_attempts` terminology and numerical RETRY accounting must be disclosed in the packet, not silently resolved by changing code.
- Actual accountable owner, exact target repository, base/candidate identity, unchanged policy epoch and C3 class, bounded tools/environments, evidence obligations, rollback/abandonment plan and no integration/credential authority.
- Explicit exclusions: Issue366, acceptance/merge, framework-pin amendment, BizTrust G00, runtime, release, deployment and any waiver of the original STOP. Windows proof remains an explicit requirement/non-coverage decision; absence of a Windows execution environment is not a fabricated PASS.

After these fields are concrete and digest-bound, the work authority can make a single new bounded decision such as:

> AGREE: I authorize the exact successor packet [published reference and digest] for [claimed successor WP] using [exact demand export]. I acknowledge WP-0161's preserved BLOCKED/STOP history and spent budget. I accept the exact inherited partial candidate and authorize only the listed remaining implementation/verification work under the successor's stated global budget. This grants no retrospective compliance, C3 gate acceptance, merge, revised BizTrust pin, G00, runtime, release or deployment approval.

This wording is a preparation template, **not an approval request while identifiers/digests remain placeholders** and not a human decision made by this reviewer. The coordinator should finish the concrete packet and then obtain the new future-only decision through the already accepted attribution channel. No repeat identity confirmation or duplicate approval of the original implementation package is needed.

Under the new decision, establish the successor's real session/ledger/delegation records before execution. Retain and reference the old stopped package; do not copy its approval as successor authorization or clear its STOP. Its unaccepted code must receive whole-candidate independent review and composed verification under the successor before any separate acceptance/merge decision.
