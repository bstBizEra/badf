# BADF Decision Governance / Board Authority v0.1

Status: **DESIGNED / ADVISORY_ONLY**  
Owner: BST Company Principal (`human_sponsor`)  
Work package: `WP-2026-0137`  
Demand: `BADF-DEM-0124` / Issue #312

## 1. Purpose

This contract defines how BADF may turn evidence and independent expert judgment into a reproducible decision recommendation. It does **not** grant decision or merge authority. The current authority source remains `badf/authority-matrix.json`; `docs/03-authority-and-agent-councils.md` remains the council doctrine; `badf/seats.json` remains the identity-binding source.

BST's human owner is the **Company Principal and constitutional authority**. A project board may become a delegated operating authority only after this contract is implemented, validated, historically shadowed, independently reviewed, and ratified through a later C3 work package. SARCHI coordinates; builders build; reviewers and verifiers challenge; the chair explains; deterministic controls evaluate; only a valid authority source permits action.

The governing equation is:

\[
DecisionAuthority = DelegatedAuthority \cap RuleCompliance \cap EvidenceSufficiency \cap RiskTolerance \cap IndependentJudgment \cap CurrentArtifactBinding
\]

## 2. Constitutional invariants

- `MAJORITY != AUTHORITY`
- `COUNCIL_RECOMMENDATION != EXECUTION_PERMISSION`
- `CONFIDENCE != CALIBRATED_COMPETENCE`
- `MODEL_COUNT != INDEPENDENCE`
- `VERIFIED_BLOCKER IS NON-COMPENSABLE`
- `AUTHOR != INDEPENDENT_APPROVER`
- `CHAIR IS NON-SOVEREIGN`
- `POLICY/RISK/REGISTRY/DOSSIER DIGEST DRIFT => STALE_EVIDENCE`
- `C3R ALWAYS REQUIRES HUMAN PRINCIPAL`
- `v0.1 AUTHORIZATION MODE = ADVISORY_ONLY`

No policy, registry, ballot, dossier, forecast, weight, council verdict, or successful tool call may expand the authority matrix. Learning and performance change future epistemic weight only; they never create permission.

## 3. Control ownership

| Concern | Single source | v0.1 effect |
| --- | --- | --- |
| Constitutional authority | `badf/authority-matrix.json` | unchanged |
| Decision criteria and aggregation | `badf/decision-policy.json` | advisory semantics |
| Organizational risk tolerance | `badf/risk-appetite.json` | advisory ceilings and blockers |
| Council profiles and independence | `badf/council-registry.json` | eligibility definitions; no identity grant |
| Actor/seat identity binding | `badf/seats.json` | referenced, never copied |
| Ballot contract | `schemas/ballot.schema.json` | sealed structured judgment |
| Decision packet | `schemas/decision-dossier.schema.json` | content-addressed recommendation |
| Forecast outcomes | `schemas/calibration-ledger.schema.json` | append-only scoring inputs |
| Gate execution | `scripts/badf_gate.py` | one canonical validator; no second gate |

If two artifacts claim the same authority function, processing stops with `AUTHORITY_CONFLICT`.

## 4. Decision layers and order

The order is mandatory and fail-closed:

1. **L0 Constitution** — classify the action, resolve reserved actions/roles, and confirm a current delegation envelope.
2. **L1 Binding and evidence** — freeze question, options, repository, base/head/result trees, evidence set, and all policy digests.
3. **L2 Hard rules** — evaluate legal/policy prohibitions, verified blockers, conflicts, self-approval, quorum, freshness, and completeness. A failure is not sent to weighting.
4. **L3 Risk** — evaluate residual risk separately from support. Missing or contradictory risk evidence yields `HOLD` or `ESCALATE`.
5. **L4 Council support** — aggregate eligible sealed ballots deterministically across decision criteria.
6. **L5 Authority** — in v0.1 emit only `RECOMMEND_AUTHORIZE`, `HOLD`, `REJECT`, `ESCALATE`, or `HUMAN_REQUIRED`. A future active policy may emit `BOARD_AUTHORIZED` only after ratification.

Ten approving ballots plus one verified hard blocker is `REJECT` or `HOLD`, never 91% approval.

## 5. Problem and option freeze

Every decision begins as a bounded problem state:

```text
initial_state + observed_facts + goal_state + constraints
+ allowed_operations + forbidden_operations + unknowns
+ candidate_options + success_metrics + failure/stop_conditions
```

The chair freezes the question, option identifiers, artifact/content-tree identity, evidence manifest, decision class, mandatory lenses, policy epochs, and expiry. Ballots over different digests do not form a council.

## 6. Council rounds

| Round | Operation | Authority limit |
| --- | --- | --- |
| R0 | Chair freezes inputs and digests | cannot choose outcome |
| R1 | Independent sealed analysis | no cross-member influence |
| R2 | Structural ballot validation | invalid ballots excluded with reasons |
| R3 | Anonymous argument/evidence cross-review | critiques arguments, not identities |
| R4 | Targeted blocker and contradiction challenge | minority risks preserved |
| R5 | Final sealed re-vote | binds the same or explicitly re-frozen digest |
| R6 | Deterministic aggregation | no LLM arithmetic |
| R7 | Chair writes explanation | cannot change votes or thresholds |
| R8 | Rule/risk/authority disposition | v0.1 stops at advisory disposition |

`APPROVE_WITH_CONDITIONS` is a `HOLD` until every condition is mechanically closed. `ABSTAIN` contributes no weight and declares non-coverage. `INSUFFICIENT_EVIDENCE` requests evidence; it is not a negative or partial vote.

## 7. Two independent weight systems

Decision-criterion weights express what BST values. Evaluator weights express how much a ballot contributes for a specific criterion. They are never substituted for each other.

All values use integer basis points (`0..10000`). Floating-point arithmetic is not authoritative.

For eligible ballot `i` and criterion `c`:

```text
raw_weight[i,c]
  = relevance_bp
  * calibration_bp
  * evidence_coverage_bp
  * freshness_bp
  * independence_bp
```

No factor comes from model brand, model price, seat title, or self-reported confidence. `calibration_bp` is derived from an eligible domain ledger; an uncalibrated shadow participant receives the fixed prior declared in policy. `evidence_coverage_bp` is recomputed from the frozen evidence manifest. `freshness_bp` is selected from policy buckets using stored timestamps. `independence_bp` is selected from the fixed correlation-cluster table.

For option `o` and criterion `c`:

```text
N = sum(raw_weight[i,c] * probability_satisfy_bp[i,o,c])
D = sum(raw_weight[i,c])
criterion_support_bp[o,c] = floor((2*N + D) / (2*D))
```

This is exact integer round-half-up. `D == 0` yields `INSUFFICIENT_EVIDENCE`.

Overall support is:

```text
N = sum(criterion_weight_bp[c] * criterion_support_bp[o,c])
D = 10000
overall_support_bp[o] = floor((2*N + D) / (2*D))
```

Ties within the policy margin are not broken by the chair; they yield `HOLD` and request discriminating evidence. Raw and normalized weights, exclusions, cluster discounts, intermediate criterion results, and rounding residues are recorded in the dossier.

## 8. Independence and correlation

Quorum counts distinct eligible ballots **and** the minimum distinct independence clusters declared for the decision class. Multiple roles using the same provider/model family/context lineage are a correlated cluster, not independent replicas. The fixed discount table in `decision-policy.json` is used in v0.1; empirical error correlation may replace it only through a later policy change.

A member is ineligible when it authored the work, shares the authoring run, has an undeclared conflict, does not bind the frozen digest, lacks the required lens, duplicates a run identity, or cannot establish the structural identity fields required by the registry.

## 9. Support and risk remain separate

Council support asks which permitted option is most likely to satisfy the criteria. Risk asks whether the residual downside fits BST's risk appetite. Risk uses stored integer probability, impact, and exposure inputs and preserves each risk dimension. Security, privacy, legality, credentials, destructive production data changes, and constitutional authority are not averaged into business value.

An option is recommendable only when:

```text
constitution_permits
AND evidence_complete_and_current
AND hard_rules_pass
AND independent_quorum_passes
AND mandatory_lenses_pass
AND overall_support_meets_threshold
AND residual_risk_within_every_dimension
AND no_verified_blocker
AND conditions_closed
```

## 10. C3A and C3R delegation

`C3A` and `C3R` are sub-classifications of existing `C3`; they do not change the authority matrix in v0.1.

- **C3A — high impact, reversible candidate:** may be considered for later board delegation only when no reserved action is involved, every material effect is bounded and reversible, canary and automatic stop/rollback are executable, evidence is complete, and the future ratified charter names the exact action/target/environment/time window.
- **C3R — reserved/constitutional:** authority-policy change, authority expansion, legal/privacy acceptance, credential handling, destructive production data operation, mandatory-gate waiver, irreversible action, external contractual commitment, major capital commitment, or human-reserved boundary. Always requires the BST human principal.

Ambiguity selects `C3R`. v0.1 routes both `C3A` and `C3R` to `HUMAN_REQUIRED`.

## 11. Board-authority evidence

A later active board authorization must be a content-addressed `decision-dossier` binding:

- question, options, repository, target branch, base/head/result tree, and composed verification;
- exact decision-policy, risk-appetite, council-registry, authority-matrix, and calibration-ledger digests;
- evidence manifest and expiry;
- every accepted/rejected ballot digest and exclusion reason;
- hard-rule, risk, quorum, mandatory-lens, support, condition, and conflict results;
- delegation receipt naming actor/role/action/target/environment/time/work package/conditions;
- separation of author, reviewers, chair, authority engine, and integration controller.

Any drift makes the dossier `STALE_EVIDENCE`; reconciliation precedes retry.

## 12. Autonomous merge predicate

The canonical workspace is GitHub-native: remote source ref + immutable commits/trees + PR identity + composed-result tree. Local `git worktree` state is not part of decision identity.

A future integration controller may merge only when all predicates are true:

```text
policy_mode == ACTIVE
AND decision_class is delegated
AND dossier_disposition == BOARD_AUTHORIZED
AND exact composed tree is current and verified
AND required CI and challenge evidence PASS
AND quorum, lenses, support, risk and conditions PASS
AND no verified blocker or conflict
AND rollback/recovery contract is executable
AND author supplied no independent approval
AND delegation and executor structural identity are current
AND GitHub protected-branch/ruleset controls permit the act
```

In v0.1, `autonomous_merge.eligible` is schema-fixed to `false`. No file in this unit enables auto-merge, modifies a ruleset, issues a credential, or performs a merge.

## 13. Calibration and performance ledger

Every forecast with an observable outcome becomes an append-only, hash-chained calibration event. Record the forecast before outcome disclosure; later bind the observed outcome, observation window, provenance, and proper-score components. Maintain calibration by domain and criterion, including observation count, Brier score, blocker precision/recall, false-block rate, missed-incident rate, and error correlation where available.

The ledger may lower, cap, or suspend epistemic weight. It cannot grant a role, waive a blocker, lower a decision class, or authorize an action. Sparse domains remain `UNCALIBRATED` and use the policy prior only in shadow mode.

## 14. Historical shadow protocol

Shadowing replays historical BADF decisions without changing their outcomes:

1. freeze a stratified population and case manifest before looking at aggregate results;
2. reconstruct only evidence available at each historical decision time;
3. prevent outcome leakage: hide the historical outcome and later discussion until R1/R5 ballots are sealed;
4. include approvals, rejections, blockers, conditions, C2/C3, authority bypasses, evidence failures, and operational decisions;
5. label the counterfactual expected disposition and actual outcome independently;
6. run the exact same inputs at least twice to prove deterministic aggregation;
7. measure false authorization, false block, missed blocker, quorum inflation, calibration, disagreement resolution, evidence cost, latency, and abstention;
8. publish non-coverage and adverse cases; never delete a failed shadow.

The initial corpus should include the authority-reservation decision (`BADF-DEC-0003`), the governed gate-transition decision (`BADF-DEC-0007`), historical verification/council records around PR #208 and Issue #211, identity attribution (#261), and the substring-matching defect (#289), plus a frozen stratified sample selected before scoring.

Candidate activation thresholds, subject to later human ratification:

- zero false authorizations on verified hard-blocker and `C3R` cases;
- one-sided 95% upper confidence bound on false-authorization rate at or below the ratified appetite;
- 100% repeated-run aggregation identity;
- zero accepted quorum-inflation or stale-digest cases;
- 100% preservation of verified minority blockers;
- calibration measurably better than the declared unweighted/prior baseline in sufficiently populated domains;
- false-block rate, decision latency, evidence cost, and abstention rate explicitly accepted by the BST Principal.

No threshold is deemed met by this design document.

## 15. Activation ladder

```text
DESIGNED
  -> IMPLEMENTED
  -> VALIDATED
  -> SHADOWED
  -> RATIFIED
  -> ACTIVE
```

| Rung | Required result | Authority effect |
| --- | --- | --- |
| DESIGNED | this contract, policies, schemas, drift tests | none |
| IMPLEMENTED | canonical validator loads and evaluates artifacts; no second gate | none |
| VALIDATED | negative-first, mutation, arithmetic, drift, adversarial tests | none |
| SHADOWED | historical corpus and metrics sealed | none |
| RATIFIED | BST Principal approves policy/risk/delegation envelope | explicit bounded delegation only |
| ACTIVE | digest-pinned controller admitted; rulesets and structural identity verified | only the ratified envelope |

Each rung is a separate governed work package. An agent board cannot vote itself from one rung to the next.

## 16. Stop and failure semantics

Stop with `HOLD`, `ESCALATE`, or `HUMAN_REQUIRED` on authority conflict, unknown decision class, missing required lens, insufficient independent clusters, evidence or policy drift, contradictory ballots/findings, outcome-unknown mutation, condition present, budget exhaustion, or inability to establish structural actor identity. Retries must change evidence, hypothesis, option, or policy input; identical retries are refused.

## 17. Non-coverage

This v0.1 contract does not prove that weighted aggregation improves BADF decisions; establish a calibrated council; define an active controller implementation; amend `badf/authority-matrix.json`; create structural identities; change GitHub rulesets; or authorize any merge. Those are later rungs and, where authority changes, human-reserved C3 decisions.
