"""badf-engineering-verification VER-C (BADF-WP-0105 / GOV-0088): deterministic G08 controls in
the canonical gate.

VER-B made typed G08 objects checkable in isolation. This rung judges them against each other,
the Work Package and the composition record, as one PURE function -- `check_g08_dossier(dossier,
work_package, evidence, composition_record, record)`: no I/O, no git -- wired into
`validate_dossier` only for G08 dossiers claiming PASS / PASS_WITH_CONDITIONS. Seven controls:
C1 exact target (VER-I01), C2 one composed identity (VER-I05), C3 independence and quorum by change
class (VER-I04/I19), C4 runtime credit when the WP demands it (VER-I08), C5 per-artifact
non-coverage (VER-I11), C6 review blockers resolved (VER-I12), C7 composed-result authority
(VER-I15). Every control fires only on fields that are declared, so every dossier on main --
WP-2026-0010's generic G08 dossier included -- stays valid.
"""
import copy
import inspect
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import badf_gate as gate  # noqa: E402

WP = "WP-2026-9999"  # the unallocatable sentinel (GOV-0085)
SHA = "a" * 40
TREE = "b" * 40
BASE = "c" * 40
DIGEST = "sha256:" + "d" * 64


def dossier(**over):
    d = {"schema_version": "1.0.0", "id": f"DOS-{WP}-G08-v1", "work_package_id": WP, "gate": "G08", "policy_epoch": "x",
         "source_revision": SHA, "target": "bstBizEra/badf:main", "change_class": "C1", "author": "builder-a", "author_type": "agent",
         "evidence": [], "approvals": [], "conditions": [], "non_coverage": [], "exceptions": [], "risks": [],
         "disposition": "PASS", "created_at": "2026-08-31T00:00:00Z"}
    d.update(over); return d


def finding(fid="VF-001", **over):
    f = {"finding_id": fid, "kind": "REGRESSION", "severity": "MAJOR", "baseline_ref": "REQ-1", "observed_ref": SHA,
         "affected_elements": [], "evidence_locations": ["src/x.py:1-2"], "expected": "e", "observed": "o", "impact": "i",
         "failure_scenario": "f", "recommendation_direction": "r", "status": "OPEN", "non_coverage": [], "lens": "correctness",
         "reported_by": ["BALLOT-001"], "also_reported_by": [], "requirement_refs": [], "evidence_refs": []}
    f.update(over); return f


def evidence(kind, binding=None, producer="controller", outcome="PASS"):
    e = {"schema_version": "1.0.0", "id": f"EVD-{WP}-G08-{kind}", "work_package_id": WP, "gate": "G08", "claim": "x",
         "evidence_type": kind, "producer": {"id": "p", "type": producer}, "source_revision": SHA, "target": "bstBizEra/badf:main",
         "toolchain": {"name": "t", "version": "1"}, "operation": "t", "started_at": "2026-01-01T00:00:00Z",
         "completed_at": "2026-01-01T00:00:00Z", "outcome": outcome, "artifact": "x", "digest": DIGEST}
    if binding is not None:
        e["binding"] = binding
    return e


def review(**over):
    b = {"target": {"source_revision": SHA, "target_base_sha": BASE, "expected_content_tree": TREE, "sealed_input_digest": DIGEST},
         "lens": "correctness", "reviewer": {"identity": "reviewer-a", "reviewer_run_id": "run-a", "principal_type": "agent"},
         "independence": {"reviewer_run_id": "run-a", "author_run_id": "run-build", "same_execution": False, "sealed_input_digest": DIGEST,
                          "prior_findings_visible": False, "author_reasoning_visible": False, "cross_pass_communication_before_ballot": False,
                          "target_digest_equal": True, "conflicts_of_interest": []},
         "findings": [], "non_coverage": [{"surface": "s", "reason": "r"}],
         "completion": {"inspected_complete_diff": True, "inspected_call_sites": True}, "verdict": "APPROVE"}
    b.update(over); return b


def observation(kind, tree=TREE, non_coverage=None, **over):
    b = {"target": {"source_revision": SHA, "expected_content_tree": tree},
         "execution": {"runtime": "ci", "command": "x", "exit_code": 0, "output_digest": DIGEST,
                       "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:00:01Z"},
         "non_coverage": [{"surface": "s", "reason": "r"}] if non_coverage is None else non_coverage}
    if kind == "composed-tree-test":
        b["composition"] = {"target_base_sha": BASE, "merge_method": "squash", "recorded_expected_content_tree": tree,
                            "recomputed_content_tree": tree, "equal": True}
        b["staleness"] = "CURRENT"
    if kind == "contract-test":
        b["surface"] = "api-contract"; b["contract_ref"] = "c"; b["result"] = "CONFORMANT"
    b.update(over); return b


def objects(**over):
    o = {"independent-review": evidence("independent-review", review()),
         "integration-test": evidence("integration-test", observation("integration-test")),
         "contract-test": evidence("contract-test", observation("contract-test")),
         "composed-tree-test": evidence("composed-tree-test", observation("composed-tree-test"))}
    o.update(over); return o


COMP = {"target_base_sha": BASE, "expected_content_tree": TREE, "merge_method": "squash"}


def record(**over):
    r = {"schema_version": "1.0.0", "id": f"VR-{WP}-G08", "work_package_id": WP, "gate": "G08",
         "target": {"source_revision": SHA, "target_base_sha": BASE, "expected_content_tree": TREE, "sealed_input_digest": DIGEST},
         "change_class": "C2", "lenses_routed": ["correctness", "quality/test"],
         "ballots": [{"ballot_id": "BALLOT-001", "reviewer": "reviewer-a", "principal_type": "agent", "reviewer_run_id": "run-a",
                      "sealed_input_digest": DIGEST, "verdict": "APPROVE", "finding_ids": [], "non_coverage": [{"surface": "s", "reason": "r"}]},
                     {"ballot_id": "BALLOT-002", "reviewer": "reviewer-b", "principal_type": "agent", "reviewer_run_id": "run-b",
                      "sealed_input_digest": DIGEST, "verdict": "APPROVE", "finding_ids": [], "non_coverage": [{"surface": "s", "reason": "r"}]}],
         "independence": {"reviewer_run_id": "run-a", "author_run_id": "run-build", "same_execution": False, "sealed_input_digest": DIGEST,
                          "prior_findings_visible": False, "author_reasoning_visible": False, "cross_pass_communication_before_ballot": False,
                          "target_digest_equal": True, "conflicts_of_interest": []},
         "findings": [], "synthesis": {"withdrawn": [], "downgraded": []}, "evidence_index": [], "matrix": [],
         "non_coverage": [{"surface": "s", "reason": "r"}], "authority": {"verification_authority": False}, "recorded_at": "2026-08-31T00:00:00Z"}
    r.update(over); return r


def wp(**over):
    w = {"id": WP, "change_class": "C1"}; w.update(over); return w


class G08DossierControlTests(unittest.TestCase):
    def check(self, d=None, w=None, ev=None, comp=COMP, rec=None):
        return gate.check_g08_dossier(d or dossier(), w, objects() if ev is None else ev, comp, rec)

    def test_c1_target_must_match_dossier_and_composition_record(self):
        self.check()
        ev = objects(); ev["integration-test"]["binding"]["target"]["source_revision"] = "e" * 40
        with self.assertRaisesRegex(gate.ValidationError, "source_revision|C1"): self.check(ev=ev)
        ev = objects()
        for o in ev.values(): o["binding"]["target"]["expected_content_tree"] = "f" * 40
        ev["composed-tree-test"]["binding"]["composition"].update(recorded_expected_content_tree="f" * 40, recomputed_content_tree="f" * 40)
        with self.assertRaisesRegex(gate.ValidationError, "composition record|C1"): self.check(ev=ev)
        self.check(ev=ev, comp=None)  # no record on disk -> nothing to bind against; C2 still holds
        ev = objects(); ev["composed-tree-test"]["binding"]["composition"]["target_base_sha"] = "9" * 40
        with self.assertRaisesRegex(gate.ValidationError, "target_base_sha|C1"): self.check(ev=ev)

    def test_c2_all_objects_bind_one_content_tree(self):
        ev = objects(); ev["independent-review"]["binding"]["target"]["expected_content_tree"] = "f" * 40
        with self.assertRaisesRegex(gate.ValidationError, "one composed identity|C2"): self.check(ev=ev, comp=None)

    def test_c3_author_review_refused_unless_deviation_carried_and_quorum_by_class(self):
        ev = objects(); ev["independent-review"]["binding"]["independence"]["author_run_id"] = "run-a"
        with self.assertRaisesRegex(gate.ValidationError, "author|C3"): self.check(ev=ev)
        carried = dossier(conditions=[{"condition_id": "C-1", "statement": "An independent reviewer distinct from the author has not recorded an approval",
                                       "status": "OPEN", "severity": "Major", "blocking_scope": "G08", "owner": "quality_authority",
                                       "closure_predicate": "x", "closure_authority": "quality_authority"}])
        self.check(d=carried, ev=ev)  # the single-collaborator deviation, carried not hidden
        ev = objects(); ev["independent-review"]["binding"]["reviewer"]["identity"] = "builder-a"
        with self.assertRaisesRegex(gate.ValidationError, "author|C3"): self.check(ev=ev)
        d2 = dossier(change_class="C2")
        with self.assertRaisesRegex(gate.ValidationError, "verification record|C3"): self.check(d=d2)
        self.check(d=d2, rec=record())
        one = record(); one["ballots"] = one["ballots"][:1]
        with self.assertRaisesRegex(gate.ValidationError, "quorum|C3"): self.check(d=d2, rec=one)
        with self.assertRaisesRegex(gate.ValidationError, "lens|C3"): self.check(d=d2, rec=record(lenses_routed=["correctness"]))
        d3 = dossier(change_class="C3")
        with self.assertRaisesRegex(gate.ValidationError, "quorum|C3"): self.check(d=d3, rec=record())

    def test_c4_runtime_required_refuses_generic_agent_observation_only_when_declared(self):
        ev = objects(**{"integration-test": evidence("integration-test", None, producer="agent")})
        self.check(ev=ev)  # undeclared -> silent
        with self.assertRaisesRegex(gate.ValidationError, "runtime_required|C4"): self.check(w=wp(verification_obligations={"runtime_required": True}), ev=ev)
        self.check(w=wp(verification_obligations={"runtime_required": True}))
        na = objects(**{"contract-test": evidence("contract-test", None, producer="agent", outcome="NOT_APPLICABLE")})
        self.check(d=dossier(non_coverage=[{"evidence_type": "contract-test", "reason": "r", "declared_by": "x"}]),
                   w=wp(verification_obligations={"runtime_required": True}), ev=na)  # declared non-coverage is not a claim

    def test_c5_empty_non_coverage_refused_unless_permitted(self):
        ev = objects(**{"integration-test": evidence("integration-test", observation("integration-test", non_coverage=[]))})
        with self.assertRaisesRegex(gate.ValidationError, "non.coverage|C5"): self.check(ev=ev)
        self.check(w=wp(verification_obligations={"comprehensive_coverage_permitted_for": ["integration-test"]}), ev=ev)

    def test_c6_open_blocking_finding_refuses_pass_and_must_map_to_a_condition(self):
        ev = objects(**{"independent-review": evidence("independent-review", review(findings=[finding()], verdict="APPROVE_WITH_CONDITIONS"))})
        with self.assertRaisesRegex(gate.ValidationError, "VF-001.*(PASS|C6)|C6"): self.check(ev=ev)
        pwc = dossier(disposition="PASS_WITH_CONDITIONS")
        with self.assertRaisesRegex(gate.ValidationError, "VF-001.*condition|C6"): self.check(d=pwc, ev=ev)
        mapped = dossier(disposition="PASS_WITH_CONDITIONS", conditions=[{"condition_id": "C-2", "statement": "bound the retry (VF-001)",
                         "status": "OPEN", "severity": "Major", "blocking_scope": "G09", "owner": "engineering_owner",
                         "closure_predicate": "x", "closure_authority": "quality_authority"}])
        self.check(d=mapped, ev=ev)
        with self.assertRaisesRegex(gate.ValidationError, "refuse PASS|C6"):  # a mapped condition does not license PASS
            self.check(d=dossier(conditions=mapped["conditions"]), ev=ev)
        minor = objects(**{"independent-review": evidence("independent-review", review(findings=[finding(severity="MINOR")]))})
        self.check(ev=minor)  # a MINOR finding does not block
        d2 = dossier(change_class="C2", disposition="PASS_WITH_CONDITIONS", conditions=mapped["conditions"])
        with self.assertRaisesRegex(gate.ValidationError, "VF-001.*record|withdraw|C6"): self.check(d=d2, ev=ev, rec=record())
        self.check(d=d2, ev=ev, rec=record(findings=[finding()], ballots=[dict(b, finding_ids=["VF-001"]) for b in record()["ballots"]]))

    def test_c7_composed_tree_test_cannot_be_not_applicable(self):
        d = dossier(non_coverage=[{"evidence_type": "composed-tree-test", "reason": "r", "declared_by": "x"}])
        with self.assertRaisesRegex(gate.ValidationError, "composed-tree-test.*(NOT_APPLICABLE|non.coverage)|C7"): self.check(d=d)
        ev = objects(**{"composed-tree-test": evidence("composed-tree-test", None, outcome="NOT_APPLICABLE")})
        with self.assertRaisesRegex(gate.ValidationError, "composed-tree-test|C7"): self.check(ev=ev)
        d = dossier(non_coverage=[{"evidence_type": "contract-test", "reason": "r", "declared_by": "x"}])
        self.check(d=d, ev=objects(**{"contract-test": evidence("contract-test", None, outcome="NOT_APPLICABLE")}))  # contract may be declared

    def test_controls_are_silent_when_fields_undeclared(self):
        generic = {t: evidence(t, None, producer="agent") for t in ("independent-review", "integration-test", "contract-test", "composed-tree-test")}
        self.check(w=None, ev=generic, comp=None)  # no typed object, no WP field -> nothing fires
        wp10 = gate.ROOT / "work" / "WP-2026-0010"
        d = json.loads((wp10 / "gate-dossier.G08.json").read_text(encoding="utf-8"))
        ev = {e["type"]: json.loads((gate.ROOT / e["path"]).read_text(encoding="utf-8")) for e in d["evidence"]}
        w = json.loads((wp10 / "work-package.json").read_text(encoding="utf-8")) if (wp10 / "work-package.json").is_file() else None
        gate.check_g08_dossier(d, w, ev, None, None)  # the historical dossier stays valid

    def test_wired_only_for_g08_pass_dossiers_and_pure(self):
        src = inspect.getsource(gate.validate_dossier)
        self.assertIn("check_g08_dossier", src); self.assertIn('"G08"', src)
        pure = inspect.getsource(gate.check_g08_dossier)
        for forbidden in ("open(", "load_json", "subprocess", "write_text", "Path("):
            self.assertNotIn(forbidden, pure, f"check_g08_dossier must be pure; found {forbidden}")


class SchemaAndRegistryTests(unittest.TestCase):
    def test_work_package_schema_declares_verification_obligations_additively(self):
        s = json.loads((gate.ROOT / "schemas/work-package.schema.json").read_text(encoding="utf-8"))
        vo = s["properties"]["verification_obligations"]
        self.assertFalse(vo.get("additionalProperties", True))
        self.assertEqual("boolean", vo["properties"]["runtime_required"]["type"])
        self.assertEqual(["independent-review", "integration-test", "contract-test", "composed-tree-test"],
                         vo["properties"]["comprehensive_coverage_permitted_for"]["items"]["enum"])
        self.assertNotIn("verification_obligations", s.get("required", []))
        for kept in ("expected_surfaces", "tdd_exception", "test_obligations"):  # BLD-C's fields untouched
            self.assertIn(kept, s["properties"])

    def test_registry_pin_is_at_least_validated_and_skill_digest_unchanged(self):
        registry = json.loads((gate.ROOT / "badf/skill-registry.json").read_text(encoding="utf-8"))
        entry = next(e for e in registry["skills"] if e["name"] == "badf-engineering-verification")
        self.assertIn(entry["status"], ("VALIDATED", "SHADOWED", "ACTIVE"))  # VER-C floor; later rungs advance it
        self.assertEqual([], entry["allowed_tools"])
        self.assertEqual(entry["digest"], gate.sha256(gate.ROOT / "skills/badf-engineering-verification/SKILL.md"))


if __name__ == "__main__":
    unittest.main()
