# Successor remaining-work plan — proposal only

WP-2026-0162, Issue365, frozen BADF-DEM-0147. Original WP0161 stays BLOCKED with immutable STOP and unchanged budget5. A new exact human decision must knowingly authorize future work; inherited source is unaccepted and prior compliance is not retroactively approved.

Inherited archive head: a8dd82f8f4860c5d08cba102d7790fc44b4da649. Tested production/test head:19c33c04ff9c473678f8747a1859cf1bcdeb306e. Archive source content tree for WP0161:7c544565f1dc9dd310113171f7c16389f57af71c. Bundle SHA256:cc6d18047350df5d49027371a301b255d0b703308c83a4010479e3ecb91ab1ad, Git blob2267195ea2b8736666265f7e4d983bbd28d560d3. Requires original main b9936e591530a74f919a86c80934b575c3a231e3. GitHub evidence-only commit62ec8957684ba77bb11632b9ff5ddb072547c587 archives the bundle; its controller remains baseline and must NOT be used as a changed framework pin.

## Prospective global budget and records

Proposed max_attempts5 means ONE first remaining-work pass plus at most FOUR corrective attempts shared across this entire successor. Every unexpected implemented verification failure followed by changed source/fixture/input, or independent-review corrective dispatch, consumes a corrective attempt. Expected initial failing-first obligations and successful planned phases do not refresh/reset that ceiling. The controller must record actual START/RETRY/STOP before transition; all delegates receive only remaining budget. Stop when fifth attempt fails or another correction is required. Existing C6 numerical RETRY>max_attempts is a refusal floor, NOT permission for a sixth implementation attempt. No per-task allowance, retrospective event rewriting or reset. Parent minimumsixsubstantive/tenconservativelyrecordedretryevents are acknowledged separately, never erased.

Before execution: accept exact successor human decision; isolate from immutable inherited archive; independently recheck current main/controller/source/demand/baselines and claim; declare actual actor/functionalseat separately; create true prospective S2 envelopes and enforce global budget; preserve unavailablehistoricalS2/seatnoncoverage. Existing original authorization and export remain byte-identical.

## Remaining obligations

Task5 source was already checked and independently APPROVED without findings:33tests/379.754s/all110writeboundaries, no skips. Inherit this engineering evidence, subject to fresh wholecandidate challenge; it is not overall acceptance or budget authority. No new Task5 source work is presumed; any newly identified fix uses the same global corrective budget and listed surfaces.

Task6 requirements and Task7 implementation/verification obligations follow, mapped to successor identities. Downstream admission references are context only, outside this decision.

## Task 6: Receipt compatibility, caller documentation and schema honesty

**Files:** Receipt schema, instance validation/schema-drift/intent-doc tests, README, project-instance/control-plane docs, new allocation operating doc and synthetic example.

**Interfaces:** Produces `expected_init_receipt_version(framework_revision: str) -> str` and `validate_init_receipt_contract(receipt: dict[str, Any]) -> None` in the gate. New output is 1.1.0 with allocation. Known historical 1.0.0 contracts remain supported only under their corroborated historical pin. Existing instance validation invokes this contract check before accepting receipt compatibility, then verifies allocation WP equals receipt/project/state WP and its fields are valid. It does not invent historical allocation evidence; arbitrary unknown pins or version flags do not obtain a legacy exemption.

- [ ] Write `test_known_historical_pin_legacy_receipt_remains_valid`, `test_post_change_receipt_allocation_deletion_and_version_downgrade_resigning_refuse`, `test_unknown_pinned_receipt_contract_refuses`, `test_new_receipt_allocation_is_bound_and_cannot_name_another_wp`, `test_allocation_envelope_and_wp_retained_bytes_match_receipt_digest`, `test_cli_docs_and_callers_have_no_implicit_allocator`, `test_examples_are_synthetic_not_approval_evidence`.
- [ ] RED: `python3 -m unittest tests.test_badf_instance_validation tests.test_badf_schema_drift tests.test_badf_intent_docs -v` plus new relevant tests; expected changed contract not implemented yet, not unrelated source drift.
- [ ] Update contracts/docs together: gather/retain source; independently reconcile; publish before bind; create reviewed bundle; invoke explicit CLI; distinguish preflight no protected writes from partial failure with held diagnostic records. Document local filesystem atomicity assumptions, unavailable Windows/network filesystem evidence, stale locks, sibling worktrees and out-of-band actors. Keep intent field table unchanged; allocation is CLI context, not new intent keys.
- [ ] Re-sign existing governed lockfile deliberately: `python3 scripts/badf_gate.py lock`; review exact paths changed. This is integrity maintenance, not authorization.
- [ ] GREEN: rerun focused doc/schema/instance commands, expected OK; commit checked slice with WP trailer.


## Task 7: Independent challenge, composed checks and governed handoff

**Files:** Actual successor work/session/verification evidence under `work/WP-2026-0162/`; original `work/WP-2026-0161/` is inherited read-only; existing PR/composition controls. No manufactured code review or human signature.

**Interfaces:** Each implementation task exports real RED/GREEN commands, exit statuses, logs/digests and commit identity to the coordinator. Fresh independent review consumes the exact composed candidate, not this plan alone.

- [ ] Establish the currently accepted owner, human authorization, C3 route, policy epoch, declared changed surfaces, build budget, delegated seats and independent lenses before any successor execution. Do not claim retrospective bootstrap compliance for original Tasks1–5. Use an isolated successor-authorized worktree only at execution time.
- [ ] Run focused allocation/reservation/transaction/intake/instance tests once on the composed result; retain skips, failures and non-coverage. Actual Linux and Windows checks must exercise atomic-directory contention and interruption; a parser mock cannot establish Windows runtime behavior. If Windows unavailable, report BLOCKED/NOT_RUN and obtain the applicable disposition rather than claiming cross-platform proof.
- [ ] Run `python3 scripts/badf_gate.py repo` and `python3 -m unittest discover -s tests -p 'test_*.py'` on the exact composed candidate. Both must actually complete; retain logs/exit status/digests. Interrupted or deferred full suite is NOT_RUN/NOT_COMPLETED, never PASS.
- [ ] Obtain fresh independent security/architecture/quality/composition challenge with all findings reconciled. Review the offline trust boundary, local-versus-global exclusivity, scoped lock ownership, failure journal and generated authority placeholders.
- [ ] Assemble actual G07/PR evidence through existing rules. Implementation authorization does not approve merge or C3 gate progression; obtain separate required decisions and repository approvals. Do not merge merely because agent consensus or CI is green.
- [ ] REFERENCE ONLY — separate downstream decisions, outside successor permission: after a legitimately landed candidate, record actual new BADF revision, repeat affected checks, and explicitly reconcile Bera's BizTrust authorization at the old framework pin before admission use. Fresh BizTrust WP claim is separate from `WP-2026-0161`.
- [ ] REFERENCE ONLY — separate downstream decisions, outside successor permission: generate BizTrust G00 only with exact authorized input and resolved/explicitly adjudicated #366 status defect, safe new allocation, clean target and appropriate pin. Generated dossier remains HUMAN_REQUIRED until its own named judgments, declarations, council when required and separate role approvals pass. `advance`/`instance` follow that evidence; runtime/release/deployment remain separate.


## Required refinements and exclusions

Task6 must reconcile control-plane historical init COMMITTED prose: generated AUTHORITY_CHECKED/OUTCOME_UNKNOWN is conservative; only linked token-owned durable reservation corroborates verified actual writes. Generic replay stays RECONCILE_FIRST; no automatic resume/reconciliation/cleanup and no gate authority. Pinned receipt schema eligibility is not approved version lineage: explicitly bind actual controller/source provenance and proposed compatibility cutover to actual candidate, retaining human acceptance dependency without a invented future commit or marker-only exemption.

Issue366, load_demand status enforcement, authority matrix/lifecycle and human-role policy changes are excluded. Wholecandidate includes inherited source and old stopped WP evidence; no claim of successful original-budget compliance. Corrective scope is exactly original filemap/expected_surfaces; no credential/integration/merge/pin/G00/runtime/release/deployment authority.

Actual Linux checks only qualify Linux. Windows is unavailable on the current host and remains NOT_RUN/BLOCKED until a real runner supplies evidence or the applicable separate authority records its required disposition. Successor authorization is NOT a Windows-proof waiver. Acceptance C3/G07 and merge remain separate; Bera's BizTrust exact original authorization needs actual new-pin reconciliation only after legitimate landing. A fresh BizTrust intake WP/claim and Issue366 resolution/adjudication precede real G00 generation; its own approvals precede advance/instance. No product status changes here.

## Immutable parent evidence boundary

All active sessions, global START/RETRY/STOP, dispatch envelopes, reviews and G07 verification records live only under work/WP-2026-0162. Original work/WP-2026-0161 is copied/read from the pinned archive unchanged; its entire original STOP/history and file bytes remain immutable. There is no old-WP glob in expected files or discovery_allowance. Inherited artifacts are baseline evidence only. Disclose their main-relative inherited delta separately at acceptance; do not represent it as an allowance to touch those files. No worker receives any parent-WP write path. Verify old-file hashes against the archived source before acceptance; refuse edits or deletions. Downstream pin/G00 bullets above are context for later separate authority, not additional successor actions.
