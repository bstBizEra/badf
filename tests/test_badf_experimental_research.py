"""experimental-research (P1, R08) and control 28.

R08 (EMPIRICAL_EXPERIMENT) was the one research type with no dedicated subskill and
no integrity control: it routed to the raw experiment mechanism and the gate never
checked an empirical run actually ran an experiment. Control 28 mirrors 23/24 --
type-specific structure grounded in the record: an R08 record carries at least one
experiment, and every experiment's hypothesis_ref resolves to a hypothesis the record
holds. An empirical run that measured nothing, or tested a hypothesis it never stated,
is not an experiment. The hypothesis_ref resolution applies to any record carrying
experiments. Every test mutates a copy of the shipped example and runs the CLI; the
evidence_digest is recomputed so the probe tests control 28, not control 17.
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import badf_gate as gate  # noqa: E402

# R07/D4 with a full challenge council and one hypothesis H-001.
BASE = json.loads((gate.ROOT / "examples/research-record-challenged.json").read_text())


class ExperimentalBase(unittest.TestCase):
    def run_cli(self, rec):
        rec = copy.deepcopy(rec)
        rec["evidence_digest"] = gate.compute_research_evidence_digest(rec)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f)
            path = Path(f.name)
        try:
            return subprocess.run(
                [sys.executable, "scripts/badf_gate.py", "research", str(path)],
                cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def r08(self):
        rec = copy.deepcopy(BASE)
        rec["type"] = "R08"
        rec["depth"] = "D5"  # challenge already present; D5 requires it
        return rec

    def experiment(self, hyp="H-001", eid="E-001"):
        return {"id": eid, "hypothesis_ref": hyp, "method": "controlled run under the composed-tree gate", "result": "measured X within tolerance"}

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective record was admitted: " + r.stdout)
        self.assertIn(needle, r.stderr, r.stderr)

    def admitted(self, rec):
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)


class Control28Tests(ExperimentalBase):
    def test_an_empirical_run_that_measured_nothing_is_refused(self):
        rec = self.r08()
        rec["experiments"] = []
        self.refused(rec, "control 28")

    def test_an_experiment_on_a_hypothesis_the_record_does_not_hold_is_refused(self):
        rec = self.r08()
        rec["experiments"] = [self.experiment(hyp="H-999")]
        self.refused(rec, "control 28")

    def test_an_r08_run_with_an_experiment_bound_to_a_held_hypothesis_is_admitted(self):
        rec = self.r08()
        rec["experiments"] = [self.experiment(hyp="H-001")]
        self.admitted(rec)

    def test_hypothesis_ref_resolution_applies_to_any_record_carrying_experiments(self):
        # a NON-R08 record with a dangling experiment ref is still refused (referential integrity).
        rec = copy.deepcopy(BASE)  # stays R07/D4
        rec["experiments"] = [self.experiment(hyp="H-404")]
        self.refused(rec, "control 28")

    def test_a_non_r08_record_without_experiments_is_unaffected(self):
        # control 28's "requires an experiment" clause is R08-specific (mirror of 23/24).
        rec = copy.deepcopy(BASE)  # R07, experiments already []
        self.admitted(rec)


class ShippedExampleTests(ExperimentalBase):
    def test_the_experimental_example_is_admitted_and_runs_an_experiment(self):
        rec = json.loads((gate.ROOT / "examples/research-record-experimental.json").read_text())
        self.assertEqual(rec["type"], "R08")
        self.assertTrue(rec["experiments"], "the experimental example runs no experiment")
        held = {h["id"] for h in rec["hypotheses"]}
        for e in rec["experiments"]:
            self.assertIn(e["hypothesis_ref"], held, f"{e['id']} tests an unheld hypothesis")
        r = subprocess.run([sys.executable, "scripts/badf_gate.py", "research",
                            "examples/research-record-experimental.json"],
                           cwd=str(gate.ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


class SubskillAdmissionTests(unittest.TestCase):
    def test_experimental_research_is_registered_implemented(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "experimental-research")
        self.assertEqual(entry["status"], "IMPLEMENTED")
        import hashlib
        want = "sha256:" + hashlib.sha256((gate.ROOT / entry["source"]).read_bytes()).hexdigest()
        self.assertEqual(entry["digest"], want)

    def test_the_family_stays_active_and_grants_no_authority(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        fam = next(e for e in reg["skills"] if e["name"] == "badf-research")
        self.assertEqual(fam["status"], "ACTIVE")
        schema = json.loads((gate.ROOT / "schemas/research-record.schema.json").read_text())
        self.assertEqual(schema["properties"]["authority"]["properties"]["implementation_authority"]["enum"], [False])

    def test_the_subskill_exists_and_claims_no_authority(self):
        skill = (gate.ROOT / "skills/badf-research/subskills/experimental-research/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("experimental-research", skill)
        self.assertRegex(skill, r"RSR-I01|no authority|grants? (no|nothing)")


if __name__ == "__main__":
    unittest.main()
