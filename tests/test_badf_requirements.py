import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("badf_requirements", ROOT / "scripts/badf_requirements.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MOD)


def valid_rtm():
    return {
        "schema_version": "1.0.0",
        "rtm_id": "RTM-TEST-001",
        "work_package_id": "WP-2026-0901",
        "gate": "G02",
        "prd_baseline": {
            "id": "PRD-TEST-001",
            "version": "1.0.0",
            "artifact": "docs/prd/test.json",
            "digest": "sha256:" + "1" * 64,
            "gate": "G01",
            "disposition": "APPROVED",
            "approval_evidence_refs": ["EVD-PRD-APPROVAL"],
            "objectives": [{"id": "OBJ-001", "statement": "Reduce checkout abandonment by 10 percent"}],
        },
        "nodes": {
            "capabilities": [{"id": "CAP-001", "statement": "Complete checkout", "rationale": "Supports OBJ-001"}],
            "epics": [{"id": "EPIC-001", "statement": "Checkout flow", "value": "Reduce abandonment", "priority": "P0"}],
            "requirements": [
                {"id": "REQ-001", "type": "FUNCTIONAL", "statement": "The buyer can confirm an order",
                 "rationale": "Core checkout outcome", "priority": "P0", "security_sensitive": False},
                {"id": "REQ-002", "type": "SECURITY", "statement": "The service protects checkout authorization",
                 "rationale": "Threat SRC-001 requires a control", "priority": "P0", "security_sensitive": True},
            ],
            "nfrs": [
                {"id": "NFR-001", "category": "PERFORMANCE", "statement": "Confirmation is responsive",
                 "metric": "p95 confirmation latency", "operator": "<=", "target": 500, "unit": "ms",
                 "measurement_method": "production-representative load test"},
                {"id": "NFR-002", "category": "SECURITY", "statement": "Unauthorized confirmations are rejected",
                 "metric": "unauthorized confirmation success rate", "operator": "==", "target": 0, "unit": "percent",
                 "measurement_method": "negative authorization test"},
            ],
            "acceptance_criteria": [
                {"id": "AC-001", "statement": "Valid order is confirmed", "pass_condition": "confirmation id is returned"},
                {"id": "AC-002", "statement": "Latency meets threshold", "pass_condition": "p95 <= 500 ms"},
                {"id": "AC-003", "statement": "Unauthorized order is rejected", "pass_condition": "zero unauthorized confirmations"},
            ],
            "test_obligations": [
                {"id": "TEST-001", "level": "E2E", "statement": "Confirm valid order", "expected_evidence_type": "TEST"},
                {"id": "TEST-002", "level": "PERFORMANCE", "statement": "Measure confirmation latency", "expected_evidence_type": "TEST"},
                {"id": "TEST-003", "level": "SECURITY", "statement": "Attempt unauthorized confirmation", "expected_evidence_type": "SECURITY"},
            ],
            "evidence_requirements": [
                {"id": "EVDREQ-001", "evidence_type": "TEST", "claim": "Valid order confirmation passes"},
                {"id": "EVDREQ-002", "evidence_type": "TEST", "claim": "p95 confirmation latency <= 500 ms"},
                {"id": "EVDREQ-003", "evidence_type": "SECURITY", "claim": "Unauthorized confirmations are rejected"},
            ],
            "security_sources": [
                {"id": "SRC-001", "kind": "THREAT", "reference": "TM-001/T-004",
                 "statement": "Unauthorized actor attempts order confirmation", "requires_requirement": True}
            ],
        },
        "links": [
            {"from": "OBJ-001", "to": "CAP-001", "type": "OBJECTIVE_TO_CAPABILITY"},
            {"from": "CAP-001", "to": "EPIC-001", "type": "CAPABILITY_TO_EPIC"},
            {"from": "EPIC-001", "to": "REQ-001", "type": "EPIC_TO_REQUIREMENT"},
            {"from": "EPIC-001", "to": "REQ-002", "type": "EPIC_TO_REQUIREMENT"},
            {"from": "REQ-001", "to": "NFR-001", "type": "REQUIREMENT_TO_NFR"},
            {"from": "REQ-002", "to": "NFR-002", "type": "REQUIREMENT_TO_NFR"},
            {"from": "REQ-001", "to": "AC-001", "type": "REQUIREMENT_TO_ACCEPTANCE"},
            {"from": "NFR-001", "to": "AC-002", "type": "NFR_TO_ACCEPTANCE"},
            {"from": "REQ-002", "to": "AC-003", "type": "REQUIREMENT_TO_ACCEPTANCE"},
            {"from": "NFR-002", "to": "AC-003", "type": "NFR_TO_ACCEPTANCE"},
            {"from": "AC-001", "to": "TEST-001", "type": "ACCEPTANCE_TO_TEST"},
            {"from": "AC-002", "to": "TEST-002", "type": "ACCEPTANCE_TO_TEST"},
            {"from": "AC-003", "to": "TEST-003", "type": "ACCEPTANCE_TO_TEST"},
            {"from": "TEST-001", "to": "EVDREQ-001", "type": "TEST_TO_EVIDENCE"},
            {"from": "TEST-002", "to": "EVDREQ-002", "type": "TEST_TO_EVIDENCE"},
            {"from": "TEST-003", "to": "EVDREQ-003", "type": "TEST_TO_EVIDENCE"},
            {"from": "SRC-001", "to": "REQ-002", "type": "SOURCE_TO_REQUIREMENT"},
        ],
        "dependencies": [],
        "decisions": [],
        "review_findings": [],
        "author": {"id": "requirements-agent", "principal_type": "agent"},
    }


class RequirementsRTMTests(unittest.TestCase):
    def test_valid_rtm_is_only_eligible_for_review(self):
        report = MOD.validate(valid_rtm())
        self.assertEqual(report["disposition"], "ELIGIBLE_FOR_G02_REVIEW")
        self.assertEqual(report["authority"], "NO_GATE_AUTHORITY")

    def test_orphan_objective_fails_closed(self):
        doc = valid_rtm()
        doc["prd_baseline"]["objectives"].append({"id": "OBJ-002", "statement": "Increase retention"})
        with self.assertRaisesRegex(MOD.ValidationError, "orphan PRD objective OBJ-002"):
            MOD.validate(doc)

    def test_requirement_without_nfr_fails_closed(self):
        doc = valid_rtm()
        doc["links"] = [l for l in doc["links"] if not (l["from"] == "REQ-001" and l["type"] == "REQUIREMENT_TO_NFR")]
        with self.assertRaisesRegex(MOD.ValidationError, "REQ-001 has no quantified NFR"):
            MOD.validate(doc)

    def test_unquantified_nfr_fails_closed(self):
        doc = valid_rtm()
        doc["nodes"]["nfrs"][0]["target"] = "fast"
        with self.assertRaisesRegex(MOD.ValidationError, "target must be numeric"):
            MOD.validate(doc)

    def test_security_requirement_needs_source_provenance(self):
        doc = valid_rtm()
        doc["links"] = [l for l in doc["links"] if l["type"] != "SOURCE_TO_REQUIREMENT"]
        with self.assertRaisesRegex(MOD.ValidationError, "REQ-002.*no source provenance"):
            MOD.validate(doc)

    def test_required_source_must_drive_requirement(self):
        doc = valid_rtm()
        doc["nodes"]["requirements"][1]["type"] = "FUNCTIONAL"
        doc["nodes"]["requirements"][1]["security_sensitive"] = False
        doc["links"] = [l for l in doc["links"] if l["type"] != "SOURCE_TO_REQUIREMENT"]
        with self.assertRaisesRegex(MOD.ValidationError, "SRC-001.*drives none"):
            MOD.validate(doc)

    def test_dependency_cycle_fails_closed(self):
        doc = valid_rtm()
        doc["dependencies"] = [
            {"from_requirement": "REQ-001", "to_requirement": "REQ-002", "kind": "REQUIRES", "status": "MAPPED"},
            {"from_requirement": "REQ-002", "to_requirement": "REQ-001", "kind": "REQUIRES", "status": "MAPPED"},
        ]
        with self.assertRaisesRegex(MOD.ValidationError, "dependency cycle"):
            MOD.validate(doc)

    def test_open_decision_is_rework_not_approval(self):
        doc = valid_rtm()
        doc["decisions"] = [{"id": "DEC-001", "status": "OPEN", "statement": "Choose retention window", "owner": "product-owner", "resolution": None}]
        report = MOD.validate(doc)
        self.assertEqual(report["disposition"], "REWORK_REQUIRED")
        self.assertIn("decision:DEC-001", report["blockers"])

    def test_open_blocking_finding_is_rework(self):
        doc = valid_rtm()
        doc["review_findings"] = [{"id": "F-001", "lens": "CLARITY", "severity": "BLOCKING", "status": "OPEN",
                                   "statement": "REQ-001 actor is ambiguous", "node_refs": ["REQ-001"]}]
        report = MOD.validate(doc)
        self.assertEqual(report["disposition"], "REWORK_REQUIRED")
        self.assertIn("finding:F-001", report["blockers"])

    def test_blocked_dependency_is_rework(self):
        doc = valid_rtm()
        doc["dependencies"] = [{"from_requirement": "REQ-001", "to_requirement": "REQ-002",
                                "kind": "EXTERNAL_BLOCKER", "status": "BLOCKED"}]
        report = MOD.validate(doc)
        self.assertEqual(report["disposition"], "REWORK_REQUIRED")

    def test_placeholder_fails_closed(self):
        doc = valid_rtm()
        doc["nodes"]["requirements"][0]["statement"] = "__REQUIRED__"
        with self.assertRaisesRegex(MOD.ValidationError, "placeholder"):
            MOD.validate(doc)

    def test_unapproved_prd_baseline_fails_closed(self):
        doc = valid_rtm()
        doc["prd_baseline"]["disposition"] = "DRAFT"
        with self.assertRaisesRegex(MOD.ValidationError, "approved G01 baseline"):
            MOD.validate(doc)

    def test_missing_evidence_chain_fails_closed(self):
        doc = valid_rtm()
        doc["links"] = [l for l in doc["links"] if not (l["from"] == "TEST-001" and l["type"] == "TEST_TO_EVIDENCE")]
        with self.assertRaisesRegex(MOD.ValidationError, "TEST-001 lacks acceptance upstream or evidence downstream"):
            MOD.validate(doc)

    def test_duplicate_json_key_is_refused(self):
        text = '{"schema_version":"1.0.0","schema_version":"1.0.0"}'
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.json"
            p.write_text(text)
            with self.assertRaisesRegex(MOD.ValidationError, "duplicate key"):
                MOD.load_json(p)

    def test_template_is_intentionally_not_passable(self):
        doc = json.loads((ROOT / "templates/requirements-rtm.json").read_text())
        with self.assertRaisesRegex(MOD.ValidationError, "placeholder"):
            MOD.validate(doc)

    def test_cli_never_claims_gate_authority(self):
        doc = valid_rtm()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rtm.json"
            p.write_text(json.dumps(doc))
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/badf_requirements.py"), str(p)],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("ELIGIBLE_FOR_G02_REVIEW", proc.stdout)
        self.assertIn("authority=NO_GATE_AUTHORITY", proc.stdout)
        self.assertNotIn("G02 PASS", proc.stdout)
        self.assertNotIn("DESIGN_READY", proc.stdout)


if __name__ == "__main__":
    unittest.main()
