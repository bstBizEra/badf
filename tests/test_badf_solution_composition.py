"""solution-composition matrix -- structural controls (BADF-WP-0071 / WP-SOL-B).

`badf_gate.py solution <path>` validates a badf-solution-design composition matrix's
STRUCTURAL integrity inside the one canonical gate (not a second validator -- SOL-I12):
unique solution ids (SOL-C01) and every row binding at least one specialist artifact
(SOL-C03). Requirement provenance (SOL-C02 / SOL-I01) is enforced by the schema
(required + ^REQ- pattern). The cross-artifact SEAM controls are WP-SOL-C. Every test
mutates a copy of the shipped example and runs the CLI.
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

EXAMPLE = json.loads((gate.ROOT / "examples/solution-composition.json").read_text())
REF_KINDS = ("ux_refs", "api_refs", "authorization_refs", "data_refs", "audit_refs", "accessibility_refs", "test_refs")


class SolutionCompositionBase(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f)
            p = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "solution", str(p)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            p.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective matrix was admitted: " + r.stdout)
        self.assertIn(needle, r.stderr, r.stderr)

    def admitted(self, rec):
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)


class StructuralControlTests(SolutionCompositionBase):
    def test_the_shipped_example_passes(self):
        self.admitted(EXAMPLE)

    def test_a_duplicate_solution_id_is_refused(self):  # SOL-C01
        rec = copy.deepcopy(EXAMPLE)
        rec["solutions"][1]["solution_id"] = rec["solutions"][0]["solution_id"]
        self.refused(rec, "duplicate")

    def test_a_composition_that_binds_no_artifact_is_refused(self):  # SOL-C03
        rec = copy.deepcopy(EXAMPLE)
        for k in REF_KINDS:
            rec["solutions"][0].pop(k, None)
        self.refused(rec, "binds no specialist artifact")

    def test_all_empty_ref_arrays_still_bind_nothing(self):  # SOL-C03 (present-but-empty)
        rec = copy.deepcopy(EXAMPLE)
        for k in REF_KINDS:
            rec["solutions"][0][k] = []
        self.refused(rec, "binds no specialist artifact")


class SchemaEnforcedProvenanceTests(SolutionCompositionBase):
    """SOL-C02 / SOL-I01 structural provenance is the schema's job, not a code branch."""

    def test_a_missing_requirement_ref_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        del rec["solutions"][0]["requirement_ref"]
        self.refused(rec, "requirement_ref")

    def test_a_malformed_requirement_ref_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["solutions"][0]["requirement_ref"] = "REQ-x"
        self.refused(rec, "requirement_ref")

    def test_an_empty_matrix_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["solutions"] = []
        self.refused(rec, "solutions")


class RegistryStatusTests(unittest.TestCase):
    def test_badf_solution_design_is_registered_implemented(self):
        reg = json.loads((gate.ROOT / "badf/skill-registry.json").read_text())
        entry = next(e for e in reg["skills"] if e["name"] == "badf-solution-design")
        self.assertEqual(entry["status"], "IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
