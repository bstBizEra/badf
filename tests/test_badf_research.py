"""Research record checks (BADF-WP-0036, RSR-002).

The first deterministic controls of the frozen research contract:
`badf_gate.py research <path>` validates a record's schema, the referential
integrity of its source and claim refs, that confidence is DERIVED not
asserted, and that a VERIFIED claim rests on an independent primary source
and an OBSERVED claim on a primary source. Research grants no implementation
authority. Later work packages add challenge, state and traceability
controls. Every test mutates a copy of the shipped example and runs the CLI.
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

EXAMPLE = json.loads((gate.ROOT / "examples/research-record.json").read_text())


class DeriveConfidenceTests(unittest.TestCase):
    """Confidence is a pure function of (independent_primary_sources,
    reproducible, contradictions) -- the table in evidence-contract.md."""

    def d(self, ips, repro, contra):
        return gate.derive_confidence({"independent_primary_sources": ips, "reproducible": repro, "contradictions": contra})

    def test_truth_table(self):
        self.assertEqual(self.d(0, True, 0), "VERY_LOW")
        self.assertEqual(self.d(0, False, 5), "VERY_LOW")
        self.assertEqual(self.d(1, False, 0), "LOW")
        self.assertEqual(self.d(1, True, 0), "MODERATE")
        self.assertEqual(self.d(2, False, 0), "MODERATE")
        self.assertEqual(self.d(3, False, 0), "MODERATE")
        self.assertEqual(self.d(2, True, 1), "HIGH")
        self.assertEqual(self.d(2, True, 0), "VERY_HIGH")
        self.assertEqual(self.d(5, True, 0), "VERY_HIGH")

    def test_every_result_is_a_schema_enum_value(self):
        levels = set(json.loads((gate.ROOT / "schemas/research-record.schema.json").read_text())
                     ["properties"]["claims"]["items"]["properties"]["confidence"]["properties"]["level"]["enum"])
        got = {self.d(i, r, c) for i in range(4) for r in (True, False) for c in range(3)}
        self.assertLessEqual(got, levels)


class ResearchRecordTests(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, "scripts/badf_gate.py", "research", str(path)],
                                  cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective research record passed")
        self.assertIn(needle, r.stderr, r.stderr)

    def test_shipped_example_passes(self):
        r = self.run_cli(copy.deepcopy(EXAMPLE))
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("RESEARCH PASS", r.stdout)

    def test_asserted_confidence_that_is_not_the_derived_level_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["confidence"]["level"] = "LOW"   # basis derives VERY_HIGH
        self.refused(rec, "not the derived level")

    def test_a_dangling_source_reference_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][0]["supporting_sources"].append("S-999")
        self.refused(rec, "S-999")

    def test_a_duplicate_source_id_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["sources"].append(dict(rec["sources"][0]))
        self.refused(rec, "duplicate source")

    def test_verified_without_an_independent_primary_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["claims"][1]["confidence"]["basis"]["independent_primary_sources"] = 0
        rec["claims"][1]["confidence"]["level"] = "VERY_LOW"   # keep confidence consistent so THIS control fires
        self.refused(rec, "no independent primary source")

    def test_verified_whose_only_support_is_secondary_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["sources"][1]["source_type"] = "SECONDARY"   # S-002, the only support of C-002 (VERIFIED)
        self.refused(rec, "no independent primary source")

    def test_observed_without_a_primary_source_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        # C-001 is OBSERVED; make both its supports non-primary while keeping it INFERRED-free
        for s in rec["sources"]:
            if s["id"] in ("S-001", "S-003"):
                s["source_type"] = "COMMUNITY"
        # C-002 (VERIFIED) also supported by S-002 primary still; C-001 now fails OBSERVED-needs-primary
        rec["claims"][0]["status"] = "PARTIALLY_VERIFIED"   # avoid the VERIFIED path so OBSERVED path is what refuses
        self.refused(rec, "cites no primary source")

    def test_implementation_authority_true_is_refused_by_the_schema(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["authority"]["implementation_authority"] = True   # schema fixes this to enum [false]
        self.refused(rec, "implementation_authority")

    def test_a_finding_referencing_an_unknown_claim_is_refused(self):
        rec = copy.deepcopy(EXAMPLE)
        rec["findings"][0]["claim_refs"].append("C-999")
        self.refused(rec, "C-999")


if __name__ == "__main__":
    unittest.main()
