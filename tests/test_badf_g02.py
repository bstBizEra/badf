"""G02 evidence contract (BADF-WP-0041, Issue #70; planned fresh from #46).

G02's four required evidence types have semantics the gate enforces by opening
the artifact, inside validate_evidence: requirements that are unique and each
trace to a real objective; NFRs each carrying a quantified (numeric) target;
an RTM that is bidirectional and complete -- no orphan requirement, no
uncovered acceptance criterion, no dangling id; and a human definition-of-ready
covering every G02 exit criterion. Every test runs the real CLI on the shipped
G02 example, mutated in a scratch clone -- the faithful-runner shape.
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

DOSSIER = "examples/gate-dossier.G02.json"
EV = "examples/evidence/G02"


class G02Scratch(unittest.TestCase):
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

    def rewrite(self, t, obj):
        """Rewrite an artifact and re-digest its evidence record (an honest edit)."""
        p = self.root / EV / f"{t}.artifact.json"; p.write_text(json.dumps(obj, indent=2) + "\n")
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text())
        rec["digest"] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest(); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def record(self, t, fn):
        rec_p = self.root / EV / f"{t}.json"; rec = json.loads(rec_p.read_text()); fn(rec); rec_p.write_text(json.dumps(rec, indent=2) + "\n")

    def refused(self, needle):
        r = self.cli()
        self.assertNotEqual(r.returncode, 0, "a defective G02 dossier rendered APPROVED")
        self.assertIn(needle, r.stderr, r.stderr)


class G02ExampleTests(G02Scratch):

    def test_shipped_example_renders_approved(self):
        r = self.cli(); self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("APPROVED", r.stdout)

    def test_missing_required_evidence_is_still_refused(self):
        d = json.loads((self.root / DOSSIER).read_text()); d["evidence"] = [e for e in d["evidence"] if e["type"] != "traceability"]
        (self.root / DOSSIER).write_text(json.dumps(d, indent=2) + "\n")
        self.refused("missing evidence")


class TraceabilityRuleTests(G02Scratch):

    def test_orphan_requirement_is_refused(self):
        rtm = self.artifact("traceability")
        rtm["requirement_to_objective"] = [r for r in rtm["requirement_to_objective"] if r["requirement"] != "REQ-003"]
        self.rewrite("traceability", rtm)
        self.refused("orphan requirement REQ-003")

    def test_uncovered_acceptance_criterion_is_refused(self):
        rtm = self.artifact("traceability")
        rtm["criterion_to_requirement"] = [c for c in rtm["criterion_to_requirement"] if c["criterion"] != "AC-002"]
        self.rewrite("traceability", rtm)
        self.refused("uncovered acceptance criterion AC-002")

    def test_a_requirement_mapped_to_an_undeclared_objective_is_refused(self):
        rtm = self.artifact("traceability")
        rtm["requirement_to_objective"][0]["objectives"] = ["OBJ-404"]
        self.rewrite("traceability", rtm)
        self.refused("undeclared objective")

    def test_a_map_entry_for_an_unknown_requirement_is_refused(self):
        rtm = self.artifact("traceability")
        rtm["requirement_to_objective"].append({"requirement": "REQ-404", "objectives": ["OBJ-001"]})
        self.rewrite("traceability", rtm)
        self.refused("absent from the requirements artifact")

    def test_a_criterion_mapped_to_an_unknown_requirement_is_refused(self):
        rtm = self.artifact("traceability")
        rtm["criterion_to_requirement"][0]["requirements"] = ["REQ-404"]
        self.rewrite("traceability", rtm)
        self.refused("maps to unknown requirement")


class RequirementsRuleTests(G02Scratch):

    def test_requirement_referencing_an_unknown_objective_is_refused(self):
        reqs = self.artifact("requirements")
        reqs["requirements"][0]["objective_refs"] = ["OBJ-999"]
        self.rewrite("requirements", reqs)
        self.refused("absent from the RTM's objective universe")

    def test_a_requirement_that_traces_to_no_objective_is_refused(self):
        reqs = self.artifact("requirements")
        reqs["requirements"][0]["objective_refs"] = []
        self.rewrite("requirements", reqs)
        self.refused("decomposes no objective")

    def test_duplicate_requirement_id_is_refused(self):
        reqs = self.artifact("requirements")
        reqs["requirements"][1]["id"] = reqs["requirements"][0]["id"]
        self.rewrite("requirements", reqs)
        self.refused("duplicate requirement id")


class NfrRuleTests(G02Scratch):

    def test_unquantified_nfr_is_refused(self):
        nfr = self.artifact("nfr")
        nfr["nfrs"][0]["target"]["value"] = "fast"
        self.rewrite("nfr", nfr)
        self.refused("is not quantified")

    def test_a_boolean_nfr_target_is_not_a_quantity(self):
        nfr = self.artifact("nfr")
        nfr["nfrs"][0]["target"]["value"] = True
        self.rewrite("nfr", nfr)
        self.refused("is not quantified")


class DefinitionOfReadyRuleTests(G02Scratch):

    def test_missing_a_criterion_is_refused(self):
        dor = self.artifact("definition-of-ready")
        dor["checklist"] = [c for c in dor["checklist"] if c["criterion"] != "NFRs quantified"]
        self.rewrite("definition-of-ready", dor)
        self.refused("missing G02 exit-criterion")

    def test_an_unmet_criterion_is_refused(self):
        dor = self.artifact("definition-of-ready")
        dor["checklist"][0]["met"] = False
        self.rewrite("definition-of-ready", dor)
        self.refused("not met")

    def test_a_non_human_definition_of_ready_is_refused(self):
        self.record("definition-of-ready", lambda rec: rec.__setitem__("producer", {"id": "bot", "type": "automation"}))
        self.refused("must be produced by a human")


if __name__ == "__main__":
    unittest.main()
