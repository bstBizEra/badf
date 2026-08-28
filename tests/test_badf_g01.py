"""G01 evidence contract (BADF-WP-0030, Issue #51; WP-B of the #41 plan).

G01's three required evidence types have semantics the gate enforces by
opening the artifact, inside validate_evidence: a prd with no scope overlap,
resolvable metric refs and no placeholders; acceptance criteria that exist
and have unique ids; a product approval by a HUMAN product owner who is not
the PRD's author, bound by digest to the exact prd bytes. Every test runs
the real CLI on the shipped G01 example, mutated in a scratch clone.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402
from tests._scratch import seed_clone  # noqa: E402

DOSSIER = "examples/gate-dossier.G01.json"
EV = "examples/evidence/G01"


class G01Scratch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(); self.root = Path(self.tmp) / "badf"
        seed_clone(self.root, carry_working_state=True)
        for rel in ("schemas", "tests"):   # the walker and the rules read the working schemas
            shutil.rmtree(self.root / rel, ignore_errors=True); shutil.copytree(gate.ROOT / rel, self.root / rel)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("BADF_")}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self):
        subprocess.run([sys.executable, "scripts/badf_gate.py", "lock"], cwd=self.root, env=self.env, capture_output=True, check=True)
        return subprocess.run([sys.executable, "scripts/badf_gate.py", "dossier", DOSSIER], cwd=self.root, env=self.env, capture_output=True, text=True)

    def artifact(self, t):
        return json.loads((self.root / EV / f"{t}.artifact.json").read_text())

    def rewrite(self, t, obj, rebind=True):
        """Rewrite an artifact and re-digest its evidence record (an honest edit)."""
        p = self.root / EV / f"{t}.artifact.json"; p.write_text(json.dumps(obj, indent=2) + "\n")
        if rebind:
            rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text())
            rec["digest"] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest(); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def record(self, t, fn):
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text()); fn(rec); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def refused(self, needle):
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a defective G01 dossier rendered APPROVED")
        self.assertIn(needle, r.stderr, r.stderr)


class G01ExampleTests(G01Scratch):

    def test_shipped_example_renders_approved(self):
        r = self.cli(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("APPROVED", r.stdout)

    def test_missing_required_evidence_is_still_refused(self):
        d = json.loads((self.root / DOSSIER).read_text()); d["evidence"] = [e for e in d["evidence"] if e["type"] != "product-approval"]
        (self.root / DOSSIER).write_text(json.dumps(d, indent=2) + "\n")
        self.refused("missing evidence")


class PrdRuleTests(G01Scratch):

    def test_scope_overlap_is_refused(self):
        p = self.artifact("prd"); p["scope"]["out_of_scope"].append(p["scope"]["in_scope"][0]); self.rewrite("prd", p)
        self.refused("both in_scope and out_of_scope")

    def test_unknown_metric_ref_is_refused(self):
        p = self.artifact("prd"); p["objectives"][0]["metric_refs"].append("KPI-999"); self.rewrite("prd", p)
        self.refused("KPI-999")

    def test_unresolved_placeholder_is_refused(self):
        p = self.artifact("prd"); p["problem"]["why_now"] = "__REQUIRED__"; self.rewrite("prd", p)
        self.refused("placeholder")

    def test_placeholder_deep_in_a_list_is_refused(self):
        p = self.artifact("prd"); p["target_users"][0]["needs"].append("TBD"); self.rewrite("prd", p)
        self.refused("placeholder")

    def test_prd_that_fails_its_schema_is_refused(self):
        p = self.artifact("prd"); del p["success_metrics"]; self.rewrite("prd", p)
        self.refused("success_metrics")


class AcceptanceCriteriaRuleTests(G01Scratch):

    def test_no_criteria_is_refused(self):
        a = self.artifact("acceptance-criteria"); a["criteria"] = []; self.rewrite("acceptance-criteria", a)
        self.refused("criteria")

    def test_duplicate_ids_are_refused(self):
        a = self.artifact("acceptance-criteria"); a["criteria"].append(dict(a["criteria"][0])); self.rewrite("acceptance-criteria", a)
        self.refused("duplicate")

    def test_criteria_for_another_prd_are_refused(self):
        a = self.artifact("acceptance-criteria"); a["prd_id"] = "PRD-OTHER"; self.rewrite("acceptance-criteria", a)
        self.refused("PRD-OTHER")

    def test_objective_ref_to_an_unknown_objective_is_refused(self):
        a = self.artifact("acceptance-criteria"); a["criteria"][0]["objective_refs"] = ["OBJ-999"]; self.rewrite("acceptance-criteria", a)
        self.refused("OBJ-999")


class ProductApprovalRuleTests(G01Scratch):

    def test_approval_by_a_non_human_producer_is_refused(self):
        self.record("product-approval", lambda r: r["producer"].update(type="agent"))
        self.refused("human")

    def test_approval_by_the_prd_author_is_refused(self):
        pa = self.artifact("product-approval"); pa["approved_by"]["principal"] = "example-author"; self.rewrite("product-approval", pa)
        self.record("product-approval", lambda r: r["producer"].update(id="example-author"))
        self.refused("author")

    def test_approval_producer_must_be_the_approver(self):
        self.record("product-approval", lambda r: r["producer"].update(id="someone-else"))
        self.refused("approved_by")

    def test_prd_edited_after_approval_is_refused(self):
        """The approval is bound to the PRD bytes. An honest re-digest of the
        edited PRD's own record does not carry the approval with it."""
        p = self.artifact("prd"); p["vision"] = "a different vision, after approval"; self.rewrite("prd", p)
        self.refused("prd_digest")

    def test_approval_for_another_prd_is_refused(self):
        pa = self.artifact("product-approval"); pa["prd_id"] = "PRD-OTHER"; self.rewrite("product-approval", pa)
        self.refused("PRD-OTHER")


if __name__ == "__main__":
    unittest.main()
