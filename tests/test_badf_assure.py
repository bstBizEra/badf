"""Architecture ASSURE substrate (BADF-WP-0057, WP-ARCH-C).

The `assure` gate command validates an architecture-assurance record against the
frozen contract's controls 13-18: it binds one baseline and one observed revision
(13, ARCH-I09), never infers compliance without a baseline (14, ARCH-I07), never
serialises an INDETERMINATE ADR result as a pass (15), never self-authorises drift
as approved evolution (16, ARCH-I08), declares its non-coverage (17), and assesses
every finding against the single bound baseline (18, ARCH-I01). Read-only; grants
no authority. Every test runs the real CLI on the shipped example, mutated.
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

EXAMPLE = json.loads((gate.ROOT / "examples/architecture-assurance.json").read_text())


class AssureTests(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "assure", str(path)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective assurance record passed")
        self.assertIn(needle, r.stderr, r.stderr)

    def test_shipped_example_passes(self):
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("ASSURE PASS", r.stdout)

    def test_no_bound_baseline_or_observed_revision_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["baseline"]["revision"] = ""
        self.refused(rec, "no bound baseline or observed revision")

    def test_compliant_with_no_baseline_digest_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["baseline"]["digest"] = None
        self.refused(rec, "COMPLIANT with no baseline digest")

    def test_indeterminate_adr_result_blocks_compliant(self):
        rec = copy.deepcopy(EXAMPLE); rec["adr_compliance"][0]["result"] = "INDETERMINATE"
        self.refused(rec, "INDETERMINATE never converts to PASS")

    def test_drift_cannot_self_classify_as_approved_evolution(self):
        rec = copy.deepcopy(EXAMPLE); rec["drift"][0]["classification"] = "APPROVED_EVOLUTION_NOT_BASELINED"
        self.refused(rec, "classifies itself as approved evolution")

    def test_no_non_coverage_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["non_coverage"] = []
        self.refused(rec, "declares no non-coverage")

    def test_a_finding_against_a_different_baseline_is_refused(self):
        rec = copy.deepcopy(EXAMPLE); rec["findings"][0]["baseline_ref"] = "deadbeef"
        self.refused(rec, "is not the record's single bound baseline")

    def test_indeterminate_conclusion_may_carry_an_indeterminate_adr(self):
        # control 15 only blocks COMPLIANT; an INDETERMINATE conclusion may report one.
        rec = copy.deepcopy(EXAMPLE)
        rec["adr_compliance"][0]["result"] = "INDETERMINATE"; rec["conclusion"] = "INDETERMINATE"
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("ASSURE PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
