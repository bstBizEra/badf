---
name: badf-build
description: Execute exactly one authorized BADF Governed Work Package into G07 build evidence — claim, preflight, isolate, baseline, slice, test-first where a durable seam exists, implement, verify freshly, self-review, reconcile, package, hand off — inside the WP's exact scope, baseline, budget and stop contract. Use when a G06-planned Work Package is authorized for implementation. Grants no push, merge, release or gate authority.
---

# BADF Build

`badf-build` performs the **authorized mutation**. `badf-implementation-plan` decides *how* authorized
work is decomposed (IMP-I15: the plan cannot execute its own Work Packages); `badf-build` executes one
Governed Work Package; G08 verifies the result **independently**; `badf-git` governs repository
topology and integration; the canonical BADF gate evaluates the evidence; **authority** permits the
lifecycle transition. `badf-build` must not swallow G08.

The skill's admission status is recorded in `badf/skill-registry.json`; this file defines behavior and
must not hardcode a lifecycle status that can drift from the registry.

## Fundamental rule

```text
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
NO UNVERIFIED MUTATION
BUILD ≠ INTEGRATION
AUTHOR REVIEW ≠ INDEPENDENT ASSURANCE
```

## Boundary

```text
badf-implementation-plan   decides HOW authorized work is decomposed
badf-build                 performs the authorized mutation
badf-verification (G08)    independently verifies the result
badf-git                   governs repository topology / integration
BADF gate                  evaluates evidence
Authority                  permits lifecycle transition
```

```text
G06 — Implementation planning: work-breakdown · test-plan · release-plan · rollback-plan
G07 — Build complete:          source-change · build · unit-test · documentation
G08 — Engineering verification: independent-review · integration-test · contract-test · composed-tree-test
```

## Authority split

```text
Agent judgment MAY resolve implementation detail inside granted scope.

Agent judgment MUST NOT resolve an authority conflict, scope expansion, risk-class change,
security acceptance, architectural deviation, acceptance weakening, or destructive escalation.
```

A build controller may make local engineering choices only while they remain within the already
authorized Work Package contract. An external methodology's "ruling" is never a BADF authority decision.

## Workflow

```text
CLAIM → PREFLIGHT → ISOLATE → BASELINE → SLICE → TEST-FIRST/VERIFY-FIRST → IMPLEMENT → LOCAL VERIFY → SELF-REVIEW → RECONCILE → PACKAGE → HANDOFF
```

1. **CLAIM** — resolve exactly one Governed Work Package: identity, demand, G06 plan, source baselines,
   scope, expected surfaces, change class, authority, budget, stop conditions, test and evidence
   obligations. No valid WP → **NO BUILD**. See `references/preflight.md`.
2. **PREFLIGHT** — before any mutation: WP executable, dependencies satisfied, G06 baseline current,
   authority current, expected branch/base current, permissions sufficient, budget remaining,
   environment available, stop contract loaded. Any uncertainty affecting authority → **STOP**, not guess.
3. **ISOLATE** — use the isolation declared by planning; request the workspace from `badf-git`, never
   invent branch mechanics.
4. **BASELINE** — record pre-change evidence (repository state, baseline tests, build/typecheck, known
   failures, environment identity, base SHA, composition baseline). `PRE-EXISTING FAILURE ≠
   BUILD-INTRODUCED FAILURE`.
5. **SLICE** — one coherent acceptance slice at a time: acceptance → test seam → failing observation →
   minimal mutation → passing observation → next slice.
6. **TEST-FIRST / VERIFY-FIRST** — governed TDD at durable seams declared by the G06 test-plan; where
   TDD does not apply, an explicit alternate verification obligation. See `references/tdd-contract.md`.
7. **IMPLEMENT** — the minimal mutation that makes the observed failure pass, inside the authorized
   surface. Design drift is upstream work. See `references/execution-contract.md`.
8. **LOCAL VERIFY** — focused tests and typecheck continuously; the full verification at finish; fresh,
   never inferred.
9. **SELF-REVIEW** — author-side challenge (self, per-task, whole-branch). It is G07 author verification
   evidence, **not** G08 independent review. See `references/self-review.md`.
10. **RECONCILE** — compare planned surface with actual surface; unexpected scope is refused or
    re-authorized. See `references/scope-containment.md`.
11. **PACKAGE** — normalize into exactly the four G07 evidence types. See `references/evidence-packaging.md`.
12. **HANDOFF** — commit to the authorized working branch if granted; route integration to `badf-git`
    and verification to G08. Never infer push → PR → merge. See `references/handoff-to-g08.md`.

## Invariants (frozen)

```text
BLD-I01 — One authorized WP
Every build run binds exactly one executable Governed Work Package.

BLD-I02 — Exact baseline
Build begins from the revision/baseline authorized by the WP.

BLD-I03 — Authority before mutation
No mutation occurs until WP authority and tool/environment permissions are validated.

BLD-I04 — Scope containment
Actual mutation remains within authorized scope; unexpected material surface is refused or re-authorized.

BLD-I05 — Acceptance binding
Every material mutation resolves to an acceptance, defect, test, migration or required implementation obligation.

BLD-I06 — Durable verification seam
Behavior tests use declared observable seams, not implementation details.

BLD-I07 — Red before green when TDD applies
A test-required behavioral change carries observed failing evidence before the implementation that makes it pass.

BLD-I08 — TDD exceptions explicit
Absence of red-green evidence requires NOT_APPLICABLE_WITH_REASON and an alternate verification obligation.

BLD-I09 — Fresh verification
No success/completion claim relies only on prior, inferred or agent-reported results.

BLD-I10 — Delegation cannot expand authority
Every subagent's authority is a strict subset of the governing WP.

BLD-I11 — Retry changes information
Repeated execution without a changed hypothesis/input/implementation/diagnostic does not consume another permitted engineering attempt.

BLD-I12 — Budget enforced
Attempt/time/cost exhaustion yields BLOCKED, never autonomous extension.

BLD-I13 — Stop conditions dominate
Authority conflict, destructive surprise, credential exposure, policy bypass, evidence corruption and other WP stop conditions stop mutation.

BLD-I14 — Design drift is upstream work
Build cannot silently modify architecture, security, requirements or acceptance semantics.

BLD-I15 — Author review ≠ independent assurance
Build-side review cannot self-satisfy G08 independence.

BLD-I16 — Build evidence is exact
Source/build/test/documentation evidence binds exact revision, commands/toolchain and resulting artifact digests.

BLD-I17 — Build ≠ integration
Completion of implementation grants no push/merge/release authority.

BLD-I18 — No second gate
No scripts/badf_build.py may become a competing lifecycle validator; deterministic G07 semantics remain in badf_gate.py.
```

## Doctrine

```text
G06 authorizes a bounded implementation plan.
A Governed Work Package is the unit of execution authority.
badf-build executes one authorized Work Package inside its exact scope, baseline, budget and stop contract.
TDD is used at durable behavioral seams where applicable.
Subagents may perform work, but delegation can only reduce authority, never expand it.
Fresh verification precedes every completion claim.
Build-side review improves the work but does not replace independent G08 assurance.
badf-git governs repository integration.
The canonical BADF gate evaluates G07 evidence.

A successful build proves only:
  "the authorized change was built and author-verified."
It does not mean "independently verified", "approved to merge", "approved to release", or "safe for production".
```

## References

- `references/g07-contract.md` — what G07 evidence is, what it binds, what a build does and does not prove.
- `references/preflight.md` — CLAIM fields and the PREFLIGHT checklist; STOP over guess.
- `references/execution-contract.md` — isolate, baseline, slice, implement, refactor doctrine, design-drift routing.
- `references/tdd-contract.md` — governed TDD: required / not-applicable-with-reason, by change type.
- `references/test-seams.md` — seams come from the G06 test-plan; TEST_PLAN_DEFECT routing.
- `references/delegation.md` — subagent contracts as strict subsets; task ≠ Work Package.
- `references/scope-containment.md` — planned vs actual surface; UNEXPECTED_SCOPE handling.
- `references/retry-and-budget.md` — attempts that add information; budget exhaustion → BLOCKED.
- `references/stop-conditions.md` — the conditions that stop mutation, and their precedence.
- `references/self-review.md` — build review vs G08 independent review.
- `references/evidence-packaging.md` — the four G07 evidence bindings and the build ledger.
- `references/handoff-to-g08.md` — package, route to badf-git, hand to G08; no inferred integration.
- `references/acceptance.md` — the admission ladder BLD-A…E.
- `references/external-methodology.md` — Matt Pocock and Superpowers: adapted, rejected, never authority.
