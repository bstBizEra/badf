import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "badf_prd.py"
spec = importlib.util.spec_from_file_location("badf_prd", SCRIPT)
badf_prd = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(badf_prd)


def sample():
    return {
        "schema_version": "1.0.0",
        "id": "PRD-BADF-G01-DEMO",
        "gate": "G01",
        "product": {"name": "Demo", "type": "Web Platform", "stage": "MVP", "owner": "product-owner", "target_market": "Enterprise"},
        "overview": "A governed demo product.",
        "problem": {"statement": "Current work is fragmented.", "affected_users": ["operators"], "current_limitations": ["manual handoffs"], "business_impact": ["slow delivery"], "why_now": "Automation is required."},
        "target_users": [{"segment": "Primary", "role": "Operator", "needs": ["traceable delivery"], "pain_points": ["manual coordination"]}],
        "value_proposition": {"statement": "Governed delivery with traceability.", "benefits": ["lower risk"]},
        "vision": "Make governed delivery repeatable.",
        "objectives": [{"id": "OBJ-1", "statement": "Reduce cycle time.", "metric_refs": ["KPI-1"]}],
        "scope": {"in_scope": ["PRD baseline"], "out_of_scope": ["architecture"]},
        "capabilities": [{"name": "PRD Review", "description": "Validate completeness.", "priority": "Must Have"}],
        "differentiation": ["evidence-bound gate preparation"],
        "success_metrics": [{"id": "KPI-1", "name": "Baseline completeness", "baseline": "0%", "target": "100%", "measurement": "validator"}],
        "stakeholders": [{"role": "Product Owner", "accountability": "G01 approval"}],
        "assumptions": [],
        "constraints": ["skill cannot approve G01"],
        "raid": {"risks": [], "assumptions": [], "issues": [], "dependencies": []},
        "legal_regulatory_data": {"legal": [], "regulatory": [], "data_classification": "internal", "privacy": []},
        "acceptance_criteria": [{"id": "AC-1", "statement": "PRD is structurally complete.", "verification": "python3 scripts/badf_prd.py validate"}],
        "challenge": {"method": "decision-tree challenge", "sources_consulted": ["repository"], "findings": [], "unresolved_decisions": []},
        "baseline": {"version": "0.1.0", "source_revision": "abc1234", "created_at": "2026-08-27T18:56:01Z", "author": "author-agent", "status": "APPROVAL_PENDING", "approval": {"required_role": "product_owner", "state": "PENDING", "approver": None, "approved_at": None, "evidence_refs": []}},
        "evidence_refs": [],
    }


class TestBadfPrd(unittest.TestCase):
    def test_complete_candidate_is_eligible_not_approved(self):
        result = badf_prd.validate_document(sample())
        self.assertEqual(result["status"], "ELIGIBLE_FOR_G01_REVIEW")
        self.assertEqual(result["authority"], "NO_GATE_AUTHORITY")

    def test_missing_required_section_fails_closed(self):
        doc = sample(); del doc["scope"]
        with self.assertRaisesRegex(badf_prd.ValidationError, "missing fields: scope"):
            badf_prd.validate_document(doc)

    def test_scope_overlap_fails(self):
        doc = sample(); doc["scope"]["out_of_scope"] = ["PRD baseline"]
        with self.assertRaisesRegex(badf_prd.ValidationError, "same item"):
            badf_prd.validate_document(doc)

    def test_unknown_metric_reference_fails(self):
        doc = sample(); doc["objectives"][0]["metric_refs"] = ["KPI-404"]
        with self.assertRaisesRegex(badf_prd.ValidationError, "unknown metrics"):
            badf_prd.validate_document(doc)

    def test_blocking_challenge_requires_rework(self):
        doc = sample(); doc["challenge"]["findings"] = [{"id":"F-1","severity":"Major","finding":"Scope unclear","disposition":"BLOCKING","evidence":"review"}]
        result = badf_prd.validate_document(doc)
        self.assertEqual(result["status"], "REWORK_REQUIRED")
        self.assertEqual(result["blocking_findings"], ["F-1"])

    def test_unresolved_decision_requires_rework(self):
        doc = sample(); doc["challenge"]["unresolved_decisions"] = ["Which market launches first?"]
        result = badf_prd.validate_document(doc)
        self.assertEqual(result["status"], "REWORK_REQUIRED")

    def test_approved_candidate_needs_evidence(self):
        doc = sample(); doc["baseline"]["status"] = "APPROVED"; doc["baseline"]["approval"].update({"state":"APPROVED","approver":"product-owner","approved_at":"2026-08-27T19:00:00Z"})
        with self.assertRaisesRegex(badf_prd.ValidationError, "approval evidence_refs"):
            badf_prd.validate_document(doc)

    def test_author_cannot_record_own_independent_approval(self):
        doc = sample(); doc["baseline"]["status"] = "APPROVED"; doc["baseline"]["approval"].update({"state":"APPROVED","approver":"author-agent","approved_at":"2026-08-27T19:00:00Z","evidence_refs":["EVD-1"]})
        with self.assertRaisesRegex(badf_prd.ValidationError, "author cannot"):
            badf_prd.validate_document(doc)


    def test_placeholder_value_is_refused(self):
        doc = sample(); doc["product"]["name"] = "__REQUIRED__"
        with self.assertRaisesRegex(badf_prd.ValidationError, "unresolved placeholder"):
            badf_prd.validate_document(doc)

    def test_duplicate_json_key_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prd.json"
            path.write_text('{"schema_version":"1.0.0","schema_version":"2.0.0"}', encoding="utf-8")
            with self.assertRaises(badf_prd.ValidationError):
                badf_prd.load_json(path)

    def test_cli_rework_exit_is_three(self):
        doc = sample(); doc["challenge"]["unresolved_decisions"] = ["decision"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prd.json"; path.write_text(json.dumps(doc), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), "validate", str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 3)
            self.assertIn("REWORK_REQUIRED", proc.stdout)


if __name__ == "__main__":
    unittest.main()
