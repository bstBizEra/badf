"""badf-engineering-verification VER-B (BADF-WP-0103 / GOV-0086): typed G08 evidence, the
verification record, and `badf_gate.py verify`.

VER-A froze the two-plane contract; this rung makes its shapes checkable. Four typed schemas
specialize evidence.schema.json for the G08 types with a CLOSED `binding` (the BLD-B pattern,
additive: generic objects stay admissible, so WP-2026-0010's historical dossier is untouched).
`check_g08_binding` in EVIDENCE_RULES refuses a typed review that is a bare PASS (VER-I10/I11),
an observation whose producer is an `agent` (VER-I08), a contract result that does not map onto
the evidence outcome (VER-I14: INDETERMINATE -> BLOCKED, never PASS), and a binding that
disagrees with the artifact the gate opens. `validate_verification_record` checks the record
that carries ballots, independence, findings, synthesis and the matrix: sealed digest equality,
no duplicate reviewer, no author ballot, findings preserved across synthesis (VER-I12), matrix
refs that resolve, VERIFIED rows with no open major finding and a composed observation
(VER-I15), non-coverage declared, and no authority granted (VER-I18). No executor, no runner.
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

WP = "WP-2026-9999"  # the unallocatable sentinel (GOV-0085): never a real ledger id
G08 = ("independent-review", "integration-test", "contract-test", "composed-tree-test")
SHA = "0" * 40
DIGEST = "sha256:" + "a" * 64
ASSURANCE_FINDING_FIELDS = ("finding_id", "kind", "severity", "baseline_ref", "observed_ref", "affected_elements",
                            "evidence_locations", "expected", "observed", "impact", "failure_scenario",
                            "recommendation_direction", "status", "non_coverage")


def finding(fid="VF-001", **over):
    f = {"finding_id": fid, "kind": "REGRESSION", "severity": "MAJOR", "baseline_ref": "REQ-021", "observed_ref": SHA,
         "affected_elements": [], "evidence_locations": ["src/payments.py:117-125"], "expected": "retry once",
         "observed": "retries forever", "impact": "payment double-charge", "failure_scenario": "timeout on first call",
         "recommendation_direction": "bound the retry", "status": "OPEN", "non_coverage": [], "lens": "correctness",
         "reported_by": ["BALLOT-001"], "also_reported_by": [], "requirement_refs": ["REQ-021"], "evidence_refs": []}
    f.update(over); return f


def record(**over):
    rec = {"schema_version": "1.0.0", "id": f"VR-{WP}-G08", "work_package_id": WP, "gate": "G08",
           "target": {"source_revision": SHA, "target_base_sha": SHA, "expected_content_tree": SHA, "sealed_input_digest": DIGEST},
           "change_class": "C1", "lenses_routed": ["correctness"],
           "ballots": [{"ballot_id": "BALLOT-001", "reviewer": "reviewer-a", "principal_type": "agent", "reviewer_run_id": "run-a",
                        "sealed_input_digest": DIGEST, "verdict": "APPROVE_WITH_CONDITIONS", "finding_ids": ["VF-001"],
                        "non_coverage": [{"surface": "concurrency", "reason": "not executable here"}]}],
           "independence": {"reviewer_run_id": "run-a", "author_run_id": "run-build", "same_execution": False,
                            "sealed_input_digest": DIGEST, "prior_findings_visible": False, "author_reasoning_visible": False,
                            "cross_pass_communication_before_ballot": False, "target_digest_equal": True, "conflicts_of_interest": []},
           "findings": [finding()], "synthesis": {"withdrawn": [], "downgraded": []},
           "evidence_index": [f"EVD-{WP}-G08-integration-test", f"EVD-{WP}-G08-composed-tree-test"],
           "matrix": [{"claim_ref": "AC-021", "change_ref": "CHG-14", "review_refs": ["BALLOT-001"],
                       "integration_refs": [f"EVD-{WP}-G08-integration-test"], "contract_refs": [],
                       "composed_refs": [f"EVD-{WP}-G08-composed-tree-test"], "result": "PARTIAL"}],
           "non_coverage": [{"surface": "security assurance", "reason": "badf-security-assurance is named, not built"}],
           "authority": {"verification_authority": False}, "recorded_at": "2026-08-31T00:00:00Z"}
    rec.update(over); return rec


class SchemaTests(unittest.TestCase):
    def test_four_schemas_specialize_evidence_schema_and_close_the_binding(self):
        core = json.loads((gate.ROOT / "schemas/evidence.schema.json").read_text(encoding="utf-8"))
        for t in G08:
            p = gate.ROOT / "schemas" / f"{t}.schema.json"; self.assertTrue(p.is_file(), t)
            s = json.loads(p.read_text(encoding="utf-8"))
            self.assertTrue(set(core["required"]) <= set(s["required"]), f"{t}: must require the evidence core")
            self.assertIn("binding", s["required"]); self.assertEqual([t], s["properties"]["evidence_type"]["enum"])
            self.assertFalse(s["properties"]["binding"].get("additionalProperties", True), f"{t}: binding must be closed")

    def test_verification_record_schema_reuses_the_assurance_finding_item(self):
        s = json.loads((gate.ROOT / "schemas/verification-record.schema.json").read_text(encoding="utf-8"))
        self.assertFalse(s.get("additionalProperties", True))
        for key in ("target", "change_class", "lenses_routed", "ballots", "independence", "findings", "synthesis",
                    "evidence_index", "matrix", "non_coverage", "authority", "recorded_at"):
            self.assertIn(key, s["required"], key)
        item = s["properties"]["findings"]["items"]
        for field in ASSURANCE_FINDING_FIELDS + ("lens", "reported_by", "also_reported_by", "requirement_refs", "evidence_refs"):
            self.assertIn(field, item["required"], field)
        self.assertFalse(item.get("additionalProperties", True))
        self.assertEqual([False], s["properties"]["authority"]["properties"]["verification_authority"]["enum"])
        self.assertEqual([False], s["properties"]["independence"]["properties"]["same_execution"]["enum"])


class G08RuleTests(unittest.TestCase):
    """EVIDENCE_RULES for the four G08 types: additive, artifact-opening, never a name."""

    def _evidence(self, kind, artifact_text, binding, producer_type="controller", outcome="PASS"):
        tmp = Path(tempfile.mkdtemp(prefix="badf-g08-rule-")); self.addCleanup(shutil.rmtree, tmp, True)
        art = tmp / "artifact.txt"; art.write_text(artifact_text, encoding="utf-8")
        ev = {"schema_version": "1.0.0", "id": f"EVD-{WP}-G08-{kind}", "work_package_id": WP, "gate": "G08", "claim": "x",
              "evidence_type": kind, "producer": {"id": "t", "type": producer_type}, "source_revision": SHA, "target": "bstBizEra/badf:main",
              "toolchain": {"name": "t", "version": "1"}, "operation": "t", "started_at": "2026-01-01T00:00:00Z",
              "completed_at": "2026-01-01T00:00:00Z", "outcome": outcome, "artifact": "x", "digest": gate.sha256(art)}
        if binding is not None:
            ev["binding"] = binding
        return art, ev

    def _target(self): return {"source_revision": SHA, "target_base_sha": SHA, "expected_content_tree": SHA, "sealed_input_digest": DIGEST}

    def _review(self, **over):
        b = {"target": self._target(), "lens": "correctness",
             "reviewer": {"identity": "reviewer-a", "reviewer_run_id": "run-a", "principal_type": "agent"},
             "independence": {"reviewer_run_id": "run-a", "author_run_id": "run-build", "same_execution": False,
                              "sealed_input_digest": DIGEST, "prior_findings_visible": False, "author_reasoning_visible": False,
                              "cross_pass_communication_before_ballot": False, "target_digest_equal": True, "conflicts_of_interest": []},
             "findings": [], "non_coverage": [{"surface": "concurrency", "reason": "not executable here", "impact": "ordering unknown"}],
             "completion": {"inspected_complete_diff": True, "inspected_call_sites": True}, "verdict": "APPROVE"}
        b.update(over); return b

    def _execution(self, **over):
        e = {"runtime": "badf_compose.py", "command": "python3 -m unittest discover -s tests", "working_directory": ".",
             "environment": {"python": "3.13"}, "toolchain": {"name": "unittest", "version": "3.13"}, "fixtures_epoch": "none",
             "seed": "none", "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z", "exit_code": 0,
             "tests": {"total": 12, "passed": 12, "failed": 0, "skipped": 0, "quarantined": 0}, "output_digest": DIGEST}
        e.update(over); return e

    def test_all_four_types_carry_a_rule_and_generic_objects_stay_admissible(self):
        for t in G08:
            self.assertIs(gate.EVIDENCE_RULES.get(t), gate.check_g08_binding, t)
        wp10 = gate.ROOT / "work" / "WP-2026-0010" / "evidence" / "G08"
        for t in G08:  # the only historical G08 objects: generic (no binding) -> untouched
            ev = json.loads((wp10 / f"{t}.json").read_text(encoding="utf-8")); self.assertNotIn("binding", ev)
            gate.check_g08_binding(gate.ROOT / ev["artifact"], {}, ev)

    def test_typed_review_refuses_bare_pass_and_verdict_contradicting_findings(self):
        art, ev = self._evidence("independent-review", "review\n", self._review()); gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("independent-review", "review\n", self._review(non_coverage=[]))
        with self.assertRaisesRegex(gate.ValidationError, "VER-I10|VER-I11|non_coverage"): gate.check_g08_binding(art, {}, ev)
        permitted = self._review(non_coverage=[], completion={"inspected_complete_diff": True, "inspected_call_sites": True,
                                                              "comprehensive_coverage_permitted_by": "review contract C1 docs-only"})
        art, ev = self._evidence("independent-review", "review\n", permitted); gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("independent-review", "review\n", self._review(findings=[finding()], verdict="APPROVE"))
        with self.assertRaisesRegex(gate.ValidationError, "APPROVE.*OPEN|contradict"): gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("independent-review", "review\n", self._review(verdict="LGTM"))
        with self.assertRaises(gate.ValidationError): gate.check_g08_binding(art, {}, ev)

    def test_observations_refuse_an_agent_producer(self):
        log = "Ran 12 tests in 0.1s\n\nOK\n"
        binding = {"target": {"source_revision": SHA, "expected_content_tree": SHA}, "execution": self._execution(), "non_coverage": []}
        art, ev = self._evidence("integration-test", log, binding); gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("integration-test", log, binding, producer_type="agent")
        with self.assertRaisesRegex(gate.ValidationError, "agent.*VER-I08|VER-I08"): gate.check_g08_binding(art, {}, ev)

    def test_integration_binding_counts_must_agree_with_the_log(self):
        binding = {"target": {"source_revision": SHA, "expected_content_tree": SHA}, "execution": self._execution(), "non_coverage": []}
        art, ev = self._evidence("integration-test", "Ran 11 tests in 0.1s\n\nOK\n", binding)
        with self.assertRaisesRegex(gate.ValidationError, "log|Ran"): gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("integration-test", "439 passed in 16.19s\nexit=0\n", binding); gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("integration-test", "439 passed in 16.19s\nexit=2\n", binding)
        with self.assertRaisesRegex(gate.ValidationError, "exit"): gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("integration-test", "nothing measurable here\n", binding)
        with self.assertRaisesRegex(gate.ValidationError, "cannot be verified"): gate.check_g08_binding(art, {}, ev)

    def test_contract_result_maps_onto_outcome_and_indeterminate_never_passes(self):
        def b(result): return {"surface": "api-contract", "contract_ref": "api-contract:v1", "target": {"source_revision": SHA, "expected_content_tree": SHA},
                               "execution": {"runtime": "ci", "command": "x", "exit_code": 0, "output_digest": DIGEST,
                                             "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z"},
                               "result": result, "non_coverage": []}
        art, ev = self._evidence("contract-test", "conformant\n", b("CONFORMANT")); gate.check_g08_binding(art, {}, ev)
        for result in ("INDETERMINATE", "NONCONFORMANT", "NOT_APPLICABLE"):
            art, ev = self._evidence("contract-test", "x\n", b(result), outcome="PASS")
            with self.assertRaisesRegex(gate.ValidationError, "VER-I14|outcome"): gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("contract-test", "x\n", b("INDETERMINATE"), outcome="BLOCKED"); gate.check_g08_binding(art, {}, ev)

    def test_composed_binding_must_agree_with_the_artifact_tree(self):
        tree = "672da1efe145a9ff8e3b89e1b13899b6f086e9e8"
        def b(**over):
            x = {"target": {"source_revision": SHA, "expected_content_tree": tree},
                 "composition": {"target_base_sha": SHA, "merge_method": "squash", "recorded_expected_content_tree": tree,
                                 "recomputed_content_tree": tree, "equal": True},
                 "execution": {"runtime": "badf_compose.py", "suite_pattern": "test_x.py", "exit_code": 0, "output_digest": DIGEST,
                               "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z"},
                 "staleness": "CURRENT", "non_coverage": []}
            x.update(over); return x
        text = f"BADF COMPOSE: base 6814a24 + candidate ed47d60 -> composed 6c1d43a (tree 822ba4c)\n  composition: CURRENT (content tree {tree[:7]}, recorded for base 6814a24)\nBADF COMPOSE PASS\n"
        art, ev = self._evidence("composed-tree-test", text, b()); gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("composed-tree-test", text, b(composition={"target_base_sha": SHA, "merge_method": "squash",
                                 "recorded_expected_content_tree": tree, "recomputed_content_tree": "b" * 40, "equal": True}))
        with self.assertRaisesRegex(gate.ValidationError, "tree"): gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("composed-tree-test", text, b(composition={"target_base_sha": SHA, "merge_method": "squash",
                                 "recorded_expected_content_tree": tree, "recomputed_content_tree": tree, "equal": False}))
        with self.assertRaisesRegex(gate.ValidationError, "equal|VER-I15"): gate.check_g08_binding(art, {}, ev)
        art, ev = self._evidence("composed-tree-test", text, b(staleness="TARGET_MOVED"))
        with self.assertRaisesRegex(gate.ValidationError, "CURRENT|stale"): gate.check_g08_binding(art, {}, ev)


class VerifyRecordTests(unittest.TestCase):
    def _path(self, rec):
        tmp = Path(tempfile.mkdtemp(prefix="badf-verify-")); self.addCleanup(shutil.rmtree, tmp, True)
        p = tmp / "verification-record.json"; p.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8"); return p

    def test_verify_accepts_a_coherent_record_and_grants_no_authority(self):
        out = gate.validate_verification_record(self._path(record()))
        self.assertIn("BADF VERIFY PASS", out); self.assertIn("grants no verification authority", out)

    def test_verify_refuses_invented_ballot_digest_duplicate_reviewer_and_author_ballot(self):
        r = record(); r["ballots"][0]["sealed_input_digest"] = "sha256:" + "b" * 64
        with self.assertRaisesRegex(gate.ValidationError, "sealed|VER-I05"): gate.validate_verification_record(self._path(r))
        r = record(); r["ballots"].append(dict(r["ballots"][0], ballot_id="BALLOT-002", reviewer_run_id="run-b"))
        with self.assertRaisesRegex(gate.ValidationError, "duplicate|VER-I19"): gate.validate_verification_record(self._path(r))
        r = record(); r["ballots"][0]["reviewer_run_id"] = "run-build"
        with self.assertRaisesRegex(gate.ValidationError, "author|VER-I04"): gate.validate_verification_record(self._path(r))

    def test_verify_preserves_findings_across_synthesis(self):
        r = record(); r["ballots"][0]["finding_ids"] = ["VF-001", "VF-002"]
        with self.assertRaisesRegex(gate.ValidationError, "VF-002.*(withdrawn|VER-I12)|VER-I12"): gate.validate_verification_record(self._path(r))
        r["synthesis"]["withdrawn"] = [{"finding_id": "VF-002", "reason": "duplicate of VF-001 at the same location", "by": "synthesis"}]
        gate.validate_verification_record(self._path(r))
        r = record(); r["synthesis"]["downgraded"] = [{"finding_id": "VF-001", "from": "MAJOR", "to": "MINOR"}]
        with self.assertRaises(gate.ValidationError): gate.validate_verification_record(self._path(r))  # decision_ref is required
        r = record(); r["synthesis"]["downgraded"] = [{"finding_id": "VF-404", "from": "MAJOR", "to": "MINOR", "decision_ref": "BADF-DEC-0009"}]
        with self.assertRaisesRegex(gate.ValidationError, "VF-404"): gate.validate_verification_record(self._path(r))

    def test_verify_matrix_rows_resolve_and_verified_needs_no_open_major_and_a_composed_observation(self):
        r = record(); r["matrix"][0]["review_refs"] = ["BALLOT-404"]
        with self.assertRaisesRegex(gate.ValidationError, "BALLOT-404"): gate.validate_verification_record(self._path(r))
        r = record(); r["matrix"][0]["integration_refs"] = ["EVD-nope"]
        with self.assertRaisesRegex(gate.ValidationError, "EVD-nope"): gate.validate_verification_record(self._path(r))
        r = record(); r["matrix"][0]["result"] = "VERIFIED"
        with self.assertRaisesRegex(gate.ValidationError, "VERIFIED.*(OPEN|MAJOR)"): gate.validate_verification_record(self._path(r))
        r = record(findings=[finding(status="RESOLVED")]); r["matrix"][0]["result"] = "VERIFIED"; gate.validate_verification_record(self._path(r))
        r = record(findings=[finding(status="RESOLVED")]); r["matrix"][0].update(result="VERIFIED", composed_refs=[])
        with self.assertRaisesRegex(gate.ValidationError, "composed|VER-I15"): gate.validate_verification_record(self._path(r))

    def test_verify_refuses_an_APPROVE_ballot_citing_its_own_open_blocking_finding(self):
        """#211: a ballot may not carry a verdict its own cited findings contradict.

        The matrix layer already refuses a VERIFIED row over an OPEN blocking finding, and
        `check_g08_binding` refuses the same shape on an independent-review evidence binding
        (badf_gate.py:1742). The record's own ballot layer did not, so `verify` PASSed a record
        whose ballot said APPROVE while citing an OPEN MAJOR it had raised itself.

        Scope is strict APPROVE only, deliberately. APPROVE_WITH_CONDITIONS over an OPEN finding
        is the honest conditional arc -- it is this module's own baseline fixture -- and REJECT
        over open findings is the honest rejecting arc. Both are pinned below so a later change
        cannot quietly widen this refusal into them.
        """
        r = record()
        r["ballots"][0]["verdict"] = "APPROVE"
        with self.assertRaisesRegex(gate.ValidationError, "APPROVE.*(contradicts|OPEN)|VF-001"):
            gate.validate_verification_record(self._path(r))

        # the two honest arcs stay valid -- negative controls, not decoration
        r = record()
        r["ballots"][0]["verdict"] = "REJECT"
        gate.validate_verification_record(self._path(r))

        gate.validate_verification_record(self._path(record()))  # APPROVE_WITH_CONDITIONS baseline

        # APPROVE is fine once nothing open is cited
        r = record(findings=[finding(status="RESOLVED")])
        r["ballots"][0]["verdict"] = "APPROVE"
        gate.validate_verification_record(self._path(r))

    def test_verify_refuses_an_APPROVE_ballot_associated_by_either_join(self):
        """#211: the association is two-sided, so the refusal must be too.

        A ballot cites findings via `finding_ids`; a finding names its reporters via
        `reported_by` / `also_reported_by`. The record checks each for CONTAINMENT and
        neither for RECIPROCITY -- nothing requires the two to agree. So an APPROVE
        ballot could carry `finding_ids: []` while the findings side still asserted it
        reported an OPEN MAJOR, and a refusal walking only `finding_ids` admitted it.
        That is the same proposition, reachable from the other side of the join.

        Found by asking what my own criteria did not name (BADF-QA read it; measured here).
        """
        r = record()
        r["ballots"][0]["verdict"] = "APPROVE"
        r["ballots"][0]["finding_ids"] = []          # association lives only on the finding
        for row in r["matrix"]:                      # deny the matrix layer an incidental catch
            if row["result"] == "VERIFIED":
                row["result"] = "NOT_VERIFIED"
        with self.assertRaisesRegex(gate.ValidationError, "APPROVE.*(contradicts|OPEN)|VF-001"):
            gate.validate_verification_record(self._path(r))

        # and the mirror: cited by the ballot, silent on the finding
        r = record(findings=[finding(reported_by=["BALLOT-OTHER"])])
        r["ballots"][0]["verdict"] = "APPROVE"
        r["findings"][0]["reported_by"] = ["BALLOT-001"]
        with self.assertRaisesRegex(gate.ValidationError, "APPROVE.*(contradicts|OPEN)|VF-001"):
            gate.validate_verification_record(self._path(r))

    def test_verify_refuses_an_APPROVE_ballot_associated_only_via_also_reported_by(self):
        """#211 vector C: the third attribution surface, pinned separately from B.

        A finding's `reported_by` is mandatory and can be satisfied by a DIFFERENT ballot while
        the approving ballot's involvement rides `also_reported_by`. The union already covers
        this -- it walks `reported_by + also_reported_by` -- but nothing pinned it, so a later
        simplification dropping `also_reported_by` would pass every existing test.

        Raised by BADF-REV against 03dae4d (pre-union head, where it was genuinely open) and
        measured closed here; the code was right and the coverage was not. One case per vector,
        because a B-only test goes green while C is silent.
        """
        r = record()
        r["ballots"].append({**r["ballots"][0], "ballot_id": "BALLOT-002", "reviewer": "reviewer-b",
                             "reviewer_run_id": "run-b", "verdict": "REJECT", "finding_ids": ["VF-001"]})
        r["ballots"][0].update(verdict="APPROVE", finding_ids=[])
        r["findings"][0].update(reported_by=["BALLOT-002"], also_reported_by=["BALLOT-001"])
        for row in r["matrix"]:
            if row["result"] == "VERIFIED":
                row["result"] = "NOT_VERIFIED"
        # discriminates on THIS control's unique wording, not the substring it shares with the
        # older binding-layer control at badf_gate.py:1743 (BADF-REV's mechanical note)
        with self.assertRaisesRegex(gate.ValidationError, r"ballot BALLOT-001:.*associated with it"):
            gate.validate_verification_record(self._path(r))

    def test_verify_refuses_a_finding_weakened_outside_the_governed_path(self):
        """#271: the record defines justified routes for weakening and required neither.

        `synthesis.withdrawn[]` demands a `reason` and a `by`; `synthesis.downgraded[]`
        demands `from`/`to`/`decision_ref`. Neither was required, so a finding could be
        erased by setting `status: WITHDRAWN` directly -- with no reason and no `by` --
        and a downgrade entry could claim any severities while the finding carried a third.
        VER-I12 says synthesis cannot erase a finding; the unjustified route was free while
        the justified one was optional.

        EVERY fixture here is non-APPROVE, deliberately. The #211 ballot control refuses
        APPROVE-over-OPEN before synthesis is ever examined, so an APPROVE fixture goes
        green through that control and proves nothing about synthesis integrity. A green
        under APPROVE says nothing here. (Method constraint, #271.)
        """
        # D: status set directly, synthesis untouched -- erasure with no reason and no `by`
        r = record(findings=[finding(status="WITHDRAWN")])
        r["ballots"][0]["verdict"] = "REJECT"
        with self.assertRaisesRegex(gate.ValidationError, r"WITHDRAWN with no synthesis\.withdrawn"):
            gate.validate_verification_record(self._path(r))

        # the governed route stays valid: withdrawn entry present, finding not carried open
        r = record(findings=[], synthesis={"withdrawn": [{"finding_id": "VF-001", "reason": "duplicate",
                                                          "by": "reviewer-a"}], "downgraded": []})
        r["ballots"][0]["verdict"] = "REJECT"
        r["matrix"][0]["result"] = "UNVERIFIED"
        gate.validate_verification_record(self._path(r))

    def test_verify_refuses_a_withdrawal_entry_whose_finding_is_still_open(self):
        """#271, the symmetric half of the withdrawal case.

        Probe D catches `status: WITHDRAWN` with no entry -- erasure without justification.
        This catches the inverse: an entry present while the finding is still carried OPEN --
        justification without effect. The record then both carries the finding as open AND
        claims it withdrawn, and `withdrawn` is the escape hatch for findings NOT carried
        (badf_gate.py's `fid not in findings and fid not in withdrawn`), so the two states
        contradict. Same shape as the downgrade entry that describes nothing.

        Non-APPROVE fixture, per the method constraint.
        """
        r = record()
        r["ballots"][0]["verdict"] = "REJECT"
        r["synthesis"]["withdrawn"] = [{"finding_id": "VF-001", "reason": "fiat", "by": "nobody"}]
        with self.assertRaisesRegex(gate.ValidationError, r"withdraws VF-001 but the record still carries it"):
            gate.validate_verification_record(self._path(r))

    def test_verify_refuses_a_downgrade_entry_that_does_not_describe_its_finding(self):
        """#271, second site: `downgraded[].to` must match the severity the finding carries.

        `badf_gate.py` checked only that the downgraded id exists, so an entry could claim
        MAJOR -> MINOR while the finding still read MAJOR -- a justification describing
        nothing. Separate test from the withdrawal case on purpose: a shared case goes
        green while one site still disagrees, which is the lesson from the #211 union join
        where the code was right and the coverage silent.
        """
        r = record()
        r["ballots"][0]["verdict"] = "REJECT"
        r["synthesis"]["downgraded"] = [{"finding_id": "VF-001", "from": "MAJOR", "to": "MINOR",
                                          "decision_ref": "DEC-1"}]
        with self.assertRaisesRegex(gate.ValidationError, r"downgrades VF-001 to MINOR but the finding carries"):
            gate.validate_verification_record(self._path(r))

        # honest downgrade: the entry describes the finding it names
        r = record(findings=[finding(severity="MINOR")])
        r["ballots"][0]["verdict"] = "REJECT"
        r["synthesis"]["downgraded"] = [{"finding_id": "VF-001", "from": "MAJOR", "to": "MINOR",
                                          "decision_ref": "DEC-1"}]
        gate.validate_verification_record(self._path(r))

    def test_verify_requires_non_coverage_and_refuses_authority(self):
        r = record(non_coverage=[])
        with self.assertRaisesRegex(gate.ValidationError, "non-coverage|VER-I11"): gate.validate_verification_record(self._path(r))
        r = record(authority={"verification_authority": True})
        with self.assertRaises(gate.ValidationError): gate.validate_verification_record(self._path(r))

    def test_verify_cli_mirrors_assure(self):
        env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
        good = self._path(record()); bad = self._path(record(non_coverage=[]))
        r = subprocess.run([sys.executable, str(gate.ROOT / "scripts/badf_gate.py"), "verify", str(good)], capture_output=True, text=True, cwd=gate.ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertIn("BADF VERIFY PASS", r.stdout)
        r = subprocess.run([sys.executable, str(gate.ROOT / "scripts/badf_gate.py"), "verify", str(bad)], capture_output=True, text=True, cwd=gate.ROOT)
        self.assertEqual(r.returncode, 1); self.assertIn("BADF GATE FAIL", r.stderr)


class RegistryTests(unittest.TestCase):
    def test_registry_pin_is_at_least_implemented_and_skill_digest_unchanged(self):
        registry = json.loads((gate.ROOT / "badf/skill-registry.json").read_text(encoding="utf-8"))
        entry = next(e for e in registry["skills"] if e["name"] == "badf-engineering-verification")
        # VER-B floor; later rungs advance it.
        self.assertIn(entry["status"], ("IMPLEMENTED", "VALIDATED", "SHADOWED", "ACTIVE"))
        # #210: this assertion was spliced INTO the comment above by a semicolon edit and ran
        # for nobody -- `allowed_tools` appeared exactly once in this module, inside a comment.
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual(entry["digest"], gate.sha256(gate.ROOT / "skills/badf-engineering-verification/SKILL.md"))


if __name__ == "__main__":
    unittest.main()
