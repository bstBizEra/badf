"""RSR-I06 — citation != support, and control 27 (semantic-support coverage honesty).

GOV-0031 (#84): a claim could be VERIFIED citing a resolving, PRIMARY, digest-bound
source whose content does not entail it, because the record had no way to say whether
semantic support was ever assessed. RSR-I06 freezes the boundary: the gate verifies
source identity, provenance, freshness, binding and adjudication -- it does NOT prove
natural-language entailment. Control 27 gives the boundary teeth without crossing it:
a VERIFIED claim on cited support must EITHER carry a fact-checking support-assessment
receipt (with a locator) for each supporting source, OR explicitly declare
semantic-support NON_COVERAGE. Silence is refused, and a receipt whose own assessment
does not substantiate the claim cannot back a VERIFIED binding. The gate checks that the
assessment happened under contract; it never asserts the sentence is true.

Every test mutates a copy of the shipped example and runs `badf_gate.py research`.
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


class RSRI06Base(unittest.TestCase):
    def run_cli(self, rec):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(rec, f)
            path = Path(f.name)
        try:
            return subprocess.run(
                [sys.executable, "scripts/badf_gate.py", "research", str(path)],
                cwd=str(gate.ROOT), capture_output=True, text=True)
        finally:
            path.unlink()

    def base(self):
        return copy.deepcopy(EXAMPLE)

    def verified_claim(self, rec):
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                return c
        raise AssertionError("fixture has no VERIFIED claim on cited support")

    def receipt(self, claim_ref, source_ref, relation="SUPPORTS",
                assessment="SUBSTANTIATED", value="120-138"):
        return {
            "claim_ref": claim_ref, "source_ref": source_ref,
            "relation": relation, "assessment": assessment,
            "assessor": "agent://badf/research/fact-checking",
            "method": "FACT_CHECKING",
            "locator": {"type": "LINE_RANGE", "value": value},
        }

    def refused(self, rec, needle):
        r = self.run_cli(rec)
        self.assertNotEqual(r.returncode, 0, "a defective record was admitted: " + r.stdout)
        self.assertIn(needle, r.stderr, r.stderr)

    def admitted(self, rec):
        r = self.run_cli(rec)
        self.assertEqual(r.returncode, 0, r.stderr)


class HonestyGapTests(RSRI06Base):
    """The #84 defect: a VERIFIED claim silently represents cited support."""

    def test_verified_without_semantic_support_is_refused(self):
        # The failing-first probe: strip any declaration -> the gate must refuse.
        rec = self.base()
        for c in rec["claims"]:
            c.pop("semantic_support", None)
        self.refused(rec, "control 27")

    def test_non_coverage_is_the_honest_fallback(self):
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        self.admitted(rec)


class AssessedReceiptTests(RSRI06Base):
    def test_assessed_without_a_receipt_is_refused(self):
        rec = self.base()
        c = self.verified_claim(rec)
        c["semantic_support"] = "ASSESSED"
        rec.pop("support_assessments", None)
        self.refused(rec, "control 27")

    def test_assessed_with_a_receipt_per_source_is_admitted(self):
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        c = self.verified_claim(rec)
        c["semantic_support"] = "ASSESSED"
        rec["support_assessments"] = [self.receipt(c["id"], s) for s in c["supporting_sources"]]
        self.admitted(rec)

    def test_a_receipt_with_an_empty_locator_is_refused(self):
        # the gate's schema walker ignores minLength, so non-empty locator is control-27 code.
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        c = self.verified_claim(rec)
        c["semantic_support"] = "ASSESSED"
        rec["support_assessments"] = [self.receipt(c["id"], s, value="   ") for s in c["supporting_sources"]]
        self.refused(rec, "control 27")


class NotSubstantiatedTeethTests(RSRI06Base):
    """A receipt the record's own assessment does not substantiate cannot back VERIFIED."""

    def test_a_not_substantiated_receipt_cannot_back_a_verified_binding(self):
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        c = self.verified_claim(rec)
        c["semantic_support"] = "ASSESSED"
        s = c["supporting_sources"][0]
        rec["support_assessments"] = [self.receipt(c["id"], s, assessment="NOT_SUBSTANTIATED")]
        for extra in c["supporting_sources"][1:]:
            rec["support_assessments"].append(self.receipt(c["id"], extra))
        self.refused(rec, "control 27")

    def test_a_non_supporting_relation_cannot_back_a_verified_binding(self):
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        c = self.verified_claim(rec)
        c["semantic_support"] = "ASSESSED"
        s = c["supporting_sources"][0]
        rec["support_assessments"] = [self.receipt(c["id"], s, relation="DOES_NOT_SUPPORT")]
        for extra in c["supporting_sources"][1:]:
            rec["support_assessments"].append(self.receipt(c["id"], extra))
        self.refused(rec, "control 27")


class ReceiptWellFormednessTests(RSRI06Base):
    def test_a_receipt_naming_an_absent_claim_is_refused(self):
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        s = self.verified_claim(rec)["supporting_sources"][0]
        rec["support_assessments"] = [self.receipt("C-999", s)]
        self.refused(rec, "control 27")

    def test_a_receipt_naming_an_absent_source_is_refused(self):
        rec = self.base()
        for c in rec["claims"]:
            if c["status"] == "VERIFIED" and c["supporting_sources"]:
                c["semantic_support"] = "NON_COVERAGE"
        cid = self.verified_claim(rec)["id"]
        rec["support_assessments"] = [self.receipt(cid, "S-999")]
        self.refused(rec, "control 27")


class ShippedShadowRecordTests(RSRI06Base):
    """The committed positive shadow record exercises the ASSESSED receipt path."""

    def test_the_support_assessment_shadow_record_is_admitted(self):
        rec = json.loads((gate.ROOT / "examples/research-record-shadow-support-assessment.json").read_text())
        self.admitted(rec)

    def test_the_shadow_record_carries_a_located_receipt_for_each_assessed_binding(self):
        rec = json.loads((gate.ROOT / "examples/research-record-shadow-support-assessment.json").read_text())
        assessed = [c for c in rec["claims"] if c.get("semantic_support") == "ASSESSED"]
        self.assertTrue(assessed, "the shadow record demonstrates no ASSESSED binding")
        receipts = rec["support_assessments"]
        for c in assessed:
            for s in c["supporting_sources"]:
                hit = [a for a in receipts if a["claim_ref"] == c["id"] and a["source_ref"] == s]
                self.assertTrue(hit, f"no receipt for {c['id']}<-{s}")
                self.assertTrue(hit[0]["locator"]["value"].strip(), "receipt carries an empty locator")


class NoAuthorityDriftTests(RSRI06Base):
    """RSR-I06 grants no implementation authority -- RSR-I01 is unchanged."""

    def test_research_record_schema_still_fixes_implementation_authority_false(self):
        schema = json.loads((gate.ROOT / "schemas/research-record.schema.json").read_text())
        self.assertEqual(schema["properties"]["authority"]["properties"]["implementation_authority"]["enum"], [False])

    def test_the_shipped_example_still_declares_no_implementation_authority(self):
        self.assertEqual(EXAMPLE["authority"]["implementation_authority"], False)


if __name__ == "__main__":
    unittest.main()
